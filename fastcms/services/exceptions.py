# fastcms/services/exceptions.py


class DBServiceError(Exception):
    """Base class for all database service-related exceptions."""

    pass


class DBServiceIntegrityError(DBServiceError):
    """Exception raised for integrity errors in database operations."""

    pass
