"""
RiskIntel — Backend API entry point.

Usage:
    cd backend/
    python run.py

The canonical FastAPI app is defined globally in `app/main.py`.
All configuration is read from environment variables (see .env.example).
"""
import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        reload=os.environ.get("RELOAD", "false").lower() in ("1", "true", "yes"),
    )
