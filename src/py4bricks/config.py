"""takes care of reading and writing a configuration in config.yml."""

import argparse
import os
from pathlib import Path

import yaml

from py4bricks.dirs import (
    get_data_dir,
    get_user_cache_dir,
    get_user_config_dir,
    get_user_data_dir,
)
from py4bricks.errors import InvalidConfigFileError

CONFIG_FILE = get_user_config_dir() / "config.yml"


def is_valid_config_file(parser, arg):  # noqa: ARG001
    """Validate that the given config file exists and is valid YAML."""
    if not os.path.exists(arg):
        raise FileNotFoundError(arg)
    with open(arg) as f:
        if yaml.load(f, Loader=yaml.SafeLoader) is None:
            raise InvalidConfigFileError(arg)
    return arg


parser = argparse.ArgumentParser()
parser.add_argument("--config", type=lambda x: is_valid_config_file(parser, x))


def get_config(config_file: str | None = None) -> Path:
    """Get the path to the configuration file, either from arguments or default."""
    if config_file is None:
        args, unknown = parser.parse_known_args()
        return Path(args.config) if args.config is not None else CONFIG_FILE
    return Path(config_file)
    

class Config:
    """Configuration settings for py4bricks."""

    ldraw_library_path: Path
    generated_path: Path
    parts_db_path: Path

    def __init__(
        self,
        ldraw_library_path: Path | None = None,
        generated_path: Path | None = None,
        parts_db_path: Path | None = None,
    ):
        self.ldraw_library_path = (
            ldraw_library_path
            if ldraw_library_path is not None
            else get_user_cache_dir() / "complete"
        )
        self.generated_path = (
            generated_path
            if generated_path is not None
            else get_user_data_dir() / "generated"
        )
        self.parts_db_path = (
            parts_db_path
            if parts_db_path is not None
            else get_data_dir() / "ldraw.db"
        )

    @classmethod
    def load(cls, config_file: str | None = None) -> "Config":
        """Load configuration from YAML file or create default configuration."""
        config_path = get_config(config_file)

        try:
            with open(config_path) as _config_file:
                cfg = yaml.load(_config_file, Loader=yaml.SafeLoader)
                return cls(
                    # pyrefly: ignore  # missing-attribute  # noqa: ERA001
                    ldraw_library_path=cfg.get("ldraw_library_path"),
                    # pyrefly: ignore  # missing-attribute  # noqa: ERA001
                    generated_path=cfg.get("generated_path"),
                    # pyrefly: ignore  # missing-attribute  # noqa: ERA001
                    parts_db_path=cfg.get("parts_db_path"),
                )
        except FileNotFoundError:
            return cls()

    def __str__(self):
        return f"Config({self.ldraw_library_path=}, {self.generated_path=}, {self.parts_db_path=})"

    def write(self, config_file=None):
        """Write the config to config.yml."""
        config_path = get_config(config_file=config_file)

        with open(config_path, "w") as _config_file:
            written = {}
            if self.ldraw_library_path is not None:
                written["ldraw_library_path"] = str(self.ldraw_library_path)
            if self.generated_path is not None:
                written["generated_path"] = str(self.generated_path)
            if self.parts_db_path is not None:
                written["parts_db_path"] = str(self.parts_db_path)

            yaml.dump(written, _config_file)
