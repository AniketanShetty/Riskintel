# RiskIntel Definitive API Contracts

**Role:** Lead API Architect  
**Status:** FROZEN FOR IMPLEMENTATION  
**Standard:** OpenAPI 3.0 Compatible  

## Global Headers
All API responses will include:
*   `X-Correlation-ID`: UUID for tracking the request across microservices and audit logs.
*   `X-Timestamp`: ISO 8601 UTC execution timestamp.

---

## 1. Assessments API

### 1.1 Create Assessment
`POST /v1/assess`

Executes the RiskIntel Orchestrator DAG (E1 -> E2 -> E3 -> E4 -> E5).

**Request Schema (`application/json`)**
```json
{
  "applicant": {
    "first_name": "string (min 1)",
    "last_name": "string (min 1)",
    "email": "string (email)",
    "tax_id": "string (SSN/PAN - will be hashed at gateway)"
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
*   `tax_id` must not be logged or persisted in plaintext. It must be hashed before passing to Orchestrator.
*   Enums are strictly evaluated.

**Success Response (Person A - Approved) - `200 OK`**
```json
{
  "assessment_id": "uuid",
  "status": "APPROVED",
  "decision_summary": {
    "eligibility": "PASS",
    "risk_tier": "P2",
    "archetype": "Mid-Career Established",
    "credit_limit": 125000.00,
    "readiness": "READY"
  },
  "lineage_metadata": {
    "e1_rule_version": "v1.0",
    "e3_model_id": "m-883a-kmns-v2.1"
  }
}
```

**Success Response (Person B - Rejected) - `200 OK`**
```json
{
  "assessment_id": "uuid",
  "status": "REJECTED",
  "rejection_reason": "Applicant credit score is below the minimum required threshold.",
  "decision_summary": {
    "eligibility": "FAIL"
  },
  "lineage_metadata": {
    "e1_rule_version": "v1.0"
  }
}
```

**Error Responses:**
*   `400 Bad Request`: JSON parsing error or missing fields.
*   `422 Unprocessable Entity`: Validation failure (e.g., `age` is -5).
*   `500 Internal Server Error`: Audit ledger timeout or Orchestrator crash.

---

### 1.2 Get Assessment by ID
`GET /v1/assessments/{id}`

Retrieves the historical results of a specific assessment. Used for displaying reports or for compliance auditing.

**Path Parameters:**
*   `id`: UUID of the assessment.

**Success Response - `200 OK`**
```json
{
  "assessment_id": "uuid",
  "applicant_id": "uuid",
  "status": "APPROVED",
  "executed_at": "2026-06-05T12:00:00Z",
  "input_features": { ... },
  "results": {
    "eligibility": { "is_eligible": true, "rule_id": "uuid" },
    "risk_tier": { "assigned_tier": "P2", "rule_id": "uuid" },
    "archetype": { "archetype_label": "Mid-Career Established", "model_id": "uuid" },
    "recommendation": { "suggested_limit": 125000.00, "model_id": "uuid" }
  }
}
```

**Error Responses:**
*   `404 Not Found`: No assessment exists with the provided ID.

---

## 2. ML Reference APIs

### 2.1 List Active Archetypes
`GET /v1/archetypes`

Retrieves the list of currently active borrower archetypes produced by the E3 ML model. Used by the frontend to populate documentation or filtering dropdowns.

**Success Response - `200 OK`**
```json
{
  "model_id": "m-883a-kmns-v2.1",
  "active_archetypes": [
    {
      "label": "High-Income Established",
      "description": "Borrowers with long tenure and high capacity.",
      "centroid_coordinates": {"income": 1.5, "cibil": 0.8}
    },
    {
      "label": "Young Starters",
      "description": "Early career professionals with thin credit files.",
      "centroid_coordinates": {"income": -0.5, "cibil": -0.2}
    }
  ]
}
```

---

### 2.2 List Recommendation Bounds
`GET /v1/recommendations`

Retrieves the active credit limit bounds and improvement action strings associated with the E4 engine.

**Success Response - `200 OK`**
```json
{
  "model_id": "m-994b-recs-v1.8",
  "limit_ranges": {
    "P1": {"min": 100000, "max": 500000},
    "P2": {"min": 50000, "max": 150000}
  },
  "improvement_actions_dictionary": [
    "Decrease current credit utilization.",
    "Increase age of oldest active tradeline."
  ]
}
```

---

## 3. Kubernetes Health Probes

### 3.1 Liveness Probe
`GET /health/live`

Validates that the API Gateway and Orchestrator processes are running and can accept connections.

**Success Response - `200 OK`**
```json
{
  "status": "UP"
}
```

### 3.2 Readiness Probe
`GET /health/ready`

Validates that the service can successfully communicate with downstream dependencies. If this fails, Kubernetes stops routing traffic to the pod.

**Success Response - `200 OK`**
```json
{
  "status": "READY",
  "dependencies": {
    "postgresql": "CONNECTED",
    "kafka": "CONNECTED",
    "rules_engine": "HEALTHY",
    "ml_inference": "HEALTHY"
  }
}
```
**Error Responses:**
*   `503 Service Unavailable`: One or more dependencies are down. The body will specify which dependency failed.
