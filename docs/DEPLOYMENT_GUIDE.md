# Deployment Guide

RiskIntel V2 relies exclusively on a fully containerized architecture to eliminate environment parity issues.

## 1. Environment Variables

The application enforces a **fail-fast configuration paradigm**. The container will instantly crash if the following variables are not injected at runtime:

* `DATABASE_URL`: The PostgreSQL connection string (e.g., `postgresql://postgres:postgrespassword@db:5432/riskintel`).
* `RISKINTEL_API_KEY`: The master secret for internal API consumption.
* `RISKINTEL_WEBHOOK_SECRET`: The cryptographic key used to sign and verify external webhook HMAC-SHA256 signatures.

## 2. Docker Compose Deployment

The fastest way to deploy the entire stack (PostgreSQL + FastAPI + Migrations) is via Docker Compose. The `docker-compose.yml` automatically mounts the database and connects the network.

```bash
# Build and deploy the stack in detached mode
docker compose up -d --build

# View operational logs
docker compose logs riskintel-backend -f
```

## 3. Database Migrations

Database schemas are strictly managed by **Alembic**.

**Automatic Migrations:**
In production and via Docker Compose, the `entrypoint.sh` script inherently runs `alembic upgrade head` before booting the `uvicorn` server. This guarantees the schema is perfectly aligned with the running code.

**Manual Operations:**
To run migrations manually or locally:
```bash
alembic upgrade head
```

## 4. Rollback Protocols

Because RiskIntel V2 utilizes strict DAG migrations, rolling back the database state is mathematically safe and heavily tested.

If a deployment introduces a critical regression, you can revert the database schema state by dropping down a revision:

```bash
# Downgrade 1 revision step
alembic downgrade -1

# Wipe the database schema completely (development only)
alembic downgrade base
```

## 5. Health and Readiness Checks

RiskIntel exposes Kubernetes-compliant probes to manage traffic routing and load balancing gracefully.

* **Liveness Probe (`GET /health`):** Verifies the FastAPI event loop is running. Requires the `X-API-Key` header.
* **Readiness Probe (`GET /ready`):** Verifies the application has successfully established a connection to the PostgreSQL database. If the database is unreachable, this endpoint actively returns a `503 Service Unavailable`, instructing the load balancer to pull the instance from the rotation. Requires the `X-API-Key` header.
