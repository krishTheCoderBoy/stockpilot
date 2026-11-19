import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useReducedMotion } from "motion/react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Alert } from "../../components/ui/Alert";
import { Skeleton } from "../../components/ui/Skeleton";
import { extractErrorMessage, procurementApi } from "../../lib/api";
import { type ForecastResponse } from "../../lib/queries";

// Enough recent history to show the weekly pattern without squashing the forecast.
const HISTORY_DAYS_SHOWN = 60;

interface ChartPoint {
  date: string;
  history?: number;
  forecast?: number;
  band?: [number, number];
}

export function ForecastChart({ productId, warehouseId }: { productId: string; warehouseId: string | null }) {
  const reducedMotion = useReducedMotion();

  const { data, isLoading, isError, error } = useQuery<ForecastResponse>({
    queryKey: ["planning-forecast", productId, warehouseId],
    queryFn: async () =>
      (
        await procurementApi.get(`/planning/forecast/${productId}`, {
          params: warehouseId ? { warehouse_id: warehouseId } : undefined,
        })
      ).data,
    retry: false,
    staleTime: 5 * 60_000,
  });

  const points = useMemo<ChartPoint[]>(() => {
    if (!data) return [];
    const history: ChartPoint[] = data.history.slice(-HISTORY_DAYS_SHOWN).map((h) => ({
      date: h.bucket_start,
      history: Number(h.quantity),
    }));
    const forecast: ChartPoint[] = data.forecast.map((f) => ({
      date: f.bucket_start,
      forecast: Number(f.mean),
      band: [Number(f.lower), Number(f.upper)],
    }));
    // Join the two lines so the forecast visibly continues from the last actual day.
    if (history.length > 0 && forecast.length > 0) {
      history[history.length - 1] = { ...history[history.length - 1], forecast: history[history.length - 1].history };
    }
    return [...history, ...forecast];
  }, [data]);

  if (isLoading) return <Skeleton className="h-72 w-full" />;
  if (isError || !data) return <Alert tone="danger">{extractErrorMessage(error)}</Alert>;

  return (
    <div className="flex flex-col gap-4">
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={points}>
          <CartesianGrid stroke="#232838" strokeDasharray="3 3" />
          <XAxis dataKey="date" stroke="#8B93A7" fontSize={11} minTickGap={32} tickFormatter={(d: string) => d.slice(5)} />
          <YAxis stroke="#8B93A7" fontSize={12} />
          <RechartsTooltip
            contentStyle={{ backgroundColor: "#12161F", border: "1px solid #232838", borderRadius: 6, fontSize: 12 }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Area
            dataKey="band"
            name="80% range"
            stroke="none"
            fill="#4FB7B3"
            fillOpacity={0.15}
            isAnimationActive={!reducedMotion}
          />
          <Line
            type="monotone"
            dataKey="history"
            name="Actual demand"
            stroke="#D9A441"
            strokeWidth={2}
            dot={false}
            isAnimationActive={!reducedMotion}
          />
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast"
            stroke="#4FB7B3"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={false}
            isAnimationActive={!reducedMotion}
          />
        </ComposedChart>
      </ResponsiveContainer>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs sm:grid-cols-4">
        <div>
          <dt className="text-text-muted">Model used</dt>
          <dd className="text-text">{data.model_label}</dd>
        </div>
        <div>
          <dt className="text-text-muted">History used</dt>
          <dd className="font-mono text-text">{data.history_length} days</dd>
        </div>
        <div>
          <dt className="text-text-muted">Backtest error (MAE)</dt>
          <dd className="font-mono text-text">
            {data.backtest ? `${data.backtest.mae} (baseline ${data.backtest.baseline_mae})` : "n/a"}
          </dd>
        </div>
        <div>
          <dt className="text-text-muted">Next {data.horizon_days} days</dt>
          <dd className="font-mono text-text">
            {data.total_forecast_demand} ({data.total_lower}–{data.total_upper})
          </dd>
        </div>
      </dl>
      <p className="text-xs text-text-muted">{data.model_reason}</p>
    </div>
  );
}
