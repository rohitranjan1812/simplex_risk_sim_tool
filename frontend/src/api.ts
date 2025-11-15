import axios from "axios";
import { z } from "zod";
import type { SimulationRequest, SimulationResult } from "./types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  timeout: 15_000,
});

const simulationResultSchema = z.object({
  mean_loss: z.number(),
  loss_std: z.number(),
  loss_min: z.number(),
  loss_max: z.number(),
  var: z.array(z.object({ level: z.number(), value: z.number() })),
  cvar: z.array(z.object({ level: z.number(), value: z.number() })),
  histogram: z.array(z.object({ start: z.number(), end: z.number(), probability: z.number() })),
  worst_trials: z.array(z.number()),
  expected_shortfall: z.number(),
  probability_of_loss: z.number(),
  metadata: z.object({
    portfolio_value: z.number(),
    horizon_months: z.number(),
    label: z.string(),
  }),
});

export const fetchSampleScenario = async (): Promise<SimulationRequest> => {
  const { data } = await api.get<SimulationRequest>("/scenarios/sample");
  return data;
};

export const runSimulation = async (
  payload: SimulationRequest
): Promise<SimulationResult> => {
  const { data } = await api.post<SimulationResult>("/simulate", payload);
  return simulationResultSchema.parse(data);
};
