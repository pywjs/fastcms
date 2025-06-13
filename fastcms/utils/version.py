# fastcms/utils/version.py

import tomllib

from pathlib import Path


def get_pyproject_version(file: Path | str) -> str:
    """
    Reads the version from the pyproject.toml file.

    :param file: The path to the pyproject.toml file.
    :return: The version string from the pyproject.toml file.
    """
    if isinstance(file, str):
        file = Path(file)
    with open(file, "rb") as f:
        config = tomllib.load(f)
        version = config["project"]["version"]
        if not version:
            version = "0.0.0"
        return version
