# fastcms/services/exceptions.py


class DBServiceError(Exception):
    """Base class for all database service-related exceptions."""

    pass


class DBServiceIntegrityError(DBServiceError):
    """Exception raised for integrity errors in database operations."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field
