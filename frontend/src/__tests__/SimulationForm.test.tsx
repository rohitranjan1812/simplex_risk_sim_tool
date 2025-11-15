import { fireEvent, render, screen } from "@testing-library/react";
import { SimulationForm } from "../components/SimulationForm";
import type { SimulationRequest } from "../types";

describe("SimulationForm", () => {
  const payload: SimulationRequest = {
    trials: 1000,
    seed: 1,
    meta: { portfolio_value: 1_000_000, horizon_months: 12, label: "Test" },
    factors: [
      {
        name: "Factor 1",
        frequency: 0.5,
        severity_mean: 100_000,
        severity_std: 50_000,
        distribution: "normal",
        correlation: 0,
      },
    ],
  };

  it("submits updated payload", () => {
    const handleChange = vi.fn();
    const handleSubmit = vi.fn();

    render(<SimulationForm value={payload} onChange={handleChange} onSubmit={handleSubmit} />);

    fireEvent.change(screen.getByLabelText(/Trials/i), { target: { value: "2000" } });
    expect(handleChange).toHaveBeenCalled();

    fireEvent.click(screen.getByText(/Run simulation/i));
    expect(handleSubmit).toHaveBeenCalled();
  });
});
