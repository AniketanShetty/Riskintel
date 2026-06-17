from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    RISKINTEL_API_KEY: str
    RISKINTEL_WEBHOOK_SECRET: str
    RISKINTEL_TIMESTAMP_TOLERANCE: int = 300

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
