# k6 Load Test Implementation: DAG Execution

**Role:** Principal Performance Engineer  
**Target Function:** `load_test_dag_execution()`  
**Objective:** Validate that the Orchestrator DAG can sustain 100 Requests Per Second (RPS) and absorb a 500 RPS spike while maintaining a strict p95 latency of < 500ms.

---

## 1. Test Architecture & Data Preparation

### 1.1 Data Generation
Because the Orchestrator enforces unique `applicant_id` and hashed SSNs (`tax_id_hash`), we cannot replay the same static JSON payload.
*   **Implementation:** The k6 script must use the `k6/execution` context and the built-in `Math.random()` to dynamically generate UUIDs and unique applicant parameters for every iteration.
*   **Distribution:** 80% of payloads should be engineered to pass E1 (forcing the heavier ML inference paths), while 20% should be engineered to fail E1 (simulating fast-fail rejections).

### 1.2 Target Endpoint
`POST /v1/assess`

---

## 2. k6 Scenario Configuration

We will use k6's `ramping-arrival-rate` executor to precisely control RPS regardless of how long the backend takes to respond.

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

// Custom Metrics
const orchestratorLatency = new Trend('orchestrator_latency');
const errorRate = new Rate('error_rate');

export const options = {
  scenarios: {
    dag_execution: {
      executor: 'ramping-arrival-rate',
      startRate: 10, // Start at 10 RPS
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 1000,
      stages: [
        { duration: '2m', target: 100 }, // Ramp up to 100 RPS
        { duration: '10m', target: 100 }, // Sustain 100 RPS (Baseline)
        { duration: '30s', target: 500 }, // Spike to 500 RPS
        { duration: '30s', target: 500 }, // Hold Spike
        { duration: '1m', target: 100 },  // Recover to 100 RPS
        { duration: '2m', target: 0 },    // Ramp down
      ],
    },
  },
  thresholds: {
    'http_req_duration': ['p(95)<500'], // Global strict SLA
    'orchestrator_latency': ['p(95)<400'], // Core DAG execution time
    'error_rate': ['rate<0.001'], // < 0.1% errors allowed
  },
};
```

---

## 3. Metric Observability & Integration

k6 will measure the external HTTP boundaries, but we must correlate this with internal service metrics. The k6 test runner will push metrics to Datadog (or Prometheus/Grafana) via StatsD, allowing us to overlay k6 RPS directly against the following backend telemetry:

### 3.1 Orchestrator Metrics
*   **Metric:** `orchestrator_dag_execution_time_ms`
*   **What to watch:** If k6 p95 is 600ms, but the Orchestrator DAG metric claims 150ms, the bottleneck is in the API Gateway queuing or TLS termination, not the application logic.

### 3.2 ML Inference Metrics
*   **Metric:** `ml_inference_time_ms`
*   **What to watch:** During the 500 RPS spike, does the Python ML Service latency spike non-linearly?
*   **Metric:** `python_gil_wait_time`
*   **What to watch:** High values indicate we are starving the event loop. We must increase the number of `gunicorn` workers or horizontal pod replicas.

### 3.3 PostgreSQL Metrics
*   **Metric:** `pg_stat_activity.wait_event_type = 'Lock'`
*   **What to watch:** We are simulating 500 concurrent writes to the `assessments` and `audit_log` tables. We must monitor row-level locking.
*   **Metric:** `pgbouncer.client_waiting`
*   **What to watch:** If connections queue at PgBouncer during the 500 RPS spike, it means database transactions are taking too long to commit and release their connections back to the pool.

---

## 4. Execution Script Core Logic

```javascript
export default function () {
  const url = 'http://api.riskintel.internal/v1/assess';
  
  // Dynamic Payload Generation
  const payload = JSON.stringify({
    applicant: {
      applicant_id: `app-${__VU}-${__ITER}-${Date.now()}`,
      tax_id_hash: `hash-${Math.floor(Math.random() * 10000000)}`,
      first_name: "Load",
      last_name: "Test"
    },
    financial_features: {
      cibil_score: Math.floor(Math.random() * (900 - 600 + 1) + 600), // Mix of pass/fail
      net_monthly_income: 85000,
      age: 35,
      time_with_curr_empr: 48,
      education: "GRADUATE"
    }
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Correlation-ID': `k6-test-${__VU}-${__ITER}`
    },
  };

  const res = http.post(url, payload, params);

  // Record Custom Metrics
  orchestratorLatency.add(res.timings.duration);
  errorRate.add(res.status >= 500);

  // Assertions
  check(res, {
    'is status 200': (r) => r.status === 200,
    'has decision': (r) => r.json('status') === 'APPROVED' || r.json('status') === 'REJECTED',
  });
}
```

---

## 5. Acceptance Criteria
The performance baseline is officially certified for frontend integration ONLY if:
1.  k6 reports a global `http_req_duration` p95 of **< 500ms** during the sustained 100 RPS phase.
2.  During the 500 RPS spike, the system does not drop traffic (0 `503` or `500` errors).
3.  The database `max_connections` limit is never hit (validating PgBouncer logic).
4.  The system fully recovers to baseline latency (< 500ms) within 30 seconds of the spike concluding.
