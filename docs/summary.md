# Risk Simulation Platform – Lean Brief

## What it does
- Configurable Monte Carlo engine models correlated operational risk via FastAPI.
- React dashboard edits scenarios, launches simulations, and visualizes loss exposure.
- Ships with container + test scripts for reproducible demos.

## Why it matters
- Replaces spreadsheet-only risk reviews with auditable, repeatable simulations.
- Quantifies tail risk (VaR/CVaR) and surfacing worst-case trials for quick narrative.

## How to run
```bash
# API
cd backend && uvicorn app.main:app --reload
# UI
cd frontend && npm install && npm run dev
# Docker
cd .. && docker compose up --build
```

## Confidence
- Backend pytest suite (5 tests) covers engine + API contract.
- Frontend Vitest suite validates core form interactions.
- Deterministic RNG via optional seeds ensures scenario reproducibility.
