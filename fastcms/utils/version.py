# fastcms/utils/version.py

import tomllib

from pathlib import Path


def get_pyproject_version(file: Path) -> str:
    """
    Reads the version from the pyproject.toml file.

    :param base_dir: The base directory where the pyproject.toml file is located.
    :return: The version string from the pyproject.toml file.
    """
    with open(file, "rb") as f:
        config = tomllib.load(f)
        version = config["project"]["version"]
        if not version:
            version = "0.0.0"
        return version
