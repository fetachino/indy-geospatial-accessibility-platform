"""FastAPI application entry point."""

from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Stable response returned by the service health check."""

    status: Literal["ok"]
    service: str


app = FastAPI(
    title="Indy Geospatial Accessibility API",
    summary="API foundation for Marion County accessibility indicators.",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health_check() -> HealthResponse:
    """Report that the API process is ready to accept requests."""
    return HealthResponse(
        status="ok",
        service="indy-geospatial-accessibility-api",
    )
