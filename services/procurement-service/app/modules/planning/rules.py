"""Reorder rules. Pure functions: no I/O, no clock, no database.

The forecast is an *input* here (`PlanningInputs.forecast_demand`). Swapping the
rule-based forecast for a statistical one changes what is passed in, never these rules.
"""
import enum
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from typing import Sequence

QUANTITY_PLACES = Decimal("0.01")
ZERO = Decimal("0")


class RiskLevel(str, enum.Enum):
    OK = "OK"
    LOW = "LOW"
    STOCKOUT_RISK = "STOCKOUT_RISK"


@dataclass(frozen=True)
class PlanningInputs:
    on_hand: Decimal
    reserved: Decimal
    incoming: Decimal
    safety_stock: Decimal
    forecast_demand: Decimal
    avg_daily_demand: Decimal
    lead_time_days: int
    min_order_multiple: Decimal


@dataclass(frozen=True)
class RuleOutcome:
    current_available: Decimal
    # What the formula asks for before the order is rounded up to a multiple.
    needed_quantity: Decimal
    recommended_order: Decimal
    rounded_up: bool
    days_of_cover: Decimal | None
    risk: RiskLevel


def quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTITY_PLACES)


def average_daily_demand(daily_demand: Sequence[Decimal], window_days: int) -> Decimal:
    """Mean over the last `window_days` days. Days with no sales must be present as zeros,
    otherwise slow movers look busier than they are."""
    window = list(daily_demand)[-window_days:] if window_days > 0 else []
    if not window:
        return ZERO
    return quantize(sum(window, ZERO) / Decimal(len(window)))


def rule_based_forecast_demand(avg_daily: Decimal, lead_time_days: int, review_period_days: int) -> Decimal:
    """Demand expected until a new order placed today could be received and reviewed again."""
    return quantize(avg_daily * Decimal(lead_time_days + review_period_days))


def round_up_to_multiple(quantity: Decimal, multiple: Decimal) -> Decimal:
    step = multiple if multiple > 0 else Decimal("1")
    return (quantity / step).to_integral_value(rounding=ROUND_CEILING) * step


def compute_rule_outcome(inputs: PlanningInputs) -> RuleOutcome:
    available = inputs.on_hand - inputs.reserved
    needed = max(ZERO, inputs.forecast_demand + inputs.safety_stock - available - inputs.incoming)

    if needed > 0:
        recommended = quantize(round_up_to_multiple(needed, inputs.min_order_multiple))
        rounded_up = recommended > quantize(needed)
    else:
        recommended, rounded_up = ZERO, False

    has_demand = inputs.avg_daily_demand > 0
    days_of_cover = quantize(available / inputs.avg_daily_demand) if has_demand else None

    # Stockout risk asks "will stock plus what is already inbound last until a new order
    # could arrive?". Inbound is counted as if it lands on time, which is optimistic, but
    # it is the same assumption the order quantity makes.
    if has_demand and (available <= 0 or (available + inputs.incoming) / inputs.avg_daily_demand < inputs.lead_time_days):
        risk = RiskLevel.STOCKOUT_RISK
    elif recommended > 0:
        risk = RiskLevel.LOW
    else:
        risk = RiskLevel.OK

    return RuleOutcome(
        current_available=quantize(available),
        needed_quantity=quantize(needed),
        recommended_order=recommended,
        rounded_up=rounded_up,
        days_of_cover=days_of_cover,
        risk=risk,
    )
