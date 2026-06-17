import sys
import os
import time
from datetime import datetime, timedelta, timezone

# Ensure we can import from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.session import SessionLocal
from models.session import ApplicationSession
from schemas.events import OrchestratorEvent, EventType
from services.orchestrator import process_event
from core.config import settings

def run_ttl_sweep(db=None):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Running TTL Sweep...")
    db_session = db or SessionLocal()
    try:
        # PENDING_VERIFICATION -> FO_UNREACHABLE_TTL_EXPIRED
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=settings.RISKINTEL_TIMESTAMP_TOLERANCE)
        # Using naive datetime to match DB if it stores naive datetimes
        naive_cutoff = cutoff.replace(tzinfo=None)

        stuck_verifications = db_session.query(ApplicationSession).filter(
            ApplicationSession.current_state == "PENDING_VERIFICATION",
            ApplicationSession.updated_at < naive_cutoff
        ).all()

        for session in stuck_verifications:
            try:
                event = OrchestratorEvent(
                    session_id=session.id,
                    event_type=EventType.FO_UNREACHABLE_TTL_EXPIRED,
                    payload={"reason": "TTL expired waiting for verification webhook"}
                )
                process_event(db_session, event, actor="ttl_worker")
                print(f"Expired PENDING_VERIFICATION for session {session.id}")
            except Exception as e:
                print(f"Failed to expire session {session.id}: {e}")

        # PENDING_REPROMPT -> REPROMPT_TIMEOUT_EXPIRED
        stuck_reprompts = db_session.query(ApplicationSession).filter(
            ApplicationSession.current_state == "PENDING_REPROMPT",
            ApplicationSession.updated_at < naive_cutoff
        ).all()

        for session in stuck_reprompts:
            try:
                event = OrchestratorEvent(
                    session_id=session.id,
                    event_type=EventType.REPROMPT_TIMEOUT_EXPIRED,
                    payload={"reason": "TTL expired waiting for user reprompt data"}
                )
                process_event(db_session, event, actor="ttl_worker")
                print(f"Expired PENDING_REPROMPT for session {session.id}")
            except Exception as e:
                print(f"Failed to expire session {session.id}: {e}")

        # NEARLY_READY -> COUNTER_OFFER_EXPIRED
        stuck_offers = db_session.query(ApplicationSession).filter(
            ApplicationSession.current_state == "NEARLY_READY",
            ApplicationSession.updated_at < naive_cutoff
        ).all()

        for session in stuck_offers:
            try:
                event = OrchestratorEvent(
                    session_id=session.id,
                    event_type=EventType.COUNTER_OFFER_EXPIRED,
                    payload={"reason": "TTL expired waiting for counter offer decision"}
                )
                process_event(db_session, event, actor="ttl_worker")
                print(f"Expired NEARLY_READY for session {session.id}")
            except Exception as e:
                print(f"Failed to expire session {session.id}: {e}")

    finally:
        if db is None:
            db_session.close()
    print("TTL Sweep Complete.")

if __name__ == "__main__":
    run_ttl_sweep()
