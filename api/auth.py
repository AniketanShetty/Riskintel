"""
api/auth.py
-----------
Authentication dependencies for FastAPI routes.

Two mechanisms:
  - verify_api_key   : Validates X-API-Key header for internal routes.
  - verify_hmac      : Validates X-Hub-Signature-256 + X-Timestamp headers for webhook routes.

Secrets are read exclusively from environment variables at import time.
Missing secrets cause a hard startup failure (fail-closed).
"""
import hashlib
import hmac
import time

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import APIKeyHeader
from core.config import settings

# ---------------------------------------------------------------------------
# API-Key dependency (internal routes)
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """
    FastAPI dependency. Raises HTTP 401 if X-API-Key is missing.
    Raises HTTP 403 if the key does not match the configured secret.

    Uses a constant-time comparison to prevent timing attacks.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header.")

    if not settings.RISKINTEL_API_KEY:
        # Server is misconfigured — reject every request
        raise HTTPException(status_code=503, detail="API authentication is not configured.")

    if not hmac.compare_digest(x_api_key, settings.RISKINTEL_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key.")


# ---------------------------------------------------------------------------
# HMAC-SHA256 + timestamp dependency (webhook routes)
# ---------------------------------------------------------------------------


async def verify_hmac(request: Request, x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"), x_timestamp: str | None = Header(default=None, alias="X-Timestamp")) -> None:
    """
    FastAPI dependency. Validates the HMAC-SHA256 signature and timestamp of a webhook request.

    Expected sender behaviour:
      1. Obtain the raw request body bytes.
      2. Concatenate: timestamp + "." + body (UTF-8 bytes).
      3. Compute HMAC-SHA256(secret, concatenated_payload).
      4. Set X-Timestamp to the Unix timestamp (integer string).
      5. Set X-Hub-Signature-256 to "sha256=<hex_digest>".

    Validation steps performed here:
      1. Both headers must be present.
      2. X-Timestamp must be a valid integer within TIMESTAMP_TOLERANCE_SECONDS of now.
      3. HMAC of (timestamp + "." + raw_body) must match X-Hub-Signature-256.
    """
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header.")
    if not x_timestamp:
        raise HTTPException(status_code=401, detail="Missing X-Timestamp header.")

    if not settings.RISKINTEL_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook authentication is not configured.")

    # 1. Validate timestamp bounds (replay protection)
    try:
        event_ts = int(x_timestamp)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-Timestamp must be a Unix integer.")

    now = int(time.time())
    if abs(now - event_ts) > settings.RISKINTEL_TIMESTAMP_TOLERANCE:
        raise HTTPException(
            status_code=400,
            detail=f"Timestamp outside tolerance window ({settings.RISKINTEL_TIMESTAMP_TOLERANCE}s).",
        )

    # 2. Read raw body (FastAPI caches it on the request object)
    raw_body: bytes = await request.body()

    # 3. Reconstruct signed payload: timestamp_bytes + b"." + body
    signed_payload = x_timestamp.encode() + b"." + raw_body

    # 4. Compute expected signature
    expected_sig = "sha256=" + hmac.new(
        settings.RISKINTEL_WEBHOOK_SECRET.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    # 5. Constant-time comparison
    if not hmac.compare_digest(expected_sig, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid HMAC signature.")
