# Risk Simulation Platform

Full-stack Monte Carlo workbench for modeling portfolio risk, running large simulations, and visualizing loss distributions.

## Stack
- **Backend:** FastAPI, NumPy, Pydantic.
- **Frontend:** React 18 + Vite + Recharts.
- **Testing:** Pytest + HTTPX; Vitest + Testing Library.

## Prerequisites
- Python 3.12 with virtualenv access.
- Node.js 20+ and npm.
- Docker (optional) for containerized runs.

## Local Development
### Backend
```bash
cd codex_test/risk-sim/backend
python -m venv .venv && source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd codex_test/risk-sim/frontend
npm install
npm run dev
```
Set `VITE_API_URL=http://localhost:8000` to proxy API requests during frontend dev.

## Testing
```bash
cd codex_test/risk-sim/backend && pytest
cd codex_test/risk-sim/frontend && npm run test
```

## Docker Compose
```bash
cd codex_test/risk-sim
docker compose up --build
```
Frontend becomes available on http://localhost:4173 and proxies `/api` calls to the backend.

## Documentation
- `docs/requirements.md` – functional + non-functional requirements.
- `docs/summary.md` – lean overview for exec consumption.
- `docs/implementation.md` – exhaustive deep dive of architecture, data flow, and test strategy.
- `docs/actuarial_cat_features.md` – advanced actuarial and CAT/accumulation features guide.

## Features
- **Monte Carlo Simulation** – Run thousands of trials to model portfolio risk and loss distributions.
- **Advanced Actuarial Modeling** – Insurance layers with deductibles, limits, coinsurance, premium rates, and loss ratios.
- **CAT/Accumulation Analysis** – Catastrophic event modeling with OEP/AEP curves, PML calculations, and geographic exposure tracking.
- **Risk Metrics** – VaR, CVaR, expected shortfall, burning cost, and probability distributions.
- **Interactive Visualization** – Real-time charts and metrics for risk assessment and decision-making.
