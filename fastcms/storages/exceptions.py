# fastcms/storages/exceptions.py


class StorageError(Exception):
    """Base class for all storage-related exceptions."""

    pass


class StorageNotFound(StorageError):
    pass


class FileNotFound(StorageError):
    pass


class FolderNotFound(StorageError):
    pass


class FileExists(StorageError):
    pass


class FolderExists(StorageError):
    pass


class StoragePermissionError(StorageError):
    pass


class FolderPermissionError(StorageError):
    pass


class FilePermissionError(StorageError):
    pass


class StorageInitializationError(StorageError):
    pass


class StorageConfigurationError(StorageError):
    pass


class StorageOperationError(StorageError):
    pass


class StorageUnsupportedOperationError(StorageError):
    pass


class StorageInvalidPathError(StorageError):
    pass


class StorageInvalidFileTypeError(StorageError):
    pass


class StorageQuotaExceededError(StorageError):
    pass


class StorageFileTooLargeError(StorageError):
    pass
