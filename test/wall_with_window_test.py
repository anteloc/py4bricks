"""
Wall with window and door test.

Wall: 40 studs wide, 35 bricks high, non-bonded (rows parallel, joints aligned).

Openings are carved by removing bricks, then the frame piece fills the gap:
    - Window1X4X3 at studs 8-11, rows 16-18  (mid-height, left of centre)
    - Door1X4X6   at studs 20-23, rows 0-5   (ground level, right of centre)
"""

from pathlib import Path

from py4bricks.library.colours import Light_Blue, Light_Grey, Tan
from py4bricks.library.parts.bricks import Brick1X2
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Group, Scene
from py4bricks.pieces import Piece

# --- wall dimensions ---
WALL_WIDTH       = 40   # studs
WALL_HEIGHT      = 35   # brick rows
BRICKS_PER_ROW   = WALL_WIDTH // 2        # 20 × Brick1X2 per row
PLATES_PER_BRICK = 3

# --- opening positions ---
WINDOW_STUDS  = 8    # leftmost stud of the window opening
WINDOW_ROW    = 16   # bottom row of the window opening
WINDOW_WIDTH  = 4    # studs  (matches 1X4 in part name)
WINDOW_ROWS   = 3    # brick rows (matches X3 in part name)

DOOR_STUDS    = 20   # leftmost stud of the door opening
DOOR_ROW      = 0    # ground floor
DOOR_WIDTH    = 4    # studs  (matches 1X4 in part name)
DOOR_ROWS     = 6    # brick rows (matches X6 in part name)


def make_row() -> Group:
    """One full-width row of Brick1X2 pieces."""
    row    = Group()
    anchor = Piece(part=Brick1X2, colour=Light_Grey)
    row.add(anchor)
    prev = anchor
    for _ in range(BRICKS_PER_ROW - 1):
        brick = Piece(part=Brick1X2, colour=Light_Grey)
        prev.attach(piece=brick, side="right")
        prev = brick
    return row


scene = Scene()

# --- build the solid wall ---
rows = [make_row() for _ in range(WALL_HEIGHT)]
scene.place(rows[0], facing="north")
for i in range(1, WALL_HEIGHT):
    scene.place_on_top_of(rows[i], rows[i - 1], facing="north")

# --- carve window opening: remove 2 bricks × 3 rows ---
for row_i in range(WINDOW_ROW, WINDOW_ROW + WINDOW_ROWS):
    for stud_x in range(WINDOW_STUDS, WINDOW_STUDS + WINDOW_WIDTH, 2):
        assert rows[row_i].remove_piece_at(studs_x=stud_x, plates_y=0, studs_z=0) is not None

# --- carve door opening: remove 2 bricks × 6 rows ---
for row_i in range(DOOR_ROW, DOOR_ROW + DOOR_ROWS):
    for stud_x in range(DOOR_STUDS, DOOR_STUDS + DOOR_WIDTH, 2):
        assert rows[row_i].remove_piece_at(studs_x=stud_x, plates_y=0, studs_z=0) is not None

# --- place frames at the carved openings ---
window = Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue)
scene.place_at(
    piece=window,
    studs_x=WINDOW_STUDS,
    plates_y=WINDOW_ROW * PLATES_PER_BRICK,
    studs_z=0,
)

door = Piece(part=Door1X4X6Frame, colour=Tan)
scene.place_at(
    piece=door,
    studs_x=DOOR_STUDS,
    plates_y=DOOR_ROW * PLATES_PER_BRICK,
    studs_z=0,
)

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Wall with window test rendered to wall_with_window_test.mpd")
