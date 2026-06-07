# RiskIntel API Contracts Specification

**Role:** Principal API Architect  
**Status:** FROZEN  
**Standard:** OpenAPI 3.0 Compatible  

## 1. Overview
This document represents the immutable, frozen API contracts for the RiskIntel platform. These contracts enforce strict backwards compatibility. Any future extensions must be purely additive; no breaking changes are permitted to the v1 specification. The API embeds comprehensive audit, lineage, and versioning metadata natively into the response headers and payloads to ensure instantaneous regulatory traceability.

### Global Headers
All endpoints support and return the following global headers:
*   `X-Correlation-ID`: Unique UUID tracking the request across the Orchestrator DAG.
*   `X-Timestamp`: ISO 8601 UTC timestamp of request completion.

---

## 2. API Endpoints

### 2.1. `POST /v1/assess`
**Description:** The primary ingestion endpoint. It accepts applicant financial features and executes the RiskIntel DAG (E1 Eligibility -> E2 Tiering -> E3 Archetype -> E4 Limit -> E5 Readiness).

**Request Schema (`application/json`)**
```json
{
  "applicant": {
    "applicant_id": "string (uuid)",
    "tax_id_hash": "string (sha256)",
    "first_name": "string",
    "last_name": "string",
    "email": "string (email)"
  },
  "financial_features": {
    "cibil_score": "integer (300-900)",
    "net_monthly_income": "number (>0)",
    "age": "integer (18-100)",
    "time_with_curr_empr": "integer (>=0)",
    "education": "string (enum: OTHERS, SSC, 10TH, 12TH, UNDER GRADUATE, GRADUATE, POST-GRADUATE, PROFESSIONAL)"
  }
}
```

**Validation Rules:**
*   `cibil_score` must be between 300 and 900.
*   `net_monthly_income` must be positive.
*   `age` must be >= 18.
*   `education` must rigidly match the defined enum strings.

**Response Schema (`application/json`)**
*The response payload structure depends on whether the applicant passes or fails the deterministic E1 gating rule.*

**Success Response (200 OK) - Person A Flow (Approved)**
```json
{
  "assessment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "APPROVED",
  "decision_summary": {
    "eligibility": "PASS",
    "risk_tier": "P2",
    "archetype": "Mid-Career Established",
    "credit_limit": 125000.00,
    "readiness": "READY"
  },
  "improvement_actions": [
    "Maintain current credit utilization to achieve P1 risk tier."
  ],
  "audit_metadata": {
    "correlation_id": "c9x8y7z6-5432-1098-hgfe-dcba09876543",
    "execution_time_ms": 142
  },
  "lineage_metadata": {
    "e1_rule_version": "v1.0.2",
    "e2_rule_version": "v1.1.0",
    "e3_model_id": "m-883a-kmns-v2.1",
    "e4_model_id": "m-994b-recs-v1.8",
    "e5_rule_version": "v1.0.0"
  }
}
```

**Success Response (200 OK) - Person B Flow (Rejected by E1)**
```json
{
  "assessment_id": "d4c3b2a1-0987-65e4-dcba-0987654321fe",
  "status": "REJECTED",
  "rejection_reason": "Applicant credit score (620) is below the minimum required threshold.",
  "decision_summary": {
    "eligibility": "FAIL"
  },
  "audit_metadata": {
    "correlation_id": "x1y2z3a4-b5c6-d7e8-f9g0-h1i2j3k4l5m6",
    "execution_time_ms": 24
  },
  "lineage_metadata": {
    "e1_rule_version": "v1.0.2",
    "e2_rule_version": null,
    "e3_model_id": null,
    "e4_model_id": null,
    "e5_rule_version": null
  }
}
```

**Error Codes:**
*   **400 Bad Request:** Validation failure on the JSON payload (e.g., negative age, invalid enum).
*   **401 Unauthorized:** Invalid or missing API key.
*   **422 Unprocessable Entity:** Payload is valid JSON but violates logical business constraints.
*   **500 Internal Server Error:** Orchestrator DAG failure or database timeout.

---

### 2.2. `GET /v1/health/live`
**Description:** Liveness probe. Confirms the API server process is running and accepting connections. Used by Kubernetes/Load Balancers to determine if a pod should be restarted.

**Response Schema (200 OK)**
```json
{
  "status": "up",
  "timestamp": "2026-06-05T22:50:00Z"
}
```

---

### 2.3. `GET /v1/health/ready`
**Description:** Readiness probe. Confirms that all necessary critical downstream dependencies (e.g., PostgreSQL, Redis, Rule Registry) are reachable. Used by Kubernetes to determine if traffic should be routed to this pod.

**Response Schema (200 OK)**
```json
{
  "status": "ready",
  "dependencies": {
    "database": "connected",
    "rule_registry": "accessible"
  }
}
```
*If any critical dependency fails, returns 503 Service Unavailable.*

---

### 2.4. `GET /v1/health/deep`
**Description:** Deep diagnostic probe. Intended for internal monitoring tools (e.g., Datadog, Prometheus). Validates the specific load status of the ML models in the Inference Service and verifies message broker connection for the Audit ledger.

**Response Schema (200 OK)**
```json
{
  "status": "healthy",
  "metrics": {
    "database_latency_ms": 4.2,
    "kafka_broker_status": "connected",
    "loaded_models": [
      {
        "engine": "E3",
        "model_id": "m-883a-kmns-v2.1",
        "status": "loaded_in_memory"
      },
      {
        "engine": "E4",
        "model_id": "m-994b-recs-v1.8",
        "status": "loaded_in_memory"
      }
    ],
    "active_rules": {
      "e1_eligibility": "v1.0.2",
      "e2_tiering": "v1.1.0",
      "e5_readiness": "v1.0.0"
    }
  }
}
```

---

## 3. Lineage and Versioning Compliance
To satisfy FCRA and ECOA regulations, the `lineage_metadata` block is injected into every `POST /v1/assess` response.
*   **Rule Versioning (`e1_rule_version`):** Maps to the exact `rule_id` in the `rule_registry` table, guaranteeing traceability to the specific configuration payload (e.g., `{"cibil_threshold": 650}`) active at the millisecond of assessment.
*   **Model Versioning (`e3_model_id`):** Maps to the exact `model_id` in the `model_registry` table, tracking the exact S3 artifact (Pickle file) and training data hash used for that specific prediction.
*   **Audit Correlation (`correlation_id`):** This UUID allows compliance teams to instantly query the immutable `audit_log` database table to reconstruct the entire orchestration trace for adverse action defense.
