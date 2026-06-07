# legacy_archive/

Quarantined reference material from prior RiskIntel implementations.

**Do not import, do not depend on, do not modify for V1 features.**

These files are kept for historical reference only. The canonical V1
backend is FastAPI + SQLite; nothing in this directory is part of the
shipping backend, models, services, or migrations.

Files:

- `ml_service.py`        — earlier FastAPI ML inference prototype
- `models.py`            — earlier SQLAlchemy model definitions
- `orchestrator.py`      — earlier orchestrator skeleton
- `rule_engine.py`       — earlier rule engine prototype
- `schemas.py`           — earlier Pydantic schemas
- `alembic/versions/`    — earlier Alembic migration
- `tests/`               — earlier test suite

If you need something from here, port it into `backend/app/` and add
proper tests. Do not resurrect this code path.
