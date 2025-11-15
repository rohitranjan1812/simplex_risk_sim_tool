import { ChangeEvent } from "react";
import type { LossDistribution, SimulationRequest } from "../types";

interface Props {
  value: SimulationRequest | null;
  disabled?: boolean;
  onChange: (next: SimulationRequest) => void;
  onSubmit: () => void;
}

const distributions: LossDistribution[] = ["normal", "lognormal", "pareto"];

export const SimulationForm = ({ value, disabled, onChange, onSubmit }: Props) => {
  if (!value) {
    return <div className="card">Loading scenario…</div>;
  }

  const updateField = (field: keyof SimulationRequest, newValue: unknown) => {
    onChange({ ...value, [field]: newValue });
  };

  const updateMeta = (field: keyof SimulationRequest["meta"], newValue: unknown) => {
    updateField("meta", { ...value.meta, [field]: newValue });
  };

  const handleFactorChange = (
    idx: number,
    field: keyof SimulationRequest["factors"][number],
    newValue: unknown
  ) => {
    const next = value.factors.map((factor, factorIdx) =>
      factorIdx === idx ? { ...factor, [field]: newValue } : factor
    );
    updateField("factors", next);
  };

  const addFactor = () => {
    const next = {
      name: `Factor ${value.factors.length + 1}`,
      frequency: 0.2,
      severity_mean: 100_000,
      severity_std: 50_000,
      distribution: "normal" as LossDistribution,
      correlation: 0,
    };
    updateField("factors", [...value.factors, next]);
  };

  const removeFactor = (idx: number) => {
    const next = value.factors.filter((_, factorIdx) => factorIdx !== idx);
    updateField("factors", next);
  };

  const handleNumberChange = (
    event: ChangeEvent<HTMLInputElement>,
    handler: (value: number) => void
  ) => {
    handler(Number(event.target.value));
  };

  return (
    <div className="card">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit();
        }}
      >
        <div className="grid" style={{ gap: "1rem" }}>
          <label>
            Trials
            <input
              type="number"
              min={100}
              max={500000}
              value={value.trials}
              onChange={(event) => handleNumberChange(event, (num) => updateField("trials", num))}
              disabled={disabled}
            />
          </label>
          <label>
            Seed
            <input
              type="number"
              value={value.seed ?? ""}
              placeholder="Optional"
              onChange={(event) => updateField("seed", event.target.value ? Number(event.target.value) : undefined)}
              disabled={disabled}
            />
          </label>
          <label>
            Portfolio Value
            <input
              type="number"
              min={0}
              value={value.meta.portfolio_value}
              onChange={(event) => handleNumberChange(event, (num) => updateMeta("portfolio_value", num))}
              disabled={disabled}
            />
          </label>
          <label>
            Horizon (months)
            <input
              type="number"
              min={1}
              max={60}
              value={value.meta.horizon_months}
              onChange={(event) => handleNumberChange(event, (num) => updateMeta("horizon_months", num))}
              disabled={disabled}
            />
          </label>
          <label>
            Scenario label
            <input
              type="text"
              value={value.meta.label}
              onChange={(event) => updateMeta("label", event.target.value)}
              disabled={disabled}
            />
          </label>
        </div>

        <h3>Risk Factors</h3>
        <div className="grid" style={{ gap: "1rem" }}>
          {value.factors.map((factor, idx) => (
            <div key={factor.name + idx} className="card" style={{ border: "1px solid #e2e8f0" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{factor.name}</strong>
                <button type="button" onClick={() => removeFactor(idx)} disabled={disabled || value.factors.length <= 1}>
                  Remove
                </button>
              </div>
              <label>
                Name
                <input
                  type="text"
                  value={factor.name}
                  onChange={(event) => handleFactorChange(idx, "name", event.target.value)}
                  disabled={disabled}
                />
              </label>
              <label>
                Frequency
                <input
                  type="number"
                  min={0}
                  step={0.1}
                  value={factor.frequency}
                  onChange={(event) => handleFactorChange(idx, "frequency", Number(event.target.value))}
                  disabled={disabled}
                />
              </label>
              <label>
                Severity Mean
                <input
                  type="number"
                  min={0}
                  value={factor.severity_mean}
                  onChange={(event) => handleFactorChange(idx, "severity_mean", Number(event.target.value))}
                  disabled={disabled}
                />
              </label>
              <label>
                Severity Std Dev
                <input
                  type="number"
                  min={0}
                  value={factor.severity_std}
                  onChange={(event) => handleFactorChange(idx, "severity_std", Number(event.target.value))}
                  disabled={disabled}
                />
              </label>
              <label>
                Distribution
                <select
                  value={factor.distribution}
                  onChange={(event) => handleFactorChange(idx, "distribution", event.target.value as LossDistribution)}
                  disabled={disabled}
                >
                  {distributions.map((distribution) => (
                    <option key={distribution} value={distribution}>
                      {distribution}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ))}
        </div>
        <div style={{ marginTop: "1rem", display: "flex", gap: "0.75rem" }}>
          <button type="button" onClick={addFactor} disabled={disabled}>
            Add factor
          </button>
          <button type="submit" disabled={disabled}>
            Run simulation
          </button>
        </div>
      </form>
    </div>
  );
};
