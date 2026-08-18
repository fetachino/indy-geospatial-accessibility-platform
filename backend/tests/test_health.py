"""Smoke tests for the API foundation."""

from fastapi.testclient import TestClient

from indy_accessibility_api.main import app


def test_health_check_reports_service_status() -> None:
    """The health endpoint exposes a stable, typed readiness response."""
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "indy-geospatial-accessibility-api",
    }
