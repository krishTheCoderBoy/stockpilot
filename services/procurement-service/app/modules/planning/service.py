import logging
import math
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Literal

import numpy as np
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.cache import cache_get_json, cache_set_json
from app.core.config import settings
from app.modules.planning.clients import InventoryPlanningClient
from app.modules.planning.forecasting import INTERVAL_Z, ForecastSelection, select_and_forecast
from app.modules.planning.repository import PlanningRepository
from app.modules.planning.rules import (
    PlanningInputs,
    RiskLevel,
    RuleOutcome,
    average_daily_demand,
    compute_rule_outcome,
    quantize,
    rule_based_forecast_demand,
)
from app.modules.planning.schemas import (
    BacktestOut,
    DraftPurchaseOrderRequest,
    ForecastOut,
    ForecastPoint,
    HistoryPoint,
    PlanningSummary,
    RecommendationOut,
    RecommendationPage,
)
from app.modules.purchase_orders.schemas import POItemCreate, PurchaseOrderCreate
from app.modules.purchase_orders.service import PurchaseOrderService
from app.modules.suppliers.models import Supplier

logger = logging.getLogger(__name__)

ForecastMode = Literal["auto", "rules"]
RISK_ORDER = {RiskLevel.STOCKOUT_RISK: 0, RiskLevel.LOW: 1, RiskLevel.OK: 2}
FORECAST_CACHE_VERSION = "v1"


@dataclass
class _ProductContext:
    product: dict
    stock_rows: list[dict]
    incoming: Decimal
    supplier: Supplier | None
    # Oldest to newest, one entry per day, zeros included, ending yesterday.
    daily_demand: list[Decimal]


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


def _fmt(value: Decimal) -> str:
    """148.00 -> '148', 11.43 -> '11.43'; keeps explanations readable."""
    return f"{value.normalize():f}"


def _to_decimal(value: float) -> Decimal:
    return quantize(Decimal(str(round(float(value), 4))))


class PlanningService:
    def __init__(self, db: Session, authorization: str):
        self.db = db
        self.authorization = authorization
        self.repo = PlanningRepository(db)
        self.inventory = InventoryPlanningClient(authorization)

    # ------------------------------------------------------------------ public API

    def list_recommendations(
        self,
        risk: RiskLevel | None,
        supplier_id: uuid.UUID | None,
        warehouse_id: uuid.UUID | None,
        mode: ForecastMode,
        skip: int,
        limit: int,
    ) -> RecommendationPage:
        items = self._all_recommendations(warehouse_id, mode, supplier_id)
        if risk is not None:
            items = [item for item in items if item.risk == risk]
        # Most urgent first: risk class, then the least cover.
        items.sort(key=lambda r: (RISK_ORDER[r.risk], r.days_of_cover if r.days_of_cover is not None else Decimal("1e9")))
        return RecommendationPage(total=len(items), skip=skip, limit=limit, items=items[skip:skip + limit])

    def get_recommendation(self, product_id: uuid.UUID, warehouse_id: uuid.UUID | None, mode: ForecastMode) -> RecommendationOut:
        product = self.inventory.get_product(product_id)
        context = self._single_context(product, warehouse_id)
        return self._recommend(context, warehouse_id, mode)

    def summary(self, warehouse_id: uuid.UUID | None) -> PlanningSummary:
        items = self._all_recommendations(warehouse_id, "auto", None)
        counts = {level: sum(1 for item in items if item.risk == level) for level in RiskLevel}
        return PlanningSummary(
            total_products=len(items),
            recommended_purchases=sum(1 for item in items if item.recommended_order > 0),
            stockout_risk=counts[RiskLevel.STOCKOUT_RISK],
            low=counts[RiskLevel.LOW],
            ok=counts[RiskLevel.OK],
        )

    def get_forecast(self, product_id: uuid.UUID, warehouse_id: uuid.UUID | None, horizon_days: int | None) -> ForecastOut:
        product = self.inventory.get_product(product_id)
        context = self._single_context(product, warehouse_id, need_stock=False)
        lead_time, _ = self._lead_time(context.supplier)
        horizon = horizon_days or lead_time + settings.planning_review_period_days
        payload = self._forecast_payload(product_id, warehouse_id, context.daily_demand, horizon)

        start, end = self._history_window()
        history = [
            HistoryPoint(bucket_start=start + timedelta(days=i), quantity=quantize(value))
            for i, value in enumerate(context.daily_demand)
        ]
        forecast_start = end + timedelta(days=1)
        forecast = [
            ForecastPoint(
                bucket_start=forecast_start + timedelta(days=i),
                mean=_to_decimal(payload["mean"][i]),
                lower=_to_decimal(payload["lower"][i]),
                upper=_to_decimal(payload["upper"][i]),
            )
            for i in range(len(payload["mean"]))
        ]
        return ForecastOut(
            product_id=product_id,
            warehouse_id=warehouse_id,
            model_used=payload["model_used"],
            model_label=payload["model_label"],
            model_reason=payload["reason"],
            history_length=payload["history_length"],
            horizon_days=horizon,
            total_forecast_demand=_to_decimal(payload["total"]),
            total_lower=_to_decimal(payload["total_lower"]),
            total_upper=_to_decimal(payload["total_upper"]),
            backtest=self._backtest_out(payload["backtest"]),
            history=history,
            forecast=forecast,
            generated_at=datetime.now(timezone.utc),
        )

    def create_draft_po(self, product_id: uuid.UUID, payload: DraftPurchaseOrderRequest, created_by: str):
        """Turn a recommendation into a DRAFT purchase order through the normal PO service,
        so supplier, warehouse and product validation and the PO lifecycle are unchanged."""
        # Recomputed here rather than trusting numbers from the client.
        recommendation = self.get_recommendation(product_id, payload.warehouse_id, "auto")
        if recommendation.supplier_id is None:
            raise HTTPException(status_code=400, detail="This product has no default supplier; assign one before ordering")
        quantity = payload.quantity or recommendation.recommended_order
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="No purchase is recommended for this product right now")

        today = datetime.now(timezone.utc).date()
        po_payload = PurchaseOrderCreate(
            supplier_id=recommendation.supplier_id,
            warehouse_id=payload.warehouse_id,
            notes=f"Draft from planning recommendation. {recommendation.explanation}",
            expected_date=today + timedelta(days=recommendation.lead_time_days),
            items=[POItemCreate(product_id=product_id, ordered_quantity=quantity, unit_price=recommendation.unit_price)],
        )
        return PurchaseOrderService(self.db).create_po(po_payload, created_by, self.authorization)

    # ------------------------------------------------------------------ data loading

    def _history_window(self) -> tuple[date, date]:
        # Today is left out: it is incomplete, and a half-day of sales reads as a demand drop.
        end = datetime.now(timezone.utc).date() - timedelta(days=1)
        return end - timedelta(days=settings.planning_history_days - 1), end

    @staticmethod
    def _zero_fill(day_map: dict[date, str], start: date, end: date) -> list[Decimal]:
        return [_dec(day_map.get(start + timedelta(days=i), "0")) for i in range((end - start).days + 1)]

    def _all_recommendations(
        self, warehouse_id: uuid.UUID | None, mode: ForecastMode, supplier_id: uuid.UUID | None
    ) -> list[RecommendationOut]:
        products = self.inventory.list_active_products()
        if supplier_id is not None:
            products = [p for p in products if p.get("default_supplier_id") == str(supplier_id)]
        if not products:
            return []

        stock_by_product: dict[str, list[dict]] = {}
        for row in self.inventory.list_stock_rows(warehouse_id):
            stock_by_product.setdefault(row["product_id"], []).append(row)

        incoming = self.repo.incoming_by_product(warehouse_id)
        suppliers = self.repo.suppliers_by_id(
            {uuid.UUID(p["default_supplier_id"]) for p in products if p.get("default_supplier_id")}
        )
        start, end = self._history_window()
        demand = self.inventory.get_daily_demand([uuid.UUID(p["id"]) for p in products], start, end, warehouse_id)

        results: list[RecommendationOut] = []
        for product in products:
            product_id = uuid.UUID(product["id"])
            supplier_uuid = uuid.UUID(product["default_supplier_id"]) if product.get("default_supplier_id") else None
            context = _ProductContext(
                product=product,
                stock_rows=stock_by_product.get(product["id"], []),
                incoming=incoming.get(product_id, Decimal("0")),
                supplier=suppliers.get(supplier_uuid) if supplier_uuid else None,
                daily_demand=self._zero_fill(demand.get(product_id, {}), start, end),
            )
            results.append(self._recommend(context, warehouse_id, mode))
        return results

    def _single_context(self, product: dict, warehouse_id: uuid.UUID | None, need_stock: bool = True) -> _ProductContext:
        product_id = uuid.UUID(product["id"])
        supplier_uuid = uuid.UUID(product["default_supplier_id"]) if product.get("default_supplier_id") else None
        suppliers = self.repo.suppliers_by_id({supplier_uuid} if supplier_uuid else set())
        start, end = self._history_window()
        demand = self.inventory.get_daily_demand([product_id], start, end, warehouse_id)
        return _ProductContext(
            product=product,
            stock_rows=self.inventory.list_stock_rows(warehouse_id, product_id) if need_stock else [],
            incoming=self.repo.incoming_by_product(warehouse_id).get(product_id, Decimal("0")),
            supplier=suppliers.get(supplier_uuid) if supplier_uuid else None,
            daily_demand=self._zero_fill(demand.get(product_id, {}), start, end),
        )

    # ------------------------------------------------------------------ the calculation

    @staticmethod
    def _lead_time(supplier: Supplier | None) -> tuple[int, Literal["supplier", "default"]]:
        if supplier is not None and supplier.lead_time_days and supplier.lead_time_days > 0:
            return supplier.lead_time_days, "supplier"
        return settings.planning_default_lead_time_days, "default"

    @staticmethod
    def _safety_stock(product: dict, rows: list[dict]) -> tuple[Decimal, Literal["inventory_override", "product_reorder_point"]]:
        # Inventory overrides win, but only when every stock row has one: mixing overrides
        # with the product-wide figure would double count the product's own buffer.
        overrides = [_dec(r["safety_stock_override"]) for r in rows if r.get("safety_stock_override") is not None]
        if rows and len(overrides) == len(rows):
            return sum(overrides, Decimal("0")), "inventory_override"
        # Product has no safety-stock field of its own; reorder_point is its only buffer.
        return _dec(product["reorder_point"]), "product_reorder_point"

    def _recommend(self, ctx: _ProductContext, warehouse_id: uuid.UUID | None, mode: ForecastMode) -> RecommendationOut:
        product = ctx.product
        product_id = uuid.UUID(product["id"])
        lead_time, lead_source = self._lead_time(ctx.supplier)
        review = settings.planning_review_period_days
        horizon = lead_time + review

        on_hand = sum((_dec(r["on_hand_quantity"]) for r in ctx.stock_rows), Decimal("0"))
        reserved = sum((_dec(r["reserved_quantity"]) for r in ctx.stock_rows), Decimal("0"))
        safety, safety_source = self._safety_stock(product, ctx.stock_rows)
        avg_daily = average_daily_demand(ctx.daily_demand, settings.planning_rule_window_days)

        if mode == "rules":
            forecast_demand = rule_based_forecast_demand(avg_daily, lead_time, review)
            forecast_lower = forecast_upper = forecast_demand
            model_used, model_label = "rule_based_average", "Rule-based average"
            model_reason = (
                f"Average daily demand over the last {settings.planning_rule_window_days} days "
                f"× {horizon} days."
            )
            history_length = self._active_history_length(ctx.daily_demand)
            backtest_mae: Decimal | None = None
        else:
            payload = self._forecast_payload(product_id, warehouse_id, ctx.daily_demand, horizon)
            forecast_demand = _to_decimal(payload["total"])
            forecast_lower = _to_decimal(payload["total_lower"])
            forecast_upper = _to_decimal(payload["total_upper"])
            model_used, model_label, model_reason = payload["model_used"], payload["model_label"], payload["reason"]
            history_length = payload["history_length"]
            backtest = payload["backtest"]
            backtest_mae = _to_decimal(backtest["mae"]) if backtest else None

        multiple = _dec(product.get("min_order_quantity") or "1")
        outcome = compute_rule_outcome(PlanningInputs(
            on_hand=on_hand,
            reserved=reserved,
            incoming=ctx.incoming,
            safety_stock=safety,
            forecast_demand=forecast_demand,
            avg_daily_demand=avg_daily,
            lead_time_days=lead_time,
            min_order_multiple=multiple,
        ))

        reasons = self._reasons(
            ctx, outcome, mode, on_hand, reserved, safety, safety_source, avg_daily, forecast_demand,
            lead_time, lead_source, review, horizon, model_label, model_reason, history_length, multiple,
        )
        explanation = (
            f"Current available = {_fmt(outcome.current_available)}, Incoming = {_fmt(ctx.incoming)}, "
            f"Safety stock = {_fmt(safety)}, Forecast demand = {_fmt(forecast_demand)}, "
            f"Recommended order = {_fmt(outcome.recommended_order)}. Risk: {outcome.risk.value}"
            + (f", about {_fmt(outcome.days_of_cover)} days of cover." if outcome.days_of_cover is not None else ", no recent demand.")
        )

        return RecommendationOut(
            product_id=product_id,
            sku=product["sku"],
            product_name=product["name"],
            warehouse_id=warehouse_id,
            supplier_id=ctx.supplier.id if ctx.supplier else (uuid.UUID(product["default_supplier_id"]) if product.get("default_supplier_id") else None),
            supplier_name=ctx.supplier.name if ctx.supplier else None,
            lead_time_days=lead_time,
            lead_time_source=lead_source,
            review_period_days=review,
            horizon_days=horizon,
            on_hand=quantize(on_hand),
            reserved=quantize(reserved),
            current_available=outcome.current_available,
            incoming=quantize(ctx.incoming),
            safety_stock=quantize(safety),
            safety_stock_source=safety_source,
            avg_daily_demand=avg_daily,
            forecast_demand=forecast_demand,
            forecast_lower=forecast_lower,
            forecast_upper=forecast_upper,
            min_order_multiple=multiple,
            recommended_order=outcome.recommended_order,
            unit_price=_dec(product["unit_price"]),
            days_of_cover=outcome.days_of_cover,
            risk=outcome.risk,
            forecast_mode=mode,
            model_used=model_used,
            model_label=model_label,
            model_reason=model_reason,
            history_length=history_length,
            backtest_mae=backtest_mae,
            explanation=explanation,
            reasons=reasons,
        )

    @staticmethod
    def _reasons(
        ctx: _ProductContext, outcome: RuleOutcome, mode: ForecastMode, on_hand: Decimal, reserved: Decimal,
        safety: Decimal, safety_source: str, avg_daily: Decimal, forecast_demand: Decimal, lead_time: int,
        lead_source: str, review: int, horizon: int, model_label: str, model_reason: str, history_length: int,
        multiple: Decimal,
    ) -> list[str]:
        reasons = [
            f"Current available = {_fmt(outcome.current_available)} (on hand {_fmt(on_hand)} − reserved {_fmt(reserved)}).",
            f"Incoming = {_fmt(ctx.incoming)} still to arrive on approved, ordered or partially received purchase orders.",
            (
                f"Safety stock = {_fmt(safety)} (set on the inventory record)."
                if safety_source == "inventory_override"
                else f"Safety stock = {_fmt(safety)} (the product's reorder point; no inventory override is set)."
            ),
        ]
        if ctx.supplier is not None and lead_source == "supplier":
            reasons.append(f"Lead time = {lead_time} days from supplier {ctx.supplier.name}.")
        else:
            why = "the product has no default supplier" if ctx.supplier is None else "its supplier has no lead time recorded"
            reasons.append(f"Lead time = {lead_time} days (the configured default, because {why}).")
        if mode == "rules":
            reasons.append(
                f"Forecast demand = {_fmt(forecast_demand)}: average {_fmt(avg_daily)} per day over the last "
                f"{settings.planning_rule_window_days} days × {horizon} days ({lead_time} lead time + {review} review period)."
            )
        else:
            reasons.append(
                f"Forecast demand = {_fmt(forecast_demand)} over the next {horizon} days "
                f"({lead_time} lead time + {review} review period). Model: {model_label}. {model_reason} "
                f"History used: {history_length} days."
            )
        needed = f"max(0, {_fmt(forecast_demand)} + {_fmt(safety)} − {_fmt(outcome.current_available)} − {_fmt(ctx.incoming)}) = {_fmt(outcome.needed_quantity)}"
        if outcome.rounded_up:
            reasons.append(f"Recommended order = {needed}, rounded up to a multiple of {_fmt(multiple)} = {_fmt(outcome.recommended_order)}.")
        else:
            reasons.append(f"Recommended order = {needed}.")

        if outcome.risk == RiskLevel.STOCKOUT_RISK:
            cover = (
                "stock is already at or below zero"
                if outcome.current_available <= 0
                else f"available plus incoming covers about {_fmt(quantize((outcome.current_available + ctx.incoming) / avg_daily))} days at {_fmt(avg_daily)} per day"
            )
            reasons.append(f"Stockout risk: {cover}, which is shorter than the {lead_time}-day lead time.")
        elif outcome.risk == RiskLevel.LOW:
            reasons.append("Low: stock and inbound orders do not cover forecast demand plus safety stock.")
        else:
            reasons.append("OK: stock and inbound orders cover forecast demand plus safety stock.")
        return reasons

    # ------------------------------------------------------------------ forecasting + cache

    @staticmethod
    def _active_history_length(daily: list[Decimal]) -> int:
        first = next((i for i, v in enumerate(daily) if v > 0), None)
        return 0 if first is None else len(daily) - first

    def _forecast_payload(
        self, product_id: uuid.UUID, warehouse_id: uuid.UUID | None, daily: list[Decimal], horizon: int
    ) -> dict[str, Any]:
        _, end = self._history_window()
        key = f"planning:forecast:{FORECAST_CACHE_VERSION}:{product_id}:{warehouse_id or 'all'}:{horizon}:{end.isoformat()}"
        cached = cache_get_json(key)
        if cached is not None:
            return cached
        selection = select_and_forecast(
            np.array([float(v) for v in daily]), horizon, settings.planning_backtest_holdout_days
        )
        payload = self._selection_to_payload(selection)
        cache_set_json(key, payload, settings.planning_forecast_cache_seconds)
        return payload

    @staticmethod
    def _selection_to_payload(selection: ForecastSelection) -> dict[str, Any]:
        band = selection.band
        horizon = len(band.mean)
        total = float(np.sum(band.mean))
        # Errors on different days are treated as independent, so uncertainty over the
        # whole horizon grows with sqrt(days), not linearly.
        spread = INTERVAL_Z * band.sigma * math.sqrt(horizon)
        backtest = None
        if selection.selected_backtest is not None and selection.baseline_backtest is not None:
            backtest = {
                "holdout_days": selection.holdout_days,
                "mae": selection.selected_backtest.mae,
                "mape": selection.selected_backtest.mape,
                "baseline_mae": selection.baseline_backtest.mae,
                "baseline_mape": selection.baseline_backtest.mape,
            }
        return {
            "model_used": selection.model_used,
            "model_label": selection.model_label,
            "reason": selection.reason,
            "history_length": selection.history_length,
            "mean": [float(x) for x in band.mean],
            "lower": [float(x) for x in band.lower],
            "upper": [float(x) for x in band.upper],
            "total": total,
            "total_lower": max(0.0, total - spread),
            "total_upper": total + spread,
            "backtest": backtest,
        }

    @staticmethod
    def _backtest_out(backtest: dict[str, Any] | None) -> BacktestOut | None:
        if backtest is None:
            return None

        def pct(value: float | None) -> Decimal | None:
            return None if value is None else _to_decimal(value * 100)

        return BacktestOut(
            holdout_days=backtest["holdout_days"],
            mae=_to_decimal(backtest["mae"]),
            mape=pct(backtest["mape"]),
            baseline_mae=_to_decimal(backtest["baseline_mae"]),
            baseline_mape=pct(backtest["baseline_mape"]),
        )
