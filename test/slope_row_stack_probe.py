"""Probe: Group-on-Group place_on_top_of with back_studs offset.

Verifies the assumption behind the planned _build_slope() refactor:
each "gable row" is a Group of slope pieces along the ridge, and
successive rows are stacked with `back_studs=1` to converge toward the peak.

Expected visual result: 3 rows of 3 small slope pieces, each row stepped
1 stud back (+Z) and 1 brick up from the row below. A clean 3-step
staircase facing north.
"""
from pathlib import Path

from py4bricks.library.colours import Red
from py4bricks.library.parts.slopes import SlopeBrick452X1
from py4bricks.llm import Scene
from py4bricks.llm.group import Group
from py4bricks.pieces import CustomPiece


def slope_piece() -> CustomPiece:
    # same construction as Roof._init_pieces.slope_piece_small
    return CustomPiece(
        part=SlopeBrick452X1,
        colour=Red,
        override_render_pos_offset=lambda p: {"z": p.ldu_z / 2},
    )


def build_row(num_pieces: int) -> Group:
    """One gable row: slope pieces laid along +X, all facing north."""
    row = Group()
    for i in range(num_pieces):
        row.place_at(slope_piece(), studs_x=i, plates_y=0, studs_z=0, facing="north")
    return row


scene = Scene("Slope row stack probe")

# Row 0 — bottom row at origin
row0 = build_row(3)
scene.place_at(row0, studs_x=0, plates_y=0, studs_z=0)

# Row 1 — stacked on row 0, offset 1 stud back toward the peak
row1 = build_row(3)
scene.place_on_top_of(row1, row0, back_studs=1, facing="north")

# Row 2 — stacked on row 1, same offset
row2 = build_row(3)
scene.place_on_top_of(row2, row1, back_studs=1, facing="north")

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Slope row stack probe rendered to slope_row_stack_probe.mpd")
