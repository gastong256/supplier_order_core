from fastapi import HTTPException, status


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str | int) -> None:
        super().__init__(f"{resource} '{identifier}' not found.", code="NOT_FOUND")


class ConflictError(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFLICT")


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Not authenticated.") -> None:
        super().__init__(message, code="UNAUTHORIZED")


class ForbiddenError(AppException):
    def __init__(self, message: str = "Permission denied.") -> None:
        super().__init__(message, code="FORBIDDEN")


# ── FastAPI HTTP shortcuts ────────────────────────────────────────────────────

HTTP_401 = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
HTTP_403 = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")
HTTP_404 = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found.")
