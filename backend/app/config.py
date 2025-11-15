"""Application configuration helpers."""
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Typed configuration for simulation defaults."""

    max_trials: int = Field(200_000, description="Upper bound for allowed Monte Carlo trials.")
    default_trials: int = 10_000
    confidence_levels: tuple[float, float] = (0.95, 0.99)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()
