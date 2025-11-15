import type { SimulationResult } from "../types";

interface Props {
  result: SimulationResult;
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);

export const MetricsCards = ({ result }: Props) => {
  const cards = [
    { label: "Expected loss", value: formatCurrency(result.mean_loss) },
    { label: "Loss volatility", value: formatCurrency(result.loss_std) },
    { label: "VaR 95%", value: formatCurrency(result.var[0]?.value ?? 0) },
    { label: "CVaR 95%", value: formatCurrency(result.cvar[0]?.value ?? 0) },
    { label: "Expected shortfall", value: formatCurrency(result.expected_shortfall) },
    {
      label: "Prob. of loss",
      value: `${(result.probability_of_loss * 100).toFixed(1)}%`,
    },
  ];

  return (
    <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
      {cards.map((card) => (
        <div key={card.label} className="card">
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#64748b" }}>{card.label}</p>
          <strong style={{ fontSize: "1.5rem" }}>{card.value}</strong>
        </div>
      ))}
    </div>
  );
};
