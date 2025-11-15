export type LossDistribution = "normal" | "lognormal" | "pareto";

export interface RiskFactor {
  name: string;
  frequency: number;
  severity_mean: number;
  severity_std: number;
  distribution: LossDistribution;
  correlation?: number;
}

export interface ScenarioMeta {
  portfolio_value: number;
  horizon_months: number;
  label: string;
}

export interface SimulationRequest {
  trials: number;
  seed?: number;
  meta: ScenarioMeta;
  factors: RiskFactor[];
}

export interface PercentilePoint {
  level: number;
  value: number;
}

export interface HistogramBucket {
  start: number;
  end: number;
  probability: number;
}

export interface SimulationResult {
  mean_loss: number;
  loss_std: number;
  loss_min: number;
  loss_max: number;
  var: PercentilePoint[];
  cvar: PercentilePoint[];
  histogram: HistogramBucket[];
  worst_trials: number[];
  expected_shortfall: number;
  probability_of_loss: number;
  metadata: ScenarioMeta;
}
