"""Called by ldraw.library_gen to generate the ldraw/library/colours.py file."""

import codecs
import os
from pathlib import Path

# TODO replace pystache with chevron elsewhere and remove dependency on pystache
# import pystache
import chevron

from py4bricks.colour import Colour
from py4bricks.geometry import LDU_PER_PLATE, LDU_PER_STUD
from py4bricks.parts import Parts
from py4bricks.resources import _get_resource_content
from py4bricks.utils import camel, class_name, clean

import sqlite3
from math import ceil

TMP_TABLE_SQL = """CREATE TEMP TABLE ALIASES_FROM_CODES (
    alias VARCHAR PRIMARY KEY
);
"""

DIMENSIONS_JOIN_SQL = """SELECT
    pbb.alias as alias,
    pbb.dim_x as ldu_x,
    pbb.dim_y as ldu_y,
    pbb.dim_z as ldu_z
    FROM PART_BBOXES pbb
    INNER JOIN ALIASES_FROM_CODES afc ON pbb.alias = afc.alias
    WHERE pbb.complete = 'true';
"""

def gen_dimensions(parts: Parts, library_path: Path, db_path: Path):
    """Generate a dimensions.py from a parts database."""
    print("Generating py4bricks.library.dimensions...")

    parts_by_code = parts.by_code

    conn = connect_db(db_path)
    populate_tmp_table(conn, parts_by_code)
    db_dimensions = query_dimensions(conn)
    conn.close()

    print(f"Got dimensions for {len(db_dimensions)} parts from the database")

    dimensions_ctx = dimensions_module_context(parts_by_code, db_dimensions)
    dimensions_mustache = Path(__file__).parent.parent / "templates" / "dimensions.mustache"
    dimensions_py = library_path / "dimensions.py"

    with open(dimensions_mustache) as template:
        dimensions_py.write_text(chevron.render(template, dimensions_ctx))

def connect_db(db_path: Path) -> sqlite3.Connection:
    """Return a connection to the SQLite database at the given path."""
    conn = sqlite3.connect(db_path.as_posix())
    conn.row_factory = sqlite3.Row  # This allows us to get results as dictionaries

    return conn

def populate_tmp_table(conn: sqlite3.Connection, parts_by_code: dict[str, str]):
    """Populate the temporary table with aliases from the parts database."""
    cursor = conn.cursor()
    cursor.execute(TMP_TABLE_SQL)

    for code in parts_by_code:
        cursor.execute("INSERT INTO aliases_from_codes (alias) VALUES (?)",
                       (f"{code}.dat",))

    conn.commit()
    cursor.close()

def query_dimensions(conn: sqlite3.Connection) -> dict[str, dict]:
    """Query the SQLite database and return results as a list of dictionaries."""
    cursor = conn.cursor()

    cursor.execute(DIMENSIONS_JOIN_SQL)
    rows = cursor.fetchall()

    # Strip .dat ext from alias to get code -> dimensions dict
    results = {row["alias"][:-4]: dict(row) for row in rows}

    cursor.close()
    return results


def dimensions_module_context(parts_by_code: dict[str, str], db_dimensions: dict[str, dict]) -> dict[str, list[dict]]:
    """Generate the contents of the dimensions.py module from parts data."""
    context = {"dimensions": [
        get_d_dict(code, parts_by_code[code], db_dimensions[code]) 
        for code in db_dimensions]}
    context["dimensions"].sort(key=lambda r: r["class_name"])
    return context


def get_d_dict(code: str, part_desc: str, part_dims: dict[str, float]) -> dict:
    """Build a dict with dimensions info for a part."""
    ldu_x = part_dims["ldu_x"]
    ldu_y = part_dims["ldu_y"]
    ldu_z = part_dims["ldu_z"]
    # Round to the highest integer: studs and plates are always whole numbers,
    # if a part is 1.4 studs long, it should be considered 2 studs long
    # for collision purposes
    studs_x = ceil(ldu_x / LDU_PER_STUD)
    studs_y = ceil(ldu_y / LDU_PER_STUD)
    plates_y = ceil(ldu_y / LDU_PER_PLATE)
    studs_z = ceil(ldu_z / LDU_PER_STUD)

    return {
        "code": code,
        "class_name": class_name(part_desc),
        "ldu_x": ldu_x,
        "ldu_y": ldu_y,
        "ldu_z": ldu_z,
        "studs_x": studs_x,
        "studs_y": studs_y,
        "plates_y": plates_y,
        "studs_z": studs_z,
    }
