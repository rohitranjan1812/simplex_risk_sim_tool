import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";
import type { HistogramBucket } from "../types";

interface Props {
  data: HistogramBucket[];
}

export const HistogramChart = ({ data }: Props) => {
  const chartData = data.map((bucket) => ({
    midpoint: (bucket.start + bucket.end) / 2,
    probability: bucket.probability,
  }));

  return (
    <div className="card" style={{ minHeight: 320 }}>
      <h3>Loss distribution</h3>
      {chartData.length === 0 ? (
        <p>No simulation results yet.</p>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={chartData}>
            <XAxis dataKey="midpoint" tickFormatter={(value) => `$${(value / 1_000_000).toFixed(1)}M`} />
            <YAxis tickFormatter={(value) => `${(value * 100).toFixed(1)}%`} />
            <Tooltip
              formatter={(value: number) => `${(value * 100).toFixed(2)}%`}
              labelFormatter={(label: number) => `$${label.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
            />
            <Area type="monotone" dataKey="probability" stroke="#2563eb" fill="#3b82f622" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
