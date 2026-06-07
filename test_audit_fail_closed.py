import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Assuming orchestrator.py is in the same directory or Python path
from orchestrator import app, get_audit_publisher, get_db_session, KafkaAuditPublisher, DatabaseSession

# Mock Payload matching the AssessmentRequest schema
VALID_PAYLOAD = {
    "applicant": {
        "first_name": "Chaos",
        "last_name": "Test",
        "email": "chaos@example.com",
        "tax_id": "HASHED_SSN_123"
    },
    "financial_features": {
        "cibil_score": 750,
        "net_monthly_income": 85000.50,
        "age": 35,
        "time_with_curr_empr": 48,
        "education": "GRADUATE"
    }
}

class MockBrokenKafkaPublisher(KafkaAuditPublisher):
    async def publish(self, event):
        """Simulate a hard network partition or broker timeout."""
        raise TimeoutError("Kafka broker unreachable - TimeoutException")

class MockTrackingDatabaseSession(DatabaseSession):
    def __init__(self):
        self.rolled_back = False
        self.committed = False
        self.persisted_records = []

    async def begin(self):
        self.rolled_back = False
        self.committed = False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True
        self.persisted_records.clear() # Simulate rollback

    async def add(self, obj):
        self.persisted_records.append(obj)

@pytest.fixture
def mock_db_session():
    return MockTrackingDatabaseSession()

@pytest.fixture
def test_client(mock_db_session):
    # Override FastAPI dependencies for the chaos test
    app.dependency_overrides[get_audit_publisher] = lambda: MockBrokenKafkaPublisher()
    app.dependency_overrides[get_db_session] = lambda: mock_db_session
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()


def test_chaos_audit_partition(test_client, mock_db_session):
    """
    Validates that the Orchestrator DAG fails closed and rolls back transactions
    if the Audit Ledger is unreachable.
    """
    # 1. Fire the assessment request
    response = test_client.post("/v1/assess", json=VALID_PAYLOAD)

    # 2. Verify API returns 500
    assert response.status_code == 500, f"Expected 500 Fail-Closed, got {response.status_code}"
    
    # Ensure no underwriting decision leaked in the response
    data = response.json()
    assert "APPROVED" not in str(data)
    assert "REJECTED" not in str(data)
    assert data.get("detail") == "System timeout. No underwriting decision was made. Please try again."

    # 3. Verify transaction rollback
    assert mock_db_session.rolled_back is True, "Database transaction was NOT rolled back."
    assert mock_db_session.committed is False, "Database transaction was erroneously committed."
    
    # 4. Verify no assessment results persisted
    # In a real integration test against a DB, we would query the tables.
    # Here, we assert the mocked tracking session cleared its persisted records.
    assert len(mock_db_session.persisted_records) == 0, "Partial records leaked into the database during a failed audit."
    
    # Note on FAILED_PROCESSING:
    # In a full saga pattern, a compensating transaction would run here to update the DB status.
    # The rollback assertion proves we did not persist un-audited decisions.
