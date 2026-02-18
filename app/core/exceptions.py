from typing import Any, Dict, Optional

class BaseAppException(Exception):
    """Base exception for the application."""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ExternalServiceError(BaseAppException):
    """Raised when an external service (Google Sheets, Firebase, etc.) fails."""
    def __init__(self, message: str, service_name: str, original_error: Optional[Exception] = None):
        details = {"service": service_name}
        if original_error:
            details["original_error"] = str(original_error)
        super().__init__(message, status_code=503, details=details)

class DatabaseError(BaseAppException):
    """Raised when a database operation fails."""
    def __init__(self, message: str, operation: str = "unknown"):
        super().__init__(message, status_code=500, details={"operation": operation})

class AuthenticationError(BaseAppException):
    """Raised when authentication fails."""
    def __init__(self, message: str):
        super().__init__(message, status_code=401)

class ConfigurationError(BaseAppException):
    """Raised when there is a configuration issue."""
    def __init__(self, message: str, config_key: str):
        super().__init__(message, status_code=500, details={"config_key": config_key})

class AuthorizationError(BaseAppException):
    """Raised when a user is not authorized to perform an action."""
    def __init__(self, message: str):
        super().__init__(message, status_code=403)

class NotFoundError(BaseAppException):
    """Raised when a resource is not found."""
    def __init__(self, message: str, resource_type: str, resource_id: str):
        super().__init__(
            message, 
            status_code=404, 
            details={"resource_type": resource_type, "resource_id": resource_id}
        )

class RateLimitExceededError(BaseAppException):
    """Raised when an API rate limit is exceeded."""
    def __init__(self, message: str, provider: str, retry_after: float = None):
        details = {"provider": provider}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, status_code=429, details=details)
