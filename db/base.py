import uuid
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

@event.listens_for(Base, "init", propagate=True)
def receive_init(target, args, kwargs):
    if "id" not in kwargs:
        kwargs["id"] = str(uuid.uuid4())
