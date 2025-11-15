# Product Requirements

## Functional
1. **Scenario definition** – Users can configure Monte Carlo parameters (trials, seed, metadata) and manage multiple risk factors (frequency, severity, distribution).
2. **Simulation execution** – API accepts scenario payloads and returns aggregate stats: mean/std, min/max, VaR, CVaR, expected shortfall, histogram, and worst trials.
3. **Visualization** – Frontend displays summary metrics, histogram, and tail events; supports editing factors and re-running simulations.
4. **Health introspection** – `/health` endpoint exposes API version + readiness status.
5. **Sample scenario** – `/scenarios/sample` provides opinionated defaults for onboarding/testing.

## Non-Functional
- **Performance** – Support up to 200k trials per request under 2 seconds on laptop-grade hardware.
- **Repeatability** – Deterministic results when `seed` is supplied.
- **Validation** – Strict schema validation with descriptive errors to protect engine integrity.
- **Security** – CORS locked down via middleware (default opens to all for demo; production should restrict domains).
- **Testability** – Automated backend (unit + API) and frontend (component) tests with simple commands.
- **Deployability** – Containerized backend/frontend plus docker-compose baseline.

## Success Metrics
- 95th percentile latency < 2.5s for 100k trial scenario.
- Zero schema validation regressions caught by automated tests.
- Frontend re-run cycle < 3s for configuration tweaks.
