"""
Wall test — a simple rectangular wall using the LLM-friendly API.

What is built:
- 5 × Brick1X2 wide (= 10 studs), 3 bricks high, facing north (Red)

Features exercised:
- Group with studs / plates / orientation constructor params
- piece.attach(side="right")  — horizontal brick chaining within a Group
- scene.add(facing=...)        — absolute placement with orientation
- scene.add(on_top_of=...)     — Group-level vertical stacking
- scene.piece_at()             — position query
"""

from pathlib import Path

from py4bricks.library.colours import Red
from py4bricks.library.parts.bricks import Brick1X2
from py4bricks.llm import Group, Scene
from py4bricks.pieces import Piece

WALL_WIDTH  = 5  # Brick1X2 pieces per row → 10 studs wide
WALL_HEIGHT = 3  # brick rows high


def make_row(width: int) -> Group:
    """Build a horizontal row of Brick1X2 bricks attached right-to-right."""
    row    = Group()
    anchor = Piece(part=Brick1X2, colour=Red)
    row.add(anchor)
    prev = anchor
    for _ in range(width - 1):
        brick = Piece(part=Brick1X2, colour=Red)
        prev.attach(piece=brick, side="right")
        prev = brick
    return row


scene = Scene()

rows = [make_row(WALL_WIDTH) for _ in range(WALL_HEIGHT)]

scene.add(rows[0], facing="north")
for i in range(1, WALL_HEIGHT):
    scene.add(rows[i], facing="north", on_top_of=rows[i - 1])

# bottom-left anchor sits at the origin
assert scene.piece_at(studs_x=0, plates_y=0, studs_z=0) is not None
# nothing at an out-of-bounds position
assert scene.piece_at(studs_x=99, plates_y=0, studs_z=0) is None

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Wall test rendered to wall_test.mpd")
