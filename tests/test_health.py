from fastapi.testclient import TestClient
from main import app
from api.dependencies import get_db

client = TestClient(app)

def test_health_check_returns_200():
    """
    Test that /health returns 200 indicating liveness.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_readiness_check_returns_200_when_db_up(db_session):
    """
    Test that /ready returns 200 when the DB is reachable.
    """
    # Override dependency to use our active test DB session
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
    finally:
        app.dependency_overrides.clear()

def test_readiness_check_returns_503_when_db_down(db_session):
    """
    Test that /ready returns 503 when the DB is unavailable.
    """
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise Exception("Simulated connection failure")
        def close(self):
            pass

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    try:
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json() == {
            "status": "unavailable",
            "details": "Simulated connection failure"
        }
    finally:
        app.dependency_overrides.clear()
