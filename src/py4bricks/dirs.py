"""data and config directories."""

from pathlib import Path

import platformdirs

from py4bricks.utils import ensure_exists

PY4BRICKS = "py4bricks"

def get_data_dir() -> Path:
    """Get the directory where to put some data."""
    return Path(__file__).parent.parent.parent / "data"


def get_user_data_dir() -> Path:
    """Get the user data directory where to put some data."""
    return Path(ensure_exists(platformdirs.user_data_dir(PY4BRICKS)))


def get_user_config_dir() -> Path:
    """Get the user configuration directory where the config is."""
    return Path(ensure_exists(platformdirs.user_config_dir(PY4BRICKS)))


def get_user_cache_dir() -> Path:
    """Get the user cache directory where cached files are stored."""
    return Path(ensure_exists(platformdirs.user_cache_dir(PY4BRICKS)))
