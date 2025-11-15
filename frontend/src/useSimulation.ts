import { useCallback, useEffect, useState } from "react";
import { fetchSampleScenario, runSimulation } from "./api";
import type { SimulationRequest, SimulationResult } from "./types";

interface SimulationState {
  loading: boolean;
  error: string | null;
  request: SimulationRequest | null;
  result: SimulationResult | null;
}

export const useSimulation = () => {
  const [state, setState] = useState<SimulationState>({
    loading: true,
    error: null,
    request: null,
    result: null,
  });

  useEffect(() => {
    fetchSampleScenario()
      .then((request) => setState((old) => ({ ...old, request, loading: false })))
      .catch((error) =>
        setState((old) => ({
          ...old,
          loading: false,
          error: error instanceof Error ? error.message : "Unable to load scenario",
        }))
      );
  }, []);

  const simulate = useCallback(async (payload: SimulationRequest) => {
    setState((old) => ({ ...old, loading: true, error: null }));
    try {
      const result = await runSimulation(payload);
      setState({ loading: false, error: null, request: payload, result });
    } catch (error) {
      setState((old) => ({
        ...old,
        loading: false,
        error: error instanceof Error ? error.message : "Simulation failed",
      }));
    }
  }, []);

  return {
    ...state,
    simulate,
  };
};
