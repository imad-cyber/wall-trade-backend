"""
Custom exception classes for the application.
Provides domain-specific exceptions for better error handling and API responses.
"""


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "APP_ERROR"):
        """
        Initialize AppException.

        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Application-specific error code
        """
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class ValidationError(AppException):
    """Raised when validation fails."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        super().__init__(message, status_code=422, error_code=error_code)


class DatabaseError(AppException):
    """Raised when database operations fail."""

    def __init__(self, message: str, error_code: str = "DATABASE_ERROR"):
        super().__init__(message, status_code=503, error_code=error_code)


class AIProviderError(AppException):
    """Raised when an AI provider call fails."""

    def __init__(self, message: str, error_code: str = "AI_PROVIDER_ERROR"):
        super().__init__(message, status_code=502, error_code=error_code)


class RateLimitError(AppException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", error_code: str = "RATE_LIMIT_ERROR"):
        super().__init__(message, status_code=429, error_code=error_code)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", error_code: str = "AUTH_ERROR"):
        super().__init__(message, status_code=401, error_code=error_code)


class AuthorizationError(AppException):
    """Raised when user lacks permissions."""

    def __init__(self, message: str = "Insufficient permissions", error_code: str = "AUTHORIZATION_ERROR"):
        super().__init__(message, status_code=403, error_code=error_code)


class ResourceNotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, error_code: str = "NOT_FOUND"):
        message = f"{resource} not found"
        super().__init__(message, status_code=404, error_code=error_code)


class ConflictError(AppException):
    """Raised when a resource already exists."""

    def __init__(self, message: str, error_code: str = "CONFLICT"):
        super().__init__(message, status_code=409, error_code=error_code)


class ExternalServiceError(AppException):
    """Raised when external service calls fail."""

    def __init__(self, service: str, message: str, error_code: str = "EXTERNAL_SERVICE_ERROR"):
        full_message = f"{service} error: {message}"
        super().__init__(full_message, status_code=502, error_code=error_code)
