"""Command-line interface for py4bricks package.

Priamrily responsible for downloading LDraw library files and
generating the ldraw.library modules from them.
"""

import argparse
import logging
from pathlib import Path
import shutil
import sys

import yaml

from py4bricks import generate as do_generate
from py4bricks.config import Config
from py4bricks.downloads import download as do_download
from py4bricks.generation.exceptions import UnwritableOutputError


def generate() -> Config:
    """Generate the ldraw.library modules from downloaded LDraw parts."""
    rw_config = Config.load()

    try:
        do_generate(config=rw_config, force=True)
    except UnwritableOutputError as e:
        print(
            f"{rw_config.generated_path} is unwritable, select another out directory",
        )
        raise e

    return rw_config


def config():
    """Show py4bricks current configuration settings."""
    config = Config.load()
    print(yaml.dump(config.__dict__))


def download():
    """Download LDraw library files from the official repository."""
    release_id = do_download()
    print(f"Downloaded LDraw library files for release {release_id}")


def update(rw_config: Config):
    """Update the LDraw library files and regenerate the ldraw.library modules."""

    # TODO use the cached rw_config.ldraw_library_path to generate an ldraw.db 
    # with the dimensions for the parts, chunking for RAG, etc.

    gen_lib_path = Path(rw_config.generated_path) / "library"
    parts_lst_path = Path(rw_config.ldraw_library_path) / "ldraw" / "parts.lst"

    # move the generated library/ dir to this same cli parent dir for imports
    dst_lib_path = Path(__file__).parent / "library"
    if dst_lib_path.exists():
        shutil.rmtree(dst_lib_path)

    gen_lib_path.rename(dst_lib_path)

    shutil.copy(parts_lst_path, dst_lib_path / "parts.lst")

    print(f"Updated library at: '{dst_lib_path}'")
    print("""**NOTE**: if the current data/ldraw.db is outdated,
          you may need to re-create it (WIP) with the dimensions
          for the new parts to avoid missing dimensions for new parts.""")


def main():
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="py4bricks",
        description="py4bricks - LDraw/LEGO library for LLM generation of LDraw models",
        epilog="Example: py4bricks --update"
    )

    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help=(
            "Download the official LDraw library part files and generate "
            "py4bricks.library modules from them"
        ),
    )

    parser.add_argument(
        "-c", "--config",
        action="store_true",
        help="Show current configuration",
    )

    args = parser.parse_args()

    # If no arguments provided, show help
    if not any([args.update, args.config]):
        parser.print_help()
        sys.exit(0)

    if args.update:
        download()
        rw_config = generate()
        update(rw_config)
    elif args.config:
        config()

if __name__ == "__main__":
    main()
