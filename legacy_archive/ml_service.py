import os
import joblib
import logging
import uuid
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Request
from pydantic import BaseModel, Field, ConfigDict
import numpy as np

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ml_inference_service")

# Global State for Model Artifacts
ACTIVE_MODEL: Dict[str, Any] = {
    "model_id": "m-883a-kmns-v2.1",
    "pipeline": None,
    "archetype_map": {
        0: "High-Income Established",
        1: "Young Starters",
        2: "Mid-Career Established",
        3: "High-Risk Revolvers"
    }
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup Event: Load the Scikit-Learn pipeline into memory.
    This guarantees the model and scaler are loaded exactly once.
    """
    model_path = os.getenv("E3_MODEL_PATH", "e3_pipeline_latest.pkl")
    logger.info(f"Booting ML Inference Service. Loading model from {model_path}...")
    
    try:
        # In a real environment, this might download from S3 first.
        # ACTIVE_MODEL["pipeline"] = joblib.load(model_path)
        
        # MOCKING pipeline load for runnable demonstration
        class MockPipeline:
            def predict(self, X):
                # Returns cluster 2 for any input
                return np.array([2])
                
            def transform(self, X):
                # Mock distances to centroids
                return np.array([[2.5, 3.1, 0.4, 4.2]])

        ACTIVE_MODEL["pipeline"] = MockPipeline()
        logger.info(f"Successfully loaded model version {ACTIVE_MODEL['model_id']} into memory.")
        
    except Exception as e:
        logger.error(f"Failed to load model artifact: {e}")
        # In production, we deliberately crash the container if the model fails to load.
        raise RuntimeError("FATAL: Cannot start Inference Service without model artifact.")
        
    yield
    
    # Shutdown Event: Clean up resources
    logger.info("Shutting down ML Inference Service, flushing models from memory.")
    ACTIVE_MODEL["pipeline"] = None


app = FastAPI(
    title="RiskIntel ML Inference Service",
    version="1.0.0",
    lifespan=lifespan
)


# --- Pydantic Schemas (The Protective Boundary) ---

class InferenceRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Drops unexpected schema drift fields
    
    cibil_score: int = Field(..., ge=300, le=900)
    net_monthly_income: float = Field(..., gt=0)
    age: int = Field(..., ge=18, le=100)
    time_with_curr_empr: int = Field(..., ge=0)
    
    def to_numpy_array(self) -> np.ndarray:
        """Enforces exact feature ordering for the model."""
        return np.array([[
            self.cibil_score,
            self.net_monthly_income,
            self.age,
            self.time_with_curr_empr
        ]])


class InferenceResponse(BaseModel):
    model_id: str
    archetype_label: str
    cluster_distances: Dict[str, float]


# --- API Routes ---

@app.post("/v1/predict", response_model=InferenceResponse, status_code=status.HTTP_200_OK)
async def predict_archetype(payload: InferenceRequest, request: Request):
    """
    Executes the E3 K-Means Inference.
    Expects strict coercion by Pydantic before hitting the ML pipeline.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    logger.info(f"[{correlation_id}] Received inference request.")
    
    if ACTIVE_MODEL["pipeline"] is None:
        logger.error(f"[{correlation_id}] Inference rejected: Model not loaded in memory.")
        raise HTTPException(status_code=503, detail="Model artifact unavailable.")
        
    try:
        # 1. Strict Ordered Array Conversion
        features_array = payload.to_numpy_array()
        
        # 2. Pipeline Execution (Scaler + K-Means)
        cluster_idx = ACTIVE_MODEL["pipeline"].predict(features_array)[0]
        distances = ACTIVE_MODEL["pipeline"].transform(features_array)[0]
        
        # 3. Output Mapping
        archetype = ACTIVE_MODEL["archetype_map"].get(int(cluster_idx), "Unknown")
        distance_map = {f"cluster_{i}": round(float(dist), 4) for i, dist in enumerate(distances)}
        
        logger.info(f"[{correlation_id}] Inference successful. Archetype: {archetype}")
        
        return InferenceResponse(
            model_id=ACTIVE_MODEL["model_id"],
            archetype_label=archetype,
            cluster_distances=distance_map
        )
        
    except ValueError as ve:
        # e.g. NumPy matrix dimension mismatch
        logger.error(f"[{correlation_id}] Matrix execution ValueError: {str(ve)}")
        raise HTTPException(status_code=422, detail=f"Inference computation error: {str(ve)}")
        
    except Exception as e:
        logger.exception(f"[{correlation_id}] Fatal inference error.")
        raise HTTPException(status_code=500, detail="Internal inference failure.")


@app.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Simple process check for Kubernetes."""
    return {"status": "UP"}


@app.get("/health/deep", status_code=status.HTTP_200_OK)
async def deep_readiness_probe():
    """Verifies that the model is actively loaded into RAM."""
    if ACTIVE_MODEL["pipeline"] is None:
        raise HTTPException(status_code=503, detail="Model pipeline missing.")
        
    return {
        "status": "READY",
        "active_model_id": ACTIVE_MODEL["model_id"],
        "pipeline_status": "LOADED_IN_MEMORY"
    }

# To run locally:
# uvicorn ml_service:app --host 0.0.0.0 --port 8000
