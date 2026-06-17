from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# Default to the local dev DB
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
