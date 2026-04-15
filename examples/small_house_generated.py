"""small_house_generated.py — A small house with two inner rooms.

House layout (top-down view, north is "up"):

   N  [==door==  north_wall  ==win==]  N
   W  |                               |  E
   e  |   (front room)                |  a
   s  |                               |  s
   t  [-------- inner_wall -|door|---]  t
      |                               |
      |   (back room)                 |
   W  |                               |  E
      [===win=== south_wall ==========]
                      S

Dimensions:
  - Footprint : HOUSE_WIDTH studs (E-W) × HOUSE_DEPTH studs (N-S)
  - Height    : HOUSE_HEIGHT bricks
  - Colours   : Tan exterior, Light_Grey inner wall
"""

from pathlib import Path

from py4bricks.geometry import Vector, proportional, studs_to_ldu
from py4bricks.library.colours import Dark_Blue, Light_Grey, Tan, White
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm.wall import Wall
from py4bricks.pieces import Piece

# ---------------------------------------------------------------------------
# House dimensions
# ---------------------------------------------------------------------------
HOUSE_WIDTH  = 16   # studs — east/west span (north and south wall length)
HOUSE_DEPTH  = 12   # studs — north/south span (east and west wall length)
HOUSE_HEIGHT =  7   # bricks

# ---------------------------------------------------------------------------
# North wall — front face: central door + two flanking windows
# ---------------------------------------------------------------------------
north_wall = Wall(
    name="north_wall",
    studs_width=HOUSE_WIDTH,
    bricks_height=HOUSE_HEIGHT,
    facing="north",
    colour=Tan,
)

# Door: centered, standing on the ground
north_wall.insert(
    Piece(colour=Dark_Blue, part=Door1X4X6Frame),
    at_studs_x=proportional(HOUSE_WIDTH, (1, 2)) - 2,  # center the 4-stud door
    at_bricks_y=0,
)

# Left window: 1 stud from the left edge, mid-height
north_wall.insert(
    Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
    at_studs_x=1,
    at_bricks_y=proportional(HOUSE_HEIGHT, (1, 2)),
)

# Right window: 1 stud from the right edge (16 - 4 - 1 = 11), mid-height
north_wall.insert(
    Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
    at_studs_x=HOUSE_WIDTH - 4 - 1,
    at_bricks_y=proportional(HOUSE_HEIGHT, (1, 2)),
)

# ---------------------------------------------------------------------------
# South wall — back face: one centred window
# ---------------------------------------------------------------------------
south_wall = Wall.from_references(
    name="south_wall",
    same_width_as=north_wall,
    same_height_as=north_wall,
    colour=Tan,
)
south_wall.place_parallel_to(other_wall=north_wall, distance_studs=-HOUSE_DEPTH)

south_wall.insert(
    Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
    at_studs_x=proportional(HOUSE_WIDTH, (1, 2)) - 2,
    at_bricks_y=proportional(HOUSE_HEIGHT, (1, 2)),
)

# ---------------------------------------------------------------------------
# Inner dividing wall — mid-depth, doorway opening in the centre
# ---------------------------------------------------------------------------
inner_wall = Wall.from_references(
    name="inner_wall",
    same_width_as=north_wall,
    same_height_as=north_wall,
    colour=Light_Grey,
)
inner_wall.place_parallel_to(other_wall=north_wall, distance_studs=-(HOUSE_DEPTH // 2))

# 4-stud doorway centred on the inner wall, floor-to-6-bricks tall
inner_wall.opening(
    at_studs_x=proportional(HOUSE_WIDTH, (1, 2)) - 2,
    studs_width=4,
    at_bricks_y=0,
    bricks_height=6,
)

# ---------------------------------------------------------------------------
# West wall — left side: one centred window
# ---------------------------------------------------------------------------
west_wall = Wall.from_dimensions(
    name="west_wall",
    studs_width=HOUSE_DEPTH,
    bricks_height=HOUSE_HEIGHT,
    colour=Tan,
)
west_wall.place(at=Vector(0, 0, 0), facing="west")

west_wall.insert(
    Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
    at_studs_x=proportional(HOUSE_DEPTH, (1, 2)) - 2,
    at_bricks_y=proportional(HOUSE_HEIGHT, (1, 2)),
)

# ---------------------------------------------------------------------------
# East wall — right side: one centred window
# ---------------------------------------------------------------------------
east_wall = Wall.from_dimensions(
    name="east_wall",
    studs_width=HOUSE_DEPTH,
    bricks_height=HOUSE_HEIGHT,
    colour=Tan,
)
# East wall originates at the SE corner; its local X extends toward the north (+Z in world)
east_wall.place(
    at=Vector(studs_to_ldu(HOUSE_WIDTH), 0, -studs_to_ldu(HOUSE_DEPTH)),
    facing="east",
)

east_wall.insert(
    Piece(colour=White, part=Window1X4X3WithoutShutterTabs),
    at_studs_x=proportional(HOUSE_DEPTH, (1, 2)) - 2,
    at_bricks_y=proportional(HOUSE_HEIGHT, (1, 2)),
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
output_path = Path(__file__).parent / "small_house_generated.mpd"
output_path.write_text("\n".join([
    repr(north_wall),
    repr(south_wall),
    repr(inner_wall),
    repr(west_wall),
    repr(east_wall),
]))
print(f"Written: {output_path}")
