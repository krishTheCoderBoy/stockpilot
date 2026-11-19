import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.planning.rules import RiskLevel


class HistoryPoint(BaseModel):
    bucket_start: date
    quantity: Decimal


class ForecastPoint(BaseModel):
    bucket_start: date
    mean: Decimal
    lower: Decimal
    upper: Decimal


class BacktestOut(BaseModel):
    holdout_days: int
    mae: Decimal
    mape: Decimal | None
    baseline_mae: Decimal
    baseline_mape: Decimal | None


class ForecastOut(BaseModel):
    product_id: uuid.UUID
    warehouse_id: uuid.UUID | None
    model_used: str
    model_label: str
    model_reason: str
    history_length: int
    horizon_days: int
    total_forecast_demand: Decimal
    total_lower: Decimal
    total_upper: Decimal
    backtest: BacktestOut | None
    history: list[HistoryPoint]
    forecast: list[ForecastPoint]
    generated_at: datetime


class RecommendationOut(BaseModel):
    product_id: uuid.UUID
    sku: str
    product_name: str
    warehouse_id: uuid.UUID | None
    supplier_id: uuid.UUID | None
    supplier_name: str | None
    lead_time_days: int
    lead_time_source: Literal["supplier", "default"]
    review_period_days: int
    horizon_days: int

    on_hand: Decimal
    reserved: Decimal
    current_available: Decimal
    incoming: Decimal
    safety_stock: Decimal
    safety_stock_source: Literal["inventory_override", "product_reorder_point"]
    avg_daily_demand: Decimal
    forecast_demand: Decimal
    forecast_lower: Decimal
    forecast_upper: Decimal
    min_order_multiple: Decimal
    recommended_order: Decimal
    unit_price: Decimal
    days_of_cover: Decimal | None
    risk: RiskLevel

    forecast_mode: Literal["auto", "rules"]
    model_used: str
    model_label: str
    model_reason: str
    history_length: int
    backtest_mae: Decimal | None

    explanation: str
    reasons: list[str]


class RecommendationPage(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[RecommendationOut]


class PlanningSummary(BaseModel):
    total_products: int
    recommended_purchases: int
    stockout_risk: int
    low: int
    ok: int


class DraftPurchaseOrderRequest(BaseModel):
    warehouse_id: uuid.UUID
    # Omit to order exactly what the engine recommends.
    quantity: Decimal | None = Field(default=None, gt=0)
