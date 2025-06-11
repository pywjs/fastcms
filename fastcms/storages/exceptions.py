# fastcms/storages/exceptions.py


class StorageError(Exception):
    """Base class for all storage-related exceptions."""

    pass


class StorageNotFoundError(StorageError):
    pass


class StorageFileNotFoundError(StorageError):
    pass


class StorageFileNotExistError(StorageError):
    pass


class StorageFolderNotFoundError(StorageError):
    pass


class StorageFileExistsError(StorageError):
    pass


class StorageFolderExists(StorageError):
    pass


class StoragePermissionError(StorageError):
    pass


class StorageFolderPermissionError(StorageError):
    pass


class StorageFilePermissionError(StorageError):
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
