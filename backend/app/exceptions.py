"""
exceptions.py

RiskIntel orchestrator exceptions.
"""

class RiskIntelException(Exception):
    """Base exception for all RiskIntel errors."""
    pass

class CriticalEngineError(RiskIntelException):
    """Exception raised when a critical engine (E1, E2, E5) fails."""
    def __init__(self, engine_name: str, original_exception: Exception):
        super().__init__(f"Critical engine {engine_name} failed: {original_exception}")
        self.engine_name = engine_name
        self.original_exception = original_exception

class NonCriticalEngineError(RiskIntelException):
    """Exception raised when a non-critical engine (E3, E4, E6) fails."""
    def __init__(self, engine_name: str, original_exception: Exception):
        super().__init__(f"Non-critical engine {engine_name} failed: {original_exception}")
        self.engine_name = engine_name
        self.original_exception = original_exception

class AuditLogError(RiskIntelException):
    """Exception raised when audit logging fails."""
    pass

class RequestValidationError(RiskIntelException):
    """Exception raised when incoming request validation fails."""
    def __init__(self, message: str, details: list = None):
        super().__init__(message)
        self.details = details or []


class GovernanceError(RiskIntelException):
    """
    Exception raised when a canonical SSOT value is missing where one is
    required. Used as the fail-loud mechanism for threshold governance:
    instead of silently substituting a hardcoded fallback, raise this error
    so the missing-engine-metadata condition is detected and the request
    is degraded (never silently miscomputed).
    """
    def __init__(self, message: str, governance_key: str = ""):
        super().__init__(message)
        self.governance_key = governance_key
