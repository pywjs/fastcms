# fastcms/utils/jwt.py

from datetime import datetime, timedelta
from typing import Any, Literal
from enum import StrEnum

import jwt as _jwt
from pydantic import BaseModel, ConfigDict

from fastcms.utils import current_time


class JWTError(Exception):
    pass


class UnsupportedJWTAlgorithmError(JWTError):
    pass


class ExpiredTokenError(JWTError):
    pass


class InvalidTokenError(JWTError):
    pass


class JWTTokenPayload(BaseModel):
    """A JWT token payload, requires minimum fields to be valid, can have extra fields."""

    model_config = ConfigDict(
        extra="allow",
    )

    sub: str
    iat: datetime | int
    exp: datetime | int


class JWTAlgorithm(StrEnum):
    HS256 = "HS256"

    @classmethod
    def choices(cls):
        return [cls.HS256]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls.choices()


class JWTHandler:
    def __init__(
        self,
        secret: str,
        algorithm: JWTAlgorithm = JWTAlgorithm.HS256,
        access_token_expire_minutes: int = 30,  # 30 minutes
        refresh_token_expire_minutes: int = 60 * 24 * 7,  # 7 days
    ):
        # Validate algorithm
        if isinstance(algorithm, str):
            try:
                algorithm = JWTAlgorithm(algorithm.capitalize())
            except ValueError:
                raise UnsupportedJWTAlgorithmError(
                    f"Unsupported JWT algorithm: {algorithm}"
                )

        # Check if the algorithm is valid
        if not JWTAlgorithm.is_valid(algorithm):
            raise UnsupportedJWTAlgorithmError(
                f"Unsupported JWT algorithm: {algorithm}"
            )

        self.secret = secret
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_minutes = refresh_token_expire_minutes

    def _encode(self, data: dict[str, Any], delta_minutes: int) -> str:
        """
        Encode the payload into a JWT token.
        :param data: A dictionary containing user data.
        """
        # Verify that the data contains the `sub` field
        if "sub" not in data.keys():
            raise ValueError("The data must contain the 'sub' field.")
        now = current_time()
        data.update({"iat": now, "exp": now + timedelta(minutes=delta_minutes)})
        return _jwt.encode(data, self.secret, algorithm=self.algorithm.value)

    def _decode(self, token: str) -> dict[str, Any]:
        """
        Decode the JWT token and return the payload dictionary.
        :param token:
        :return:
        """
        try:
            return _jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm.value],
                options={"verify_exp": True, "require_iat": True},
            )
        except _jwt.ExpiredSignatureError:
            raise ExpiredTokenError
        except _jwt.InvalidTokenError:
            raise InvalidTokenError

    @staticmethod
    def _filter_data(
        data: dict[str, Any],
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Filter the data dictionary based on include and exclude lists.
        :param data: The original data dictionary.
        :param include: List of fields to include in the filtered data.
        :param exclude: List of fields to exclude from the filtered data.
        :return: Filtered data dictionary.
        """
        if include is not None:
            return {key: value for key, value in data.items() if key in include}
        elif exclude is not None:
            return {key: value for key, value in data.items() if key not in exclude}
        return data

    def _create_token(
        self,
        data: dict[str, Any],
        variant: Literal["access", "refresh"] = "access",
        sub_field: str = "id",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> str:
        """
        Create an access token for the user.
        :param data: A dictionary containing user data.
        :param sub_field: The field name to use as the subject (sub) in the token payload, default is "id".
        :param include: Include only these fields in the token payload.
        :param exclude: Exclude fields from the token payload.
        :return: JWT token as a string.
        """
        # Filter the data based on include and exclude lists
        filtered_data = self._filter_data(data, include, exclude)

        # Set the subject (sub) field if not already present
        if "sub" not in filtered_data:
            if sub_field not in data:
                raise ValueError(f"The data must contain the '{sub_field}' field.")
            filtered_data["sub"] = filtered_data[sub_field]

        # Create the token with a default expiration time
        if variant == "access":
            return self._encode(filtered_data, self.access_token_expire_minutes)
        elif variant == "refresh":
            return self._encode(filtered_data, self.refresh_token_expire_minutes)

        raise ValueError(
            f"Invalid token variant: {variant}. Must be 'access' or 'refresh'."
        )

    def create_access_token(
        self,
        data: dict[str, Any],
        sub_field: str = "id",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> str:
        """
        Create an access token for the user.
        :param sub_field:  The field name to use as the subject (sub) in the token payload, default is "id".
        :param data: A dictionary containing user data.
        :param include: Include only these fields in the token payload.
        :param exclude: Exclude fields from the token payload.
        :return: JWT token as a string.
        """
        return self._create_token(
            data, "access", sub_field=sub_field, include=include, exclude=exclude
        )

    def create_refresh_token(
        self,
        data: dict[str, Any],
        sub_field: str = "id",
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> str:
        """
        Create a refresh token for the user.
        :param sub_field: The field name to use as the subject (sub) in the token payload, default is "id".
        :param data: A dictionary containing user data.
        :param include: Include only these fields in the token payload.
        :param exclude: Exclude fields from the token payload.
        :return: JWT token as a string.
        """
        return self._create_token(
            data, "refresh", sub_field=sub_field, include=include, exclude=exclude
        )

    def decode_token(self, token: str) -> JWTTokenPayload:
        """This method decodes the JWT token and returns the payload."""
        return JWTTokenPayload(**self._decode(token))
