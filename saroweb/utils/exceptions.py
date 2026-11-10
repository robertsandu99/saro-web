class AppError(Exception):
    """Base exception for all application domain errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""


class ConflictError(AppError):
    """Raised when a resource already exists (e.g. duplicate name)."""


class UnauthorizedError(AppError):
    """Raised when authentication fails or a token is invalid/expired."""


class ForbiddenError(AppError):
    """Raised when an authenticated user lacks permission for an action."""


class ValidationError(AppError):
    """Raised when domain-level validation fails (not HTTP/Pydantic level)."""
