"""Module tasked with generating python files for the ldraw.library namespace."""

import hashlib
import logging
import os
import shutil
from pathlib import Path

from py4bricks.config import Config
from py4bricks.generation.colours import gen_colours
from py4bricks.generation.dimensions import gen_dimensions
from py4bricks.generation.parts import gen_parts
from py4bricks.parts import Parts
from py4bricks.resources import _get_resource, _get_resource_content
from py4bricks.utils import ensure_exists

logger = logging.getLogger("ldraw")


def generate(config: Config, *, force=False):
    """Generate the library from configuration."""
    generated_library_path = config.generated_path / "library"
    ensure_exists(generated_library_path.as_posix())

    hash_path = generated_library_path / "__hash__"

    library_path = config.ldraw_library_path

    parts_lst = library_path / "ldraw" / "parts.lst"
    md5_parts_lst = hashlib.md5(parts_lst.read_bytes()).hexdigest()

    if hash_path.exists():
        md5 = hash_path.read_text()
        if md5 == md5_parts_lst and not force:
            logger.error(
                "Path %s already generated (checksums match)",
                generated_library_path,
            )
            return

    # pyrefly: ignore  # deprecated  # noqa: ERA001
    shutil.rmtree(generated_library_path)
    ensure_exists(generated_library_path.as_posix())

    parts = Parts(parts_lst)

    library__init__ = generated_library_path / "__init__.py"

    with open(library__init__, "w") as library__init__:
        library__init__.write(LIBRARY_INIT)

    shutil.copy(
        _get_resource("ldraw-license.txt"),
        generated_library_path / "license.txt",
    )

    gen_colours(parts, generated_library_path)
    gen_parts(parts, generated_library_path)
    gen_dimensions(parts, generated_library_path, config.parts_db_path)

    hash_path.write_text(md5_parts_lst)


LIBRARY_INIT = _get_resource_content(os.path.join("templates", "py4bricks__init__"))
