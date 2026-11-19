"""Mutation tools. They NEVER execute anything.

Each one validates the request against live data, builds a human-readable summary and
returns a PendingAction. Only the user pressing Confirm in the UI (POST /chat/confirm)
runs it, and that calls the same business endpoint the UI uses, with the user's own token.
"""
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.api import ApiError
from app.tools.base import PendingAction, Tool, ToolContext, ToolError, ToolOutcome, parse_uuid
from app.tools.read_tools import _describe_purchase_order

STRICT = ConfigDict(extra="forbid")

AWAITING = (
    "NOT EXECUTED. A confirmation card has been shown to the user. Tell them what is about to "
    "happen and that nothing changes until they press Confirm. Do not say it is done."
)


def _prepare(ctx: ToolContext, action: PendingAction) -> ToolOutcome:
    if ctx.pending is not None:
        raise ToolError(
            "Another action is already waiting for the user's confirmation. "
            "Ask them to confirm or cancel it before preparing a second one."
        )
    ctx.pending = action
    return ToolOutcome({"status": "awaiting_user_confirmation", "summary": action.summary, "note": AWAITING})


async def _load_po(ctx: ToolContext, po_id: str | None, po_number: str | None) -> dict[str, Any]:
    if po_number:
        po = await ctx.api.get(f"/purchase-orders/by-number/{po_number.strip()}")
    elif po_id:
        po = await ctx.api.get(f"/purchase-orders/{parse_uuid(po_id, 'purchase order')}")
    else:
        raise ToolError("Give a po_number (like PO-1A2B3C4D) or a po_id.")
    return await _describe_purchase_order(ctx, po)


def _fmt(value: Decimal) -> str:
    return f"{value.normalize():f}"


# ----------------------------------------------------------------------------- receive goods

class ReceiveItem(BaseModel):
    model_config = STRICT
    po_item_id: str = Field(description="The line item id (po_item_id) from get_purchase_order.")
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=2, description="Quantity received now.")


class ReceiveInput(BaseModel):
    model_config = STRICT
    po_id: str = Field(description="Purchase order id (UUID) from get_purchase_order.")
    items: list[ReceiveItem] = Field(min_length=1, max_length=20)


async def receive_purchase_order_items(ctx: ToolContext, args: ReceiveInput) -> ToolOutcome:
    po = await _load_po(ctx, args.po_id, None)
    by_id = {item["po_item_id"]: item for item in po["items"]}

    lines, body_items = [], []
    for entry in args.items:
        item = by_id.get(entry.po_item_id)
        if item is None:
            raise ToolError(f"Item {entry.po_item_id} is not on {po['po_number']}. Use the po_item_id values from get_purchase_order.")
        remaining = Decimal(item["remaining_quantity"])
        if entry.quantity > remaining:
            label = item.get("sku") or entry.po_item_id
            raise ToolError(f"Cannot receive {_fmt(entry.quantity)} of {label}: only {_fmt(remaining)} is still outstanding.")
        label = f"{item.get('sku') or 'item'} ({item.get('product_name') or 'unknown product'})"
        lines.append(f"{_fmt(entry.quantity)} × {label}")
        body_items.append({"po_item_id": entry.po_item_id, "quantity": str(entry.quantity)})

    return _prepare(ctx, PendingAction(
        tool="receive_purchase_order_items",
        summary=f"Receive goods against {po['po_number']}: " + "; ".join(lines),
        details={
            "Purchase order": f"{po['po_number']} ({po['status']})",
            "Supplier": po.get("supplier_name") or "unknown",
            "Receiving into": po.get("warehouse_name") or "unknown warehouse",
            "Items": "; ".join(lines),
        },
        method="POST",
        path=f"/purchase-orders/{po['id']}/receive",
        body={"items": body_items},
    ))


# ----------------------------------------------------------------------------- PO lifecycle

class PoActionInput(BaseModel):
    model_config = STRICT
    po_number: str | None = Field(default=None, max_length=40, description="Human PO number such as PO-1A2B3C4D.")
    po_id: str | None = Field(default=None, description="Purchase order id (UUID).")


def _po_action_tool(name: str, endpoint: str, verb: str, description: str, label: str) -> Tool:
    async def handler(ctx: ToolContext, args: PoActionInput) -> ToolOutcome:
        po = await _load_po(ctx, args.po_id, args.po_number)
        return _prepare(ctx, PendingAction(
            tool=name,
            summary=f"{verb} purchase order {po['po_number']} (currently {po['status']})",
            details={
                "Purchase order": po["po_number"],
                "Current status": po["status"],
                "Supplier": po.get("supplier_name") or "unknown",
                "Warehouse": po.get("warehouse_name") or "unknown",
                "Lines": str(len(po["items"])),
            },
            method="POST",
            path=f"/purchase-orders/{po['id']}/{endpoint}",
            body=None,
        ))

    return Tool(name, description, PoActionInput, handler, label, mutating=True)


# ----------------------------------------------------------------------------- stock movement

class MovementInput(BaseModel):
    model_config = STRICT
    product_id: str = Field(description="Product id (UUID) from the search tool.")
    warehouse_id: str = Field(description="Warehouse id (UUID) from the search tool.")
    movement_type: Literal["RECEIVE", "ISSUE", "ADJUSTMENT_INCREASE", "ADJUSTMENT_DECREASE", "DAMAGED", "RETURNED"]
    quantity: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    unit_cost: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2, description="Only meaningful for RECEIVE.")
    notes: str | None = Field(default=None, max_length=300)


async def record_inventory_movement(ctx: ToolContext, args: MovementInput) -> ToolOutcome:
    product_id = parse_uuid(args.product_id, "product")
    warehouse_id = parse_uuid(args.warehouse_id, "warehouse")
    try:
        product = await ctx.api.get(f"/products/{product_id}")
        warehouse = await ctx.api.get(f"/warehouses/{warehouse_id}")
    except ApiError as exc:
        raise ToolError(f"Could not verify the product and warehouse: {exc.message}") from exc

    body: dict[str, Any] = {
        "product_id": str(product_id),
        "warehouse_id": str(warehouse_id),
        "movement_type": args.movement_type,
        "quantity": str(args.quantity),
    }
    if args.unit_cost is not None:
        body["unit_cost"] = str(args.unit_cost)
    if args.notes:
        body["notes"] = args.notes

    summary = f"Record {args.movement_type} of {_fmt(args.quantity)} × {product['sku']} ({product['name']}) at {warehouse['name']}"
    details = {
        "Movement type": args.movement_type,
        "Product": f"{product['sku']} ({product['name']})",
        "Warehouse": warehouse["name"],
        "Quantity": _fmt(args.quantity),
    }
    if args.notes:
        details["Notes"] = args.notes
    return _prepare(ctx, PendingAction("record_inventory_movement", summary, details, "POST", "/inventory-movements/", body))


# ----------------------------------------------------------------------------- draft PO from recommendation

class DraftPoInput(BaseModel):
    model_config = STRICT
    product_id: str = Field(description="Product id (UUID) from the search tool.")
    warehouse_id: str = Field(description="Warehouse id (UUID) the order should be delivered to.")
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2, description="Omit to order the recommended quantity.")


async def create_draft_po_from_recommendation(ctx: ToolContext, args: DraftPoInput) -> ToolOutcome:
    product_id = parse_uuid(args.product_id, "product")
    warehouse_id = parse_uuid(args.warehouse_id, "warehouse")
    rec = await ctx.api.get(f"/planning/recommendations/{product_id}", warehouse_id=str(warehouse_id))
    recommended = Decimal(str(rec["recommended_order"]))
    quantity = args.quantity or recommended
    if quantity <= 0:
        raise ToolError("The planning engine does not currently recommend ordering this product (recommended order is 0).")
    if not rec.get("supplier_id"):
        raise ToolError("This product has no default supplier, so a purchase order cannot be drafted for it.")

    body: dict[str, Any] = {"warehouse_id": str(warehouse_id)}
    if args.quantity is not None:
        body["quantity"] = str(args.quantity)
    basis = "your quantity" if args.quantity is not None else "the recommended quantity"
    return _prepare(ctx, PendingAction(
        tool="create_draft_po_from_recommendation",
        summary=f"Create a DRAFT purchase order for {_fmt(quantity)} × {rec['sku']} ({rec['product_name']}) from {rec.get('supplier_name') or 'the default supplier'}",
        details={
            "Product": f"{rec['sku']} ({rec['product_name']})",
            "Supplier": rec.get("supplier_name") or "default supplier",
            "Quantity": f"{_fmt(quantity)} ({basis})",
            "Why": rec.get("explanation", ""),
        },
        method="POST",
        path=f"/planning/recommendations/{product_id}/draft-po",
        body=body,
    ))


MUTATION_TOOLS: list[Tool] = [
    Tool("receive_purchase_order_items", "Prepare receiving goods against a purchase order (stock is added once the user confirms). Get the po_id and po_item_id values from get_purchase_order first.", ReceiveInput, receive_purchase_order_items, "Prepared a goods receipt", mutating=True),
    _po_action_tool("submit_purchase_order", "submit", "Submit", "Prepare submitting a DRAFT purchase order for approval.", "Prepared a PO submission"),
    _po_action_tool("approve_purchase_order", "approve", "Approve", "Prepare approving a SUBMITTED purchase order (admins only).", "Prepared a PO approval"),
    _po_action_tool("mark_purchase_order_ordered", "mark-ordered", "Mark as ordered", "Prepare marking an APPROVED purchase order as ordered with the supplier.", "Prepared marking a PO as ordered"),
    _po_action_tool("cancel_purchase_order", "cancel", "Cancel", "Prepare cancelling a purchase order that has not received anything (admins only).", "Prepared a PO cancellation"),
    Tool("record_inventory_movement", "Prepare recording a stock movement (receive, issue, adjustment, damaged or returned).", MovementInput, record_inventory_movement, "Prepared a stock movement", mutating=True),
    Tool("create_draft_po_from_recommendation", "Prepare a DRAFT purchase order from the planning engine's recommendation for a product and warehouse.", DraftPoInput, create_draft_po_from_recommendation, "Prepared a draft purchase order", mutating=True),
]
