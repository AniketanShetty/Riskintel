# Chaos Engineering Spec: Audit Partition (Fail-Closed Validation)

**Role:** Principal Chaos Engineer  
**Target Function:** `chaos_test_audit_partition()`  
**Objective:** Prove mathematically and operationally that the RiskIntel Orchestrator cannot issue an underwriting decision to a user if the Audit Ledger broker is unreachable. This guarantees FCRA/ECOA compliance by preventing a "Fail-Open" scenario.

---

## 1. Infrastructure Setup
To execute this chaos experiment, the test environment must precisely mirror the production topology.
*   **Services Required:** Orchestrator, Rules Engine (E1, E2, E5), ML Inference (E3, E4).
*   **Databases:** PostgreSQL (RiskIntel core tables).
*   **Message Broker:** A single-node Apache Kafka cluster (or RabbitMQ) acting as the Audit Ledger ingress.
*   **Chaos Tooling:** Toxiproxy or Chaos Mesh installed between the Orchestrator service and the Kafka broker.

## 2. Kafka Outage Simulation
We will simulate a hard network partition mid-execution.
1.  **Baseline:** Ensure the Orchestrator can successfully ping the Kafka broker.
2.  **Partition Trigger:** Inject a network block using Toxiproxy (drop all TCP packets on port 9092) or use `iptables` to block the IP address of the Kafka broker from the Orchestrator pod.
3.  **Verification:** The Orchestrator's internal Kafka Producer client will immediately begin queuing events locally and attempting retries, eventually triggering a `TimeoutException`.

## 3. Expected Orchestrator Behavior
The Orchestrator processes the `POST /v1/assess` request. 
*   It successfully evaluates the E1 eligibility rule.
*   It attempts to asynchronously fire the `E1_EVALUATED` event to the Kafka broker.
*   Because the producer requires `acks=1` (or `acks=all` for highest durability), the publish request times out (e.g., after a configured 1000ms `request.timeout.ms`).
*   **CRITICAL JUNCTURE:** The Orchestrator catches the `TimeoutException`. It *must not* proceed to E2. It must immediately halt the Directed Acyclic Graph (DAG) execution.

## 4. Rollback Validation
When the DAG halts due to the audit failure, the Orchestrator must execute a database rollback.
*   The Orchestrator initiates a PostgreSQL `ROLLBACK` on the current active transaction.
*   Alternatively (if using Sagas), it issues an explicit `UPDATE assessments SET status = 'FAILED_PROCESSING'` for that specific `applicant_id`.

## 5. API Assertions
The frontend must receive an explicit error; it must never receive an approval or rejection.
*   **Expected HTTP Status:** `500 Internal Server Error` (or `503 Service Unavailable`).
*   **Expected Response Body:**
    ```json
    {
      "error": "system_failure",
      "message": "The assessment could not be completed due to an internal system timeout. No underwriting decision was made. Please try again."
    }
    ```
*   **Assertion:** The response payload *must not* contain `status: APPROVED` or `status: REJECTED`. It must not contain any credit limits or adverse action codes.

## 6. Database Assertions
We must mathematically prove that no partial or un-audited decisions "leaked" into the database.
*   **Query 1:** `SELECT * FROM assessments WHERE id = 'test_assessment_id';`
    *   **Assertion:** The row exists, but `status` MUST equal `FAILED_PROCESSING`. It must NOT equal `APPROVED` or `REJECTED`.
*   **Query 2:** `SELECT * FROM eligibility_results WHERE assessment_id = 'test_assessment_id';`
    *   **Assertion:** Returns 0 rows. The rollback prevented the un-audited E1 result from persisting.
*   **Query 3:** `SELECT * FROM archetype_results WHERE assessment_id = 'test_assessment_id';`
    *   **Assertion:** Returns 0 rows.

## 7. Acceptance Criteria
The `chaos_test_audit_partition()` test is considered passing ONLY if all of the following are true:
1.  The network partition successfully triggers a Kafka publish timeout.
2.  The Orchestrator intercepts the timeout and explicitly aborts the DAG.
3.  The API returns a `500` error and does *not* leak an underwriting decision.
4.  The PostgreSQL database rolls back the transaction, ensuring no partial E1/E2 results are persisted without their corresponding audit logs. 
5.  When the network partition is healed (Toxiproxy block removed), the system immediately recovers and processes the next assessment normally, demonstrating resilience.
