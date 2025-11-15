# Risk Simulation Platform – Detailed Implementation Guide

## 1. Architecture Overview
- **Backend (FastAPI)** – Provides REST endpoints (`/health`, `/simulate`, `/scenarios/sample`). Houses Monte Carlo engine built atop NumPy and Pydantic schemas.
- **Frontend (React + Vite)** – SPA delivering scenario authoring UI, simulation controls, visualization (Recharts) and results drill-down.
- **Transport** – JSON over HTTPS (or HTTP locally). CORS middleware currently allows `*` for ease of evaluation; tighten for production.
- **Containerization** – Separate Dockerfiles for API + UI, orchestrated by `docker-compose.yml`. Frontend build arg `VITE_API_URL` injects API base path at build time, while nginx reverse-proxies `/api/*` back to FastAPI when deployed via compose.

## 2. Backend Deep Dive
### 2.1 Schemas (`app/schemas.py`)
- Enumerated `LossDistribution` (normal, lognormal, pareto).
- `RiskFactor` enforces positive frequency/severity inputs plus optional correlation knob (future use for covariance modeling).
  - **New:** `is_cat_event` flag to identify catastrophic events for specialized metrics.
  - **New:** `geographic_zone` attribute for spatial exposure tracking.
- `ActuarialLayer` models insurance coverage with deductibles, limits, participation rates, and premium rates.
- `SimulationRequest` includes metadata + RNG seed, validated bounds (100–500k trials) to protect compute budgets.
  - **New:** `layers` field for actuarial layer definitions.
- Response objects capture histogram buckets, percentile stats, and scenario metadata enabling idempotent UI refresh with minimal recomputation.
  - **New:** Actuarial metrics (burning_cost, loss_ratio, layer_losses, net_retained_loss).
  - **New:** CAT metrics (oep_curve, aep_curve, pml_values, cat_event_count, geographic_exposure).

### 2.2 Engine (`app/simulation.py`)
1. **Distribution Sampling** – Severity draws per factor using NumPy RNG.
   - Normal: truncated at zero to avoid negative losses.
   - Lognormal: derive μ/σ from target mean/std via closed forms.
   - Pareto: heuristically derive α from coefficient of variation for heavy-tail modeling.
2. **Frequency Modeling** – Poisson arrivals per factor (λ = `frequency`). Each trial multiplies event counts * severity sample to accumulate losses.
3. **Aggregation** – After iterating factors, compute summary stats, histogram (density converted to bucket probabilities), and percentile metrics (`np.quantile`).
4. **Tail Metrics** – `worst_trials` sorts and surfaces top 10 losses; `expected_shortfall` averages losses above mean; `probability_of_loss` derived from positive-tail ratio.
5. **Determinism** – All runs rely on `np.random.default_rng(seed)` ensuring reproducibility when user provides a seed. Trials automatically capped by `Settings.max_trials`.
6. **Actuarial Layer Application** – Applies deductibles, limits, and participation rates to gross losses:
   - Excess = max(Loss - Deductible, 0)
   - Capped = min(Excess, Limit)
   - Layer Loss = Capped × Participation Rate
   - Net Retained = Gross Loss - Layer Loss
7. **CAT Metrics Calculation**:
   - **OEP/AEP Curves** – Exceedance probability curves at standard return periods (10, 25, 50, 100, 250, 500 years).
   - **PML** – Probable Maximum Loss at 100, 250, and 500-year return periods.
   - **Geographic Exposure** – Tracks losses by geographic zone for concentration risk analysis.
   - **Event Counting** – Counts catastrophic events across all trials.

### 2.3 API Layer (`app/main.py`)
- FastAPI routers annotate responses for auto-generated OpenAPI docs.
- `CORSMiddleware` currently unrestricted; adjust `allow_origins` before production hardening.
- Sample scenario helper ensures UX has default data without manual entry.

### 2.4 Testing (`tests/*.py`)
- `test_simulation.py` ensures positive losses, histogram creation, deterministic outputs given identical seeds.
- `test_api.py` uses FastAPI `TestClient` to validate endpoint contracts and sample scenario semantics.
- `test_actuarial.py` validates burning cost calculations, layer applications, coinsurance, and loss ratios.
- `test_cat.py` tests CAT event identification, OEP/AEP curves, PML calculations, and geographic exposure tracking.
- Pytest config sets `asyncio_mode=auto` and adds `app` to `PYTHONPATH` for direct imports.
- **Test Coverage**: 16 tests covering core simulation, API contracts, actuarial features, and CAT modeling.

## 3. Frontend Deep Dive
### 3.1 State + Hooks (`src/useSimulation.ts`)
- Manages async lifecycle: `loading`, `error`, `request`, `result`.
- Fetches sample scenario on mount, handles optimistic state updates when running new simulations.

### 3.2 Components
- `SimulationForm` – Controlled inputs for scenario meta + dynamic risk factors. Supports add/remove, number coercion, and seed editing. Buttons disable while running for idempotence.
- `ResultsPanel` – Composes `MetricsCards`, `HistogramChart`, and worst-trial list. Handles empty and loading states.
- `HistogramChart` – Recharts area chart; probability axis displays percent; tooltip clarifies bucket probability vs. currency axis.

### 3.3 API Client (`src/api.ts`)
- Axios instance targeting configurable `VITE_API_URL` (defaults to `http://localhost:8000`).
- Zod schema ensures runtime validation so UI fails fast if backend changes payload shape.

### 3.4 Styles
- Lightweight CSS grid / card primitives for responsive layout (two-column above 960px). No CSS frameworks to minimize dependencies.

### 3.5 Testing
- Vitest + Testing Library ensures `SimulationForm` emits change + submit events. `setupTests.ts` wires `jest-dom` for matcher ergonomics.

## 4. DevOps & Tooling
- **Python packaging** – `pyproject.toml` + `requirements.txt` keep FastAPI deps pinned; optional `dev` extra for pytest/httpx.
- **Node packaging** – `package.json` scripts for dev/build/test; TypeScript strict mode enforced via `tsconfig`.
- **Docker Compose** – Builds backend image, then frontend (passing API URL). Frontend container listens on 4173 externally and proxies `/api/*` requests to backend service, enabling single-host demos.
- **CI Hooks (future)** – Workflows can run `pytest` + `npm run test` + `npm run build` + `docker compose build` for regression gating.

## 5. Operational Guidance
- **Seed management** – Encourage analysts to save `seed` + scenario payload for reproducible findings.
- **Performance tuning** – Increase `Settings.max_trials` or adjust histogram buckets in `simulation.py` to match hardware budgets.
- **Security hardening** – Add AuthN (API keys/OAuth), enforce HTTPS, restrict CORS origins, and validate inputs against business limits.
- **Extensibility** – Replace Poisson arrival with user-selected distributions, plug covariance matrices for correlated factors, or connect persistence (Postgres) for scenario history.

## 6. Testing Evidence
- `pytest` run (16 tests) – PASS covering core simulation, API contracts, actuarial features, and CAT modeling.
- `vitest run` – PASS (1 component test) after installing jsdom, as recorded in terminal output.
- **Test Categories:**
  - Core simulation: 2 tests (determinism, positive losses)
  - API contracts: 3 tests (health, simulate, sample scenario)
  - Actuarial features: 5 tests (burning cost, layers, coinsurance, loss ratios)
  - CAT/accumulation: 6 tests (event identification, OEP/AEP, PML, geographic tracking)

## 7. Advanced Features
### 7.1 Actuarial Modeling
- **Insurance Layers** – Model deductibles, limits, and coinsurance with `ActuarialLayer` schema.
- **Burning Cost** – Automatic calculation of average annual loss rate as percentage of portfolio value.
- **Loss Ratios** – Compare actual losses to premiums for profitability analysis.
- **Net Retained Loss** – Track losses after applying insurance layers.
- See `docs/actuarial_cat_features.md` for detailed guide and examples.

### 7.2 CAT/Accumulation Analysis
- **Catastrophic Events** – Flag risk factors as CAT events with `is_cat_event` for specialized analysis.
- **Geographic Exposure** – Track losses by zone using `geographic_zone` attribute.
- **OEP/AEP Curves** – Occurrence and Aggregate Exceedance Probability at standard return periods.
- **PML Calculations** – Probable Maximum Loss at 100, 250, and 500-year return periods.
- **Event Counting** – Track frequency of catastrophic events across simulations.
- See `docs/actuarial_cat_features.md` for mathematical formulations and use cases.

## 8. Future Enhancements
1. **Batch simulations** – queue multiple scenarios and stream incremental percentiles via WebSockets.
2. **Report exports** – PDF/CSV summarizing VaR ladder + scenario metadata for risk committees.
3. **User management** – Role-based permissions with audit log of scenario changes.
4. **Scenario versioning** – Persist payloads + results for time-series analysis.
5. **Spatial Correlation** – Implement correlation matrices for geographic zones.
6. **Advanced Reinsurance** – Model quota share, surplus share, and stop-loss treaties.
7. **Parameter Uncertainty** – Add secondary uncertainty to distributions for robust risk estimates.
8. **Climate Trends** – Adjust CAT event frequencies and severities based on climate projections.
