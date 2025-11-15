"""FastAPI entrypoint for the risk simulation service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .sample_data import sample_request
from .schemas import HealthResponse, SimulationRequest, SimulationResult
from .simulation import run_simulation

app = FastAPI(title="Risk Simulation API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    return HealthResponse(api_version=app.version, status="ok")


@app.post("/simulate", response_model=SimulationResult, tags=["simulation"])
def simulate(payload: SimulationRequest) -> SimulationResult:
    return run_simulation(payload)


@app.get("/scenarios/sample", response_model=SimulationRequest, tags=["simulation"])
def get_sample_scenario() -> SimulationRequest:
    return sample_request()
