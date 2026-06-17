import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

TEST_DB_URL = settings.TEST_DATABASE_URL or "postgresql://postgres:postgres@localhost:5432/riskintel_test"

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
