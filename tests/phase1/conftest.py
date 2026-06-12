import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/riskintel_test")

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DB_URL)
    yield eng
    eng.dispose()

@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def raw_connection(engine):
    with engine.connect() as conn:
        yield conn
