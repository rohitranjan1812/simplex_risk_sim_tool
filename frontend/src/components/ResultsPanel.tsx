import type { SimulationResult } from "../types";
import { HistogramChart } from "./HistogramChart";
import { MetricsCards } from "./MetricsCards";

interface Props {
  result: SimulationResult | null;
  loading: boolean;
}

export const ResultsPanel = ({ result, loading }: Props) => {
  if (loading && !result) {
    return <div className="card">Running simulation…</div>;
  }

  if (!result) {
    return <div className="card">Awaiting simulation results.</div>;
  }

  return (
    <div className="grid" style={{ gap: "1rem" }}>
      <MetricsCards result={result} />
      <HistogramChart data={result.histogram} />
      <div className="card">
        <h3>Worst trials</h3>
        <ol>
          {result.worst_trials.slice(0, 5).map((trial, idx) => (
            <li key={`${trial}-${idx}`}>
              ${trial.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
};
