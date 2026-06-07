"""
RiskIntel — SQLAlchemy declarative base.

All ORM models inherit from this Base class.
Import this module to ensure all models are registered with the metadata.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base class for all RiskIntel ORM models."""
    pass
