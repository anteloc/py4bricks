"""big_house_generated.py — A large house with four inner rooms.

Top-down layout (N = top):

  [door door ===== north_wall(24) ===== win  win]
  |                    |                        |
  |     NW room        |       NE room          |
  |                    |                        |
  [=== inner_wall_ns =[door]====[door]= inner_ns]
  |                    |                        |
  |     SW room        |       SE room          |
  |                    |                        |
  [win  win ====== south_wall(24) ====== win  win]

  inner_wall_ew runs full depth at the mid-width (x = HOUSE_WIDTH // 2).
  It carries one doorway in the front half and one in the back half.

Dimensions:
  - Footprint : HOUSE_WIDTH studs (E-W) × HOUSE_DEPTH studs (N-S)
  - Height    : HOUSE_HEIGHT bricks
  - Colours   : Light_Blue exterior · White inner walls · Dark_Blue doors
"""

from pathlib import Path

from py4bricks.geometry import Vector, proportional, studs_to_ldu
from py4bricks.library.colours import Dark_Blue, Light_Blue, White
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm.wall import Wall
from py4bricks.pieces import Piece

# ---------------------------------------------------------------------------
# House dimensions
# ---------------------------------------------------------------------------
HOUSE_WIDTH  = 24   # studs — east/west span
HOUSE_DEPTH  = 20   # studs — north/south span
HOUSE_HEIGHT = 10   # bricks

# Derived landmarks (no magic numbers elsewhere)
HALF_WIDTH  = HOUSE_WIDTH  // 2   # 12 — east/west mid-line
HALF_DEPTH  = HOUSE_DEPTH  // 2   # 10 — north/south mid-line
HALF_HEIGHT = HOUSE_HEIGHT // 2   #  5 — mid-height (window row)

# ---------------------------------------------------------------------------
# North wall — front face: double door (centre) + one window per side zone
# ---------------------------------------------------------------------------
north_wall = Wall(
    name="north_wall",
    studs_width=HOUSE_WIDTH,
    bricks_height=HOUSE_HEIGHT,
    facing="north",
    colour=Light_Blue,
)

# Double door: two 4-stud frames side by side, centred on the wall
north_wall.insert(
    Piece(colour=Dark_Blue, part=Door1X4X6Frame),
    at_studs_x=HALF_WIDTH - 4,   # left door: ends at centre
    at_bricks_y=0,
)
north_wall.insert(
    Piece(colour=Dark_Blue, part=Door1X4X6Frame),
    at_studs_x=HALF_WIDTH,        # right door: starts at centre
    at_bricks_y=0,
)

# Left window: in the left zone, mid-height
north_wall.insert(
    Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
    at_studs_x=proportional(HOUSE_WIDTH, (1, 8)),      # ≈ stud 3
    at_bricks_y=HALF_HEIGHT,
)

# # Right window: symmetric with left window
north_wall.insert(
    Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
    at_studs_x=proportional(HOUSE_WIDTH, (3, 4)),      # ≈ stud 18
    at_bricks_y=HALF_HEIGHT,
)

# ---------------------------------------------------------------------------
# South wall — back face: three windows spread evenly
# ---------------------------------------------------------------------------
south_wall = Wall.from_references(
    name="south_wall",
    same_width_as=north_wall,
    same_height_as=north_wall,
    colour=Light_Blue,
)
south_wall.place_parallel_to(other_wall=north_wall, distance_studs=-HOUSE_DEPTH)

for studs_x in (
    proportional(HOUSE_WIDTH, (1, 8)),      # left zone  ≈ 3
    HALF_WIDTH - 2,                          # centre     = 10
    proportional(HOUSE_WIDTH, (3, 4)),      # right zone ≈ 18
):
    south_wall.insert(
        Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
        at_studs_x=studs_x,
        at_bricks_y=HALF_HEIGHT,
    )

# ---------------------------------------------------------------------------
# Inner N-S wall — runs east/west at mid-depth; two doorways (one per side half)
# ---------------------------------------------------------------------------
inner_wall_ns = Wall.from_references(
    name="inner_wall_ns",
    same_width_as=north_wall,
    same_height_as=north_wall,
    colour=White,
)
inner_wall_ns.place_parallel_to(other_wall=north_wall, distance_studs=-HALF_DEPTH)

# Doorway in the left half (NW↔SW), doorway in the right half (NE↔SE)
for door_x in (
    proportional(HOUSE_WIDTH, (1, 4)) - 2,   # ≈ stud 4
    proportional(HOUSE_WIDTH, (3, 4)) - 2,   # ≈ stud 16
):
    inner_wall_ns.opening(
        at_studs_x=door_x,
        studs_width=4,
        at_bricks_y=0,
        bricks_height=6,
    )

# ---------------------------------------------------------------------------
# Inner E-W wall — runs north/south at mid-width; two doorways (one per depth half)
# ---------------------------------------------------------------------------
inner_wall_ew = Wall.from_dimensions(
    name="inner_wall_ew",
    studs_width=HOUSE_DEPTH,
    bricks_height=HOUSE_HEIGHT,
    colour=White,
)
# East-facing: local X → world +Z; origin at SE corner of this wall span
inner_wall_ew.place(
    at=Vector(studs_to_ldu(HALF_WIDTH), 0, -studs_to_ldu(HOUSE_DEPTH)),
    facing="east",
)

# Doorway in the front half (NW↔NE), doorway in the back half (SW↔SE)
for door_x in (
    proportional(HOUSE_DEPTH, (1, 4)) - 2,   # ≈ stud 3 (front)
    proportional(HOUSE_DEPTH, (3, 4)) - 2,   # ≈ stud 13 (back)
):
    inner_wall_ew.opening(
        at_studs_x=door_x,
        studs_width=4,
        at_bricks_y=0,
        bricks_height=6,
    )

# ---------------------------------------------------------------------------
# West wall — left side: two windows (front and back halves)
# ---------------------------------------------------------------------------
west_wall = Wall.from_dimensions(
    name="west_wall",
    studs_width=HOUSE_DEPTH,
    bricks_height=HOUSE_HEIGHT,
    colour=Light_Blue,
)
west_wall.place(at=Vector(0, 0, 0), facing="west")

for studs_x in (
    proportional(HOUSE_DEPTH, (1, 4)),   # front-zone window  ≈ stud 5
    proportional(HOUSE_DEPTH, (3, 4)),   # back-zone window   ≈ stud 15
):
    west_wall.insert(
        Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
        at_studs_x=studs_x,
        at_bricks_y=HALF_HEIGHT,
    )

# ---------------------------------------------------------------------------
# East wall — right side: mirrors west wall
# ---------------------------------------------------------------------------
east_wall = Wall.from_references(
    name="east_wall",
    same_width_as=west_wall,
    same_height_as=west_wall,
    colour=Light_Blue,
)
# East-facing: origin at SE corner, local X extends northward (+Z world)
east_wall.place(
    at=Vector(studs_to_ldu(HOUSE_WIDTH), 0, -studs_to_ldu(HOUSE_DEPTH)),
    facing="east",
)

for studs_x in (
    proportional(HOUSE_DEPTH, (1, 4)),
    proportional(HOUSE_DEPTH, (3, 4)),
):
    east_wall.insert(
        Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
        at_studs_x=studs_x,
        at_bricks_y=HALF_HEIGHT,
    )

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
output_path = Path(__file__).parent / "big_house_generated.mpd"
output_path.write_text("\n".join([
    repr(north_wall),
    repr(south_wall),
    repr(inner_wall_ns),
    repr(inner_wall_ew),
    repr(west_wall),
    repr(east_wall),
]))
print(f"Written: {output_path}")
