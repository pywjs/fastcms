# fastcms/utils/crypto.py

from passlib.context import CryptContext
from enum import StrEnum


class UnSupportedHashingSchemeError(Exception):
    """Exception raised for unsupported hashing schemes."""

    pass


class HashingScheme(StrEnum):
    ARGON2 = "argon2"
    BCRYPT = "bcrypt"
    MD5 = "md5"  # Not recommended for production use, only for tests

    @classmethod
    def choices(cls):
        return [cls.ARGON2, cls.BCRYPT, cls.MD5]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.choices()


class PasswordHasher:
    def __init__(self, scheme: HashingScheme = HashingScheme.ARGON2):
        if isinstance(scheme, str):
            try:
                scheme = HashingScheme(scheme.lower())
            except ValueError:
                raise UnSupportedHashingSchemeError(
                    f"Unsupported hashing scheme: {scheme}"
                )
        if not HashingScheme.is_valid(scheme):
            raise UnSupportedHashingSchemeError(f"Unsupported hashing scheme: {scheme}")

        # Loop through the schemes to set up the CryptContext
        if scheme == HashingScheme.ARGON2:
            self.context = CryptContext(
                schemes=["argon2"],
                deprecated="auto",
                argon2__type="ID",
                argon2__memory_cost=65536,  # 64 MB
                argon2__time_cost=2,
                argon2__parallelism=4,
                argon2__hash_len=16,
                argon2__salt_size=16,
            )
        elif scheme == HashingScheme.BCRYPT:
            self.context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        elif scheme == HashingScheme.MD5:
            # MD5 is not recommended for production use, only for tests
            self.context = CryptContext(
                schemes=["md5_crypt"],
                deprecated="auto",
            )
        else:
            raise UnSupportedHashingSchemeError(f"Unsupported hashing scheme: {scheme}")

    def hash(self, password: str) -> str:
        return self.context.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self.context.verify(plain_password, hashed_password)

    def needs_rehash(self, hashed_password: str) -> bool:
        return self.context.needs_update(hashed_password)
