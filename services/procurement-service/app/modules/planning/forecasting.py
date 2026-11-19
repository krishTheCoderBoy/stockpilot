"""Demand forecasting behind a small `Forecaster` interface.

Daily history in, a daily forecast with an uncertainty band out. numpy floats are used
inside this module only; the service converts to Decimal at the boundary.

Three forecasters, deliberately simple:
  - MovingAverageForecaster: the baseline everything else has to beat.
  - ExponentialSmoothingForecaster: simple exponential smoothing (level only).
  - HoltWintersForecaster: damped trend + additive weekly seasonality (needs statsmodels).

`select_and_forecast` backtests the candidates on the most recent days and keeps one only
if it clearly beats the baseline; otherwise the baseline is used and the reason says so.
"""
import logging
import math
import warnings
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

try:  # statsmodels is optional: without it the candidates are just SES and the baseline.
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    HAS_STATSMODELS = True
except ImportError:  # pragma: no cover - depends on the environment
    HAS_STATSMODELS = False

logger = logging.getLogger(__name__)

SEASONAL_PERIOD = 7
# 80% two-sided interval for normally distributed errors.
INTERVAL_Z = 1.2816
# Below this much (active) history no statistical model is trusted.
MIN_HISTORY_FOR_MODELS = 28
BASELINE_WINDOW = 14
# A candidate must beat the baseline's backtest MAE by at least this fraction.
MIN_IMPROVEMENT = 0.05


@dataclass(frozen=True)
class ForecastBand:
    mean: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    sigma: float


class Forecaster(Protocol):
    name: str
    label: str

    def forecast(self, history: np.ndarray, horizon: int) -> ForecastBand: ...


def _band(mean: np.ndarray, sigma: float) -> ForecastBand:
    mean = np.clip(mean, 0.0, None)
    spread = INTERVAL_Z * sigma
    return ForecastBand(mean=mean, lower=np.clip(mean - spread, 0.0, None), upper=mean + spread, sigma=sigma)


def _residual_sigma(residuals: np.ndarray) -> float:
    residuals = residuals[np.isfinite(residuals)]
    return float(np.std(residuals, ddof=1)) if residuals.size > 1 else 0.0


class MovingAverageForecaster:
    name = "moving_average"
    label = "Moving average"

    def __init__(self, window: int = BASELINE_WINDOW) -> None:
        self.window = window

    def forecast(self, history: np.ndarray, horizon: int) -> ForecastBand:
        window = max(1, min(self.window, len(history)))
        level = float(np.mean(history[-window:])) if len(history) else 0.0
        # One-step-ahead errors of the same rule, replayed over the history.
        errors = [
            history[t] - float(np.mean(history[t - window:t]))
            for t in range(window, len(history))
        ]
        return _band(np.full(horizon, level), _residual_sigma(np.array(errors)))


class ExponentialSmoothingForecaster:
    name = "exponential_smoothing"
    label = "Simple exponential smoothing"
    _ALPHAS = np.linspace(0.05, 0.95, 19)

    def forecast(self, history: np.ndarray, horizon: int) -> ForecastBand:
        best_alpha, best_sse = 0.3, math.inf
        for alpha in self._ALPHAS:
            sse = float(np.sum(self._one_step_errors(history, alpha) ** 2))
            if sse < best_sse:
                best_alpha, best_sse = float(alpha), sse
        level = self._final_level(history, best_alpha)
        return _band(np.full(horizon, level), _residual_sigma(self._one_step_errors(history, best_alpha)))

    @staticmethod
    def _one_step_errors(history: np.ndarray, alpha: float) -> np.ndarray:
        level = float(history[0])
        errors = np.empty(len(history) - 1)
        for t in range(1, len(history)):
            errors[t - 1] = history[t] - level
            level = alpha * history[t] + (1.0 - alpha) * level
        return errors

    @staticmethod
    def _final_level(history: np.ndarray, alpha: float) -> float:
        level = float(history[0])
        for value in history[1:]:
            level = alpha * float(value) + (1.0 - alpha) * level
        return level


class HoltWintersForecaster:
    name = "holt_winters"
    label = "Holt-Winters (weekly seasonality)"

    def forecast(self, history: np.ndarray, horizon: int) -> ForecastBand:
        if not HAS_STATSMODELS:
            raise RuntimeError("statsmodels is not installed")
        with warnings.catch_warnings():
            # Convergence and boundary warnings are routine for noisy demand and are
            # handled by the backtest, which discards a model that fits badly.
            warnings.simplefilter("ignore")
            model = ExponentialSmoothing(
                history,
                trend="add",
                damped_trend=True,
                seasonal="add",
                seasonal_periods=SEASONAL_PERIOD,
                initialization_method="estimated",
            ).fit()
            mean = np.asarray(model.forecast(horizon), dtype=float)
            sigma = _residual_sigma(np.asarray(model.resid, dtype=float))
        return _band(mean, sigma)


@dataclass(frozen=True)
class BacktestResult:
    name: str
    mae: float
    # Mean absolute percentage error over days with sales; None when every actual is zero.
    mape: float | None


@dataclass(frozen=True)
class ForecastSelection:
    model_used: str
    model_label: str
    reason: str
    band: ForecastBand
    history_length: int
    holdout_days: int | None
    selected_backtest: BacktestResult | None
    baseline_backtest: BacktestResult | None
    candidates: list[BacktestResult] = field(default_factory=list)


def backtest(forecaster: Forecaster, series: np.ndarray, holdout: int) -> BacktestResult:
    """Fit on everything but the last `holdout` days, then score the forecast of those days."""
    train, actual = series[:-holdout], series[-holdout:]
    predicted = forecaster.forecast(train, holdout).mean
    errors = np.abs(actual - predicted)
    positive = actual > 0
    mape = float(np.mean(errors[positive] / actual[positive])) if positive.any() else None
    return BacktestResult(forecaster.name, float(np.mean(errors)), mape)


def _trim_leading_zeros(series: np.ndarray) -> np.ndarray:
    """A product added mid-window would otherwise look like months of zero demand."""
    nonzero = np.flatnonzero(series > 0)
    return series[nonzero[0]:] if nonzero.size else series[:0]


def _describe_gain(candidate: BacktestResult, baseline: BacktestResult, holdout: int) -> str:
    gain = (baseline.mae - candidate.mae) / baseline.mae * 100 if baseline.mae > 0 else 0.0
    return (
        f"backtest MAE {candidate.mae:.2f} vs {baseline.mae:.2f} for the moving-average baseline "
        f"({gain:.0f}% better) over the last {holdout} days"
    )


def select_and_forecast(
    daily_series: np.ndarray, horizon: int, holdout_days: int = 14
) -> ForecastSelection:
    """Pick the forecaster that backtests best, falling back to the baseline when unsure."""
    horizon = max(1, horizon)
    baseline = MovingAverageForecaster()
    series = _trim_leading_zeros(np.asarray(daily_series, dtype=float))
    n = len(series)

    if n == 0:
        return ForecastSelection(
            baseline.name, baseline.label, "No sales in the history window, so zero demand is forecast.",
            baseline.forecast(series, horizon), 0, None, None, None,
        )
    if n < MIN_HISTORY_FOR_MODELS:
        return ForecastSelection(
            baseline.name, baseline.label,
            f"Only {n} days of sales history (need {MIN_HISTORY_FOR_MODELS} for a statistical model), so the moving-average baseline is used.",
            baseline.forecast(series, horizon), n, None, None, None,
        )

    holdout = max(7, min(holdout_days, n // 4))
    baseline_result = backtest(baseline, series, holdout)

    candidates: list[Forecaster] = [ExponentialSmoothingForecaster()]
    if HAS_STATSMODELS:
        candidates.append(HoltWintersForecaster())

    scored: list[tuple[Forecaster, BacktestResult]] = []
    for candidate in candidates:
        try:
            scored.append((candidate, backtest(candidate, series, holdout)))
        except Exception:
            # A model that cannot be fitted for this series is simply not a candidate.
            logger.warning("Forecaster %s failed to backtest", candidate.name, exc_info=True)

    results = [baseline_result] + [result for _, result in scored]
    best = min(scored, key=lambda pair: pair[1].mae, default=None)

    if best is not None and best[1].mae <= baseline_result.mae * (1.0 - MIN_IMPROVEMENT):
        forecaster, result = best
        try:
            band = forecaster.forecast(series, horizon)
            return ForecastSelection(
                forecaster.name, forecaster.label,
                f"{forecaster.label} selected: {_describe_gain(result, baseline_result, holdout)}.",
                band, n, holdout, result, baseline_result, results,
            )
        except Exception:
            logger.warning("Final fit of %s failed; using baseline", forecaster.name, exc_info=True)

    if best is None:
        why = "no statistical model could be fitted"
    else:
        why = (
            f"best alternative ({best[0].label}) had backtest MAE {best[1].mae:.2f} against "
            f"{baseline_result.mae:.2f} for the baseline, not a clear enough improvement"
        )
    return ForecastSelection(
        baseline.name, baseline.label, f"Moving-average baseline kept: {why}.",
        baseline.forecast(series, horizon), n, holdout, baseline_result, baseline_result, results,
    )
