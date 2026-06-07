# RiskIntel Project State

## Last Updated
- Date: 2026-06-07
- Authoring agent: Antigravity

## Current Phase
- V1 Remediation and Preparation

## Current Objective
- Complete V1 immediate requirements (routing decisions, E6/E5 metadata flags), fix the backend API startup sequence, and establish strict project state tracking.

## Verified Reality
- The repository is currently **not** a git repository (`git status` fails with a fatal error).
- The backend test suite is completely passing (317 passed).
- The backend API now starts successfully via `python run.py` (rewritten to launch uvicorn against `app.main:app`). Verified 2026-06-07: `GET /health/live` → 200, `/health/ready` → 200 (SQLite CONNECTED), `/health/deep` → 200, `/docs` → 200.
- V1 logic items `routing_decision`, `E6 is_unclassified`, and `E5 metadata` are now surfaced in API responses and audit log (verified 2026-06-07).

## Recently Completed
- Executed Repository Reality Audit based on live filesystem and code state (2026-06-07).
- Verified implementation status of key components.

## Current Blockers
- **Missing Source Control:** No `.git` directory exists, preventing version tracking or drift auditing.

## Recently Resolved
- **API Runtime Error (2026-06-07):** Rewrote `backend/run.py` from Flask factory entry point to a thin uvicorn launcher (`uvicorn.run("app.main:app", ...)`). Backend now boots, lifespan startup completes, SQLite engine connects, and `/health/*` + `/docs` respond 200.
- **V1 Logic Surfacing (2026-06-07):** Surfaced `routing_decision` (top-level: `{original_user_type, routed_to, reason}`), `E6 is_unclassified` (on `archetype` when `cluster_id == 0`), and `E5 metadata` (`imputed_fields`, `mapped_features`, `policy_override_applied` on `readiness`). Audit schema migrated forward-only to add `request_payload_hash`, `user_type_original`, `routing_decision` columns. Response schemas extended additively.

## Open Questions
- Should we initialize a fresh git repository to begin tracking governance remediation?
- Should `run.py` be removed entirely in favor of a Makefile / `uvicorn` CLI convention, or kept as the canonical entrypoint?

## Settled Decisions
- `PROJECT_STATE.md` is the canonical memory layer for the project and must be maintained as truth.
- Repository reality supersedes documentation.
- Backend is built on FastAPI with SQLite as the authoritative persistence layer.

## Next Action
- Initialize a git repository and commit the current state (post-`run.py` fix and V1 logic surfacing).

## Implementation Status
- routing_decision: Implemented (VERIFIED 2026-06-07) — top-level field `{original_user_type, routed_to, reason}` in both response paths and audit log.
- E6 is_unclassified: Implemented (VERIFIED 2026-06-07) — surfaced on `archetype` object; `true` when `cluster_id == 0` (General Micro-Enterprise / unknown).
- E5 metadata injection: Implemented (VERIFIED 2026-06-07) — `imputed_fields`, `mapped_features`, `policy_override_applied` propagated into `readiness.metadata` and audit log.
- fail-closed audit logging: Implemented (VERIFIED)

## Notes for Future Sessions
- Read this file before making any edits or recommendations.
- Update this file after every meaningful change.
- Never rely only on chat history or governance documents. Trust repository reality.
- If something is unknown, mark it UNKNOWN rather than guessing.
- Do not silently change scope or allow the project to drift into unrelated work.
- If any repository reality conflicts with this file, verify and update this file before proceeding.

## Change Log
- [2026-06-07] Initialized PROJECT_STATE.md following the Repository Reality Audit.
- [2026-06-07] Rewrote `backend/run.py` (Flask → uvicorn launcher) to fix backend startup. Verified: server boots, lifespan completes, SQLite connects, `/health/live|ready|deep` and `/docs` all return 200.
- [2026-06-07] Surfaced V1 logic in API + audit: `routing_decision` (top-level), `archetype.is_unclassified` (E6), `readiness.metadata` (E5). Audit schema migrated forward-only with 3 additive columns. Response schemas extended additively. All 317 backend tests pass.
