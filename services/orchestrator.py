from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from schemas.events import OrchestratorEvent
from models.session import ApplicationSession
from models.state_event import StateTransitionEvent
from core.fsm_graph import get_next_state, InvalidTransitionError

class OrchestratorError(Exception):
    pass

class SessionNotFoundError(OrchestratorError):
    pass

def process_event(db: Session, event: OrchestratorEvent, actor: str = "system", auto_commit: bool = True) -> ApplicationSession:
    """
    The singular, atomic entrypoint for all State Machine transitions.
    Enforces a strict Unit-of-Work boundary and pessimistic row locking.
    """
    try:
        # 1. Pessimistic Row Lock (FOR UPDATE)
        # Prevents race conditions during simultaneous event ingestion
        session_obj = db.query(ApplicationSession).with_for_update().filter_by(id=event.session_id).first()
        
        if not session_obj:
            raise SessionNotFoundError(f"ApplicationSession {event.session_id} not found.")

        old_state = session_obj.current_state

        # 2. FSM Validation & Transition
        # This will raise InvalidTransitionError if the event violates the strict graph
        new_state = get_next_state(old_state, event.event_type)

        # 3. State Mutation
        session_obj.current_state = new_state

        # 4. Immutable Audit Ledger Append
        transition_event = StateTransitionEvent(
            session_id=session_obj.id,
            from_state=old_state,
            to_state=new_state,
            trigger_event=event.event_type,
            occurred_at=event.occurred_at,
            actor=actor
        )
        db.add(transition_event)

        # 5. Atomic Commit (or Flush if auto_commit=False)
        if auto_commit:
            db.commit()
        else:
            db.flush()
        db.refresh(session_obj)
        
        return session_obj

    except InvalidTransitionError:
        # Rollback implicitly handled by session management, but we ensure cleanliness
        db.rollback()
        raise
    except OrchestratorError:
        # Prevent double wrapping of custom errors
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise OrchestratorError(f"Transaction failed: {str(e)}") from e
