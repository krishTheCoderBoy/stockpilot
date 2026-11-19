"""Read-only tools. Each is a thin wrapper over one or two existing public GET endpoints."""
import asyncio
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.tools.api import ApiError
from app.tools.base import Tool, ToolContext, ToolError, ToolOutcome, parse_uuid
from app.tools.trim import pick

STRICT = ConfigDict(extra="forbid")

PRODUCT_KEYS = ("id", "sku", "name", "unit_price", "unit_of_measure", "reorder_point", "min_order_quantity", "is_active", "default_supplier_id")
SUPPLIER_KEYS = ("id", "code", "name", "lead_time_days", "is_active")
WAREHOUSE_KEYS = ("id", "code", "name", "city", "state", "warehouse_type", "is_active")
MOVEMENT_KEYS = ("id", "movement_type", "quantity", "unit_cost", "reference_type", "notes", "created_at", "product_id", "warehouse_id")
RECOMMENDATION_KEYS = (
    "product_id", "sku", "product_name", "warehouse_id", "risk", "current_available", "incoming",
    "safety_stock", "forecast_demand", "horizon_days", "recommended_order", "days_of_cover",
    "lead_time_days", "lead_time_source", "supplier_id", "supplier_name", "model_label", "explanation",
)


def _po_summary_row(po: dict[str, Any]) -> dict[str, Any]:
    row = pick(po, ("id", "po_number", "status", "supplier_id", "warehouse_id", "expected_date", "created_at"))
    row["item_count"] = len(po.get("items", []))
    return row


# ----------------------------------------------------------------------------- search

class SearchInput(BaseModel):
    model_config = STRICT
    entity: Literal["products", "suppliers", "warehouses", "purchase_orders", "movements"] = Field(
        description="Which kind of record to search."
    )
    query: str = Field(min_length=1, max_length=100, description="Free text: a name, SKU, code, PO number or note.")
    limit: int = Field(default=5, ge=1, le=10, description="Maximum number of results.")


_SEARCH_PATHS = {
    "products": "/products/search",
    "suppliers": "/suppliers/search",
    "warehouses": "/warehouses/search",
    "purchase_orders": "/purchase-orders/search",
    "movements": "/inventory-movements/search",
}


async def search_records(ctx: ToolContext, args: SearchInput) -> ToolOutcome:
    rows = await ctx.api.get(_SEARCH_PATHS[args.entity], q=args.query, limit=args.limit)
    if args.entity == "products":
        shaped = [pick(r, PRODUCT_KEYS) for r in rows]
    elif args.entity == "suppliers":
        shaped = [pick(r, SUPPLIER_KEYS) for r in rows]
    elif args.entity == "warehouses":
        shaped = [pick(r, WAREHOUSE_KEYS) for r in rows]
    elif args.entity == "purchase_orders":
        shaped = [_po_summary_row(r) for r in rows]
    else:
        shaped = [pick(r, MOVEMENT_KEYS) for r in rows]
    return ToolOutcome({"entity": args.entity, "count": len(shaped), "results": shaped})


# ----------------------------------------------------------------------------- stock

class StockInput(BaseModel):
    model_config = STRICT
    product_id: str | None = Field(default=None, description="Product id (UUID), from the search tool.")
    warehouse_id: str | None = Field(default=None, description="Warehouse id (UUID), from the search tool.")


async def get_stock_levels(ctx: ToolContext, args: StockInput) -> ToolOutcome:
    if not args.product_id and not args.warehouse_id:
        raise ToolError("Give a product_id, a warehouse_id, or both. Use the search tool to find ids.")
    product_id = parse_uuid(args.product_id, "product") if args.product_id else None
    warehouse_id = parse_uuid(args.warehouse_id, "warehouse") if args.warehouse_id else None

    if product_id and warehouse_id:
        rows = [await ctx.api.get(f"/inventory/{product_id}/{warehouse_id}")]
    elif product_id:
        rows = await ctx.api.get(f"/inventory/product/{product_id}")
    else:
        rows = await ctx.api.get(f"/inventory/warehouse/{warehouse_id}")

    # Names make the answer readable; failing to fetch them must not fail the lookup.
    names, product = {}, None
    try:
        names = {w["id"]: w["name"] for w in await ctx.api.get("/warehouses/", limit=200)}
        if product_id:
            product = pick(await ctx.api.get(f"/products/{product_id}"), ("id", "sku", "name", "reorder_point"))
    except ApiError:
        pass

    shaped = [
        {
            **pick(r, ("product_id", "warehouse_id", "on_hand_quantity", "reserved_quantity", "available_quantity")),
            "warehouse_name": names.get(r["warehouse_id"]),
        }
        for r in rows
    ]
    return ToolOutcome({"product": product, "stock": shaped})


class LowStockInput(BaseModel):
    model_config = STRICT
    limit: int = Field(default=15, ge=1, le=30)


async def list_low_stock(ctx: ToolContext, args: LowStockInput) -> ToolOutcome:
    rows = await ctx.api.get("/inventory/low-stock", limit=args.limit)
    keys = ("sku", "product_name", "warehouse_name", "on_hand_quantity", "reserved_quantity", "available_quantity", "reorder_point", "product_id", "warehouse_id")
    return ToolOutcome({"count": len(rows), "low_stock": [pick(r, keys) for r in rows]})


# ----------------------------------------------------------------------------- purchase orders

class PurchaseOrderLookupInput(BaseModel):
    model_config = STRICT
    po_number: str | None = Field(default=None, max_length=40, description="Human PO number such as PO-1A2B3C4D.")
    po_id: str | None = Field(default=None, description="Purchase order id (UUID).")


async def get_purchase_order(ctx: ToolContext, args: PurchaseOrderLookupInput) -> ToolOutcome:
    if args.po_number:
        po = await ctx.api.get(f"/purchase-orders/by-number/{args.po_number.strip()}")
    elif args.po_id:
        po = await ctx.api.get(f"/purchase-orders/{parse_uuid(args.po_id, 'purchase order')}")
    else:
        raise ToolError("Give a po_number (like PO-1A2B3C4D) or a po_id.")
    return ToolOutcome(await _describe_purchase_order(ctx, po))


async def _describe_purchase_order(ctx: ToolContext, po: dict[str, Any]) -> dict[str, Any]:
    """The PO plus supplier, warehouse and product names, so item ids can be turned into
    words without extra tool calls. Lookups that fail simply leave the name out."""
    items = po.get("items", [])
    product_ids = list({item["product_id"] for item in items})[:15]

    async def fetch(path: str) -> dict | None:
        try:
            return await ctx.api.get(path)
        except ApiError:
            return None

    supplier, warehouse, *products = await asyncio.gather(
        fetch(f"/suppliers/{po['supplier_id']}"),
        fetch(f"/warehouses/{po['warehouse_id']}"),
        *[fetch(f"/products/{pid}") for pid in product_ids],
    )
    product_by_id = {p["id"]: p for p in products if p}

    shaped_items = []
    for item in items:
        product = product_by_id.get(item["product_id"], {})
        ordered, received = Decimal(str(item["ordered_quantity"])), Decimal(str(item["received_quantity"]))
        shaped_items.append({
            "po_item_id": item["id"],
            "product_id": item["product_id"],
            "sku": product.get("sku"),
            "product_name": product.get("name"),
            "ordered_quantity": item["ordered_quantity"],
            "received_quantity": item["received_quantity"],
            "remaining_quantity": str(ordered - received),
            "unit_price": item["unit_price"],
        })
    return {
        **pick(po, ("id", "po_number", "status", "expected_date", "notes", "created_at", "supplier_id", "warehouse_id")),
        "supplier_name": supplier.get("name") if supplier else None,
        "warehouse_name": warehouse.get("name") if warehouse else None,
        "items": shaped_items,
    }


class PurchaseOrderListInput(BaseModel):
    model_config = STRICT
    status: Literal["DRAFT", "SUBMITTED", "APPROVED", "ORDERED", "PARTIALLY_RECEIVED", "RECEIVED", "CLOSED", "CANCELLED"] | None = None
    limit: int = Field(default=10, ge=1, le=20)


async def list_purchase_orders(ctx: ToolContext, args: PurchaseOrderListInput) -> ToolOutcome:
    rows = await ctx.api.get("/purchase-orders/", status=args.status, limit=args.limit)
    return ToolOutcome({"count": len(rows), "purchase_orders": [_po_summary_row(r) for r in rows]})


# ----------------------------------------------------------------------------- planning

class RecommendationsInput(BaseModel):
    model_config = STRICT
    product_id: str | None = Field(default=None, description="Set for one product's full recommendation and reasons.")
    risk: Literal["OK", "LOW", "STOCKOUT_RISK"] | None = None
    supplier_id: str | None = None
    warehouse_id: str | None = None
    limit: int = Field(default=10, ge=1, le=15)


async def get_recommendations(ctx: ToolContext, args: RecommendationsInput) -> ToolOutcome:
    if args.product_id:
        pid = parse_uuid(args.product_id, "product")
        row = await ctx.api.get(f"/planning/recommendations/{pid}", warehouse_id=args.warehouse_id)
        return ToolOutcome({**pick(row, RECOMMENDATION_KEYS), "reasons": row.get("reasons", [])})
    page = await ctx.api.get(
        "/planning/recommendations",
        risk=args.risk, supplier_id=args.supplier_id, warehouse_id=args.warehouse_id, limit=args.limit,
    )
    return ToolOutcome({
        "total_matching": page["total"],
        "shown": len(page["items"]),
        "recommendations": [pick(r, RECOMMENDATION_KEYS) for r in page["items"]],
    })


class StockoutRiskInput(BaseModel):
    model_config = STRICT
    warehouse_id: str | None = None
    limit: int = Field(default=10, ge=1, le=15)


async def get_stockout_risk(ctx: ToolContext, args: StockoutRiskInput) -> ToolOutcome:
    page = await ctx.api.get(
        "/planning/recommendations", risk="STOCKOUT_RISK", warehouse_id=args.warehouse_id, limit=args.limit
    )
    return ToolOutcome({
        "products_at_stockout_risk": page["total"],
        "shown": len(page["items"]),
        "items": [pick(r, RECOMMENDATION_KEYS) for r in page["items"]],
    })


class ForecastInput(BaseModel):
    model_config = STRICT
    product_id: str = Field(description="Product id (UUID), from the search tool.")
    warehouse_id: str | None = None
    horizon_days: int | None = Field(default=None, ge=1, le=90, description="Days ahead; defaults to lead time + review period.")


async def get_product_forecast(ctx: ToolContext, args: ForecastInput) -> ToolOutcome:
    pid = parse_uuid(args.product_id, "product")
    data = await ctx.api.get(f"/planning/forecast/{pid}", warehouse_id=args.warehouse_id, horizon_days=args.horizon_days)
    recent = [h["quantity"] for h in data["history"][-14:]]
    return ToolOutcome({
        **pick(data, ("product_id", "model_label", "model_reason", "history_length", "horizon_days",
                      "total_forecast_demand", "total_lower", "total_upper", "backtest")),
        "recent_daily_demand_last_14_days": recent,
        "forecast_daily_mean_next_14_days": [f["mean"] for f in data["forecast"][:14]],
        "forecast_starts": data["forecast"][0]["bucket_start"] if data["forecast"] else None,
    })


# ----------------------------------------------------------------------------- movements

class MovementHistoryInput(BaseModel):
    model_config = STRICT
    product_id: str = Field(description="Product id (UUID), from the search tool.")
    limit: int = Field(default=10, ge=1, le=20)


async def get_movement_history(ctx: ToolContext, args: MovementHistoryInput) -> ToolOutcome:
    pid = parse_uuid(args.product_id, "product")
    rows = await ctx.api.get(f"/inventory-movements/product/{pid}", limit=args.limit)
    return ToolOutcome({"count": len(rows), "movements": [pick(r, MOVEMENT_KEYS) for r in rows[: args.limit]]})


READ_TOOLS: list[Tool] = [
    Tool("search_records", "Search products, suppliers, warehouses, purchase orders or stock movements by free text, to find ids before calling other tools. If you already know a purchase order's number (like PO-1A2B3C4D), do not search: call get_purchase_order with it.", SearchInput, search_records, "Searched records"),
    Tool("get_stock_levels", "Current on-hand, reserved and available stock for a product and/or warehouse.", StockInput, get_stock_levels, "Checked stock levels"),
    Tool("list_low_stock", "Stock rows whose available quantity is at or below the product's reorder point.", LowStockInput, list_low_stock, "Listed low-stock items"),
    Tool("get_purchase_order", "Look up one purchase order by PO number or id: status, supplier, expected date and line items with item ids and remaining quantities.", PurchaseOrderLookupInput, get_purchase_order, "Looked up a purchase order"),
    Tool("list_purchase_orders", "List recent purchase orders, optionally filtered by status.", PurchaseOrderListInput, list_purchase_orders, "Listed purchase orders"),
    Tool("get_recommendations", "Reorder recommendations from the planning engine (what to order and why), for one product or a filtered list. Each includes the engine's own explanation.", RecommendationsInput, get_recommendations, "Checked reorder recommendations"),
    Tool("get_stockout_risk", "Products the planning engine flags as at risk of running out before a new order could arrive, most urgent first.", StockoutRiskInput, get_stockout_risk, "Checked stockout risk"),
    Tool("get_product_forecast", "Demand forecast for one product: model used, backtest error, total expected demand and the next days.", ForecastInput, get_product_forecast, "Checked the demand forecast"),
    Tool("get_movement_history", "Most recent stock movements for a product.", MovementHistoryInput, get_movement_history, "Checked movement history"),
]
