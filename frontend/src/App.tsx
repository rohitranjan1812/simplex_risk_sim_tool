import { useEffect, useMemo, useState } from "react";
import { SimulationForm } from "./components/SimulationForm";
import { ResultsPanel } from "./components/ResultsPanel";
import { useSimulation } from "./useSimulation";
import type { SimulationRequest } from "./types";

const App = () => {
  const { loading, error, request, result, simulate } = useSimulation();
  const [formState, setFormState] = useState<SimulationRequest | null>(null);

  useEffect(() => {
    if (request) {
      setFormState(request);
    }
  }, [request]);

  const canSubmit = useMemo(() => {
    if (!formState) return false;
    return formState.factors.length > 0 && formState.trials >= 100;
  }, [formState]);

  return (
    <div className="app-shell">
      <header style={{ marginBottom: "1.5rem" }}>
        <h1>Risk Simulation Workbench</h1>
        <p>Configure Monte Carlo scenarios, run simulations, and visualize loss distributions.</p>
        <small>version {typeof __APP_VERSION__ !== "undefined" ? __APP_VERSION__ : "dev"}</small>
      </header>
      {error && (
        <div className="card" style={{ border: "1px solid #ef4444", color: "#b91c1c" }}>
          {error}
        </div>
      )}
      <div className="layout">
        <SimulationForm
          value={formState}
          disabled={loading || !formState}
          onChange={(next) => setFormState(next)}
          onSubmit={() => formState && canSubmit && simulate(formState)}
        />
        <ResultsPanel result={result} loading={loading} />
      </div>
    </div>
  );
};

export default App;
