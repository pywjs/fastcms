# tests/utils/test_crypto.py
import pytest

from fastcms.utils.crypto import (
    HashingScheme,
    PasswordHasher,
    get_random_string,
    UnSupportedHashingSchemeError,
)


@pytest.mark.parametrize(
    "scheme", [HashingScheme.ARGON2, HashingScheme.BCRYPT, HashingScheme.MD5]
)
def test_password_hashing(scheme):
    hasher = PasswordHasher(scheme)
    password = "s3cr3t-password"
    hashed = hasher.hash(password)

    assert isinstance(hashed, str)
    assert hasher.verify(password, hashed)
    assert not hasher.verify("wrong-password", hashed)


@pytest.mark.parametrize("length", [8, 16, 32, 64])
def test_get_random_string_length(length):
    s = get_random_string(length)
    assert isinstance(s, str)
    assert len(s) == length


def test_get_random_string_allowed_chars():
    allowed = "ABC123"
    s = get_random_string(20, allowed_chars=allowed)
    assert all(c in allowed for c in s)


def test_unsupported_scheme_raises():
    with pytest.raises(UnSupportedHashingSchemeError):
        PasswordHasher("unsupported")  # noqa


def test_invalid_scheme_enum_validation():
    assert HashingScheme.is_valid("argon2") is True
    assert HashingScheme.is_valid("bcrypt") is True
    assert HashingScheme.is_valid("md5") is True
    assert HashingScheme.is_valid("sha512") is False
