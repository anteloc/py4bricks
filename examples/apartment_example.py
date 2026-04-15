"""apartment_example.py — A roofless apartment for interior inspection.

Floor plan (top-down, north = top of page):

    W=0                X=12       X=20
    |--- Living/Kitchen ---|-- Bedroom --|   ← Z=0  (north outer wall)
    |                      |            |
    |                      |   [inner   |   ← Z=10 (inner E-W wall)
    |                      |  E-W wall] |
    |                      |  Bathroom  |
    |--- south outer wall (entry door) --|   ← Z=15 (south outer wall)

Outer walls:  Tan
Inner walls:  White
Windows:      Medium_Azure
Entry door:   Reddish_Brown
"""

from pathlib import Path

from py4bricks.geometry import Identity, Vector, studs_to_ldu
from py4bricks.library.colours import (
    Medium_Azure,
    Reddish_Brown,
    Tan,
    White,
)
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm.wall import Wall
from py4bricks.pieces import Piece

# ---------------------------------------------------------------------------
# Apartment dimensions
# ---------------------------------------------------------------------------
APARTMENT_WIDTH  = 20  # studs, east-west  (X axis)
APARTMENT_DEPTH  = 15  # studs, north-south (Z axis)
APARTMENT_HEIGHT = 10  # brick rows

LIVING_WIDTH  = 12   # studs — living/kitchen occupies the west 12 studs
LIVING_DEPTH  = 10   # studs — bedroom is separated from bathroom at Z=10
BEDROOM_WIDTH = APARTMENT_WIDTH - LIVING_WIDTH   # = 8 studs

# ---------------------------------------------------------------------------
# Outer walls
# ---------------------------------------------------------------------------

# North wall — back of the apartment; two windows looking outward
north_wall = Wall(
    studs_width=APARTMENT_WIDTH,
    bricks_height=APARTMENT_HEIGHT,
    position=Vector(0, 0, 0),
    facing="north",
    colour=Tan,
    name="north_wall",
)

# South wall — entry façade; starts at top-right corner from outside (south-facing
# local X runs in the -world-X direction, so origin is at world X = APARTMENT_WIDTH)
south_wall = Wall(
    same_width_as=north_wall,
    same_height_as=north_wall,
    position=Vector(studs_to_ldu(APARTMENT_WIDTH), 0, studs_to_ldu(APARTMENT_DEPTH)),
    facing="south",
    colour=Tan,
    name="south_wall",
)

# East wall — right side; bedroom window
east_wall = Wall(
    studs_width=APARTMENT_DEPTH,
    same_height_as=north_wall,
    position=Vector(studs_to_ldu(APARTMENT_WIDTH), 0, 0),
    facing="east",
    colour=Tan,
    name="east_wall",
)

# West wall — left side; living-room window
west_wall = Wall(
    studs_width=APARTMENT_DEPTH,
    same_height_as=north_wall,
    position=Vector(0, 0, studs_to_ldu(APARTMENT_DEPTH)),
    facing="west",
    colour=Tan,
    name="west_wall",
)

# ---------------------------------------------------------------------------
# Inner walls
# ---------------------------------------------------------------------------

# N-S dividing wall: living/kitchen (west) vs bedroom/bathroom (east).
# Placed LIVING_WIDTH studs inward along the west wall's face normal (+X world).
inner_ns_wall = Wall(
    studs_width=APARTMENT_DEPTH,
    same_height_as=north_wall,
    parallel_to=(west_wall, LIVING_WIDTH),
    colour=White,
    name="inner_ns_wall",
)

# E-W wall: bedroom (north of this wall) vs bathroom (south of this wall).
# Runs from the N-S dividing wall to the east outer wall (BEDROOM_WIDTH studs).
inner_ew_wall = Wall(
    studs_width=BEDROOM_WIDTH,
    same_height_as=north_wall,
    position=Vector(studs_to_ldu(LIVING_WIDTH), 0, studs_to_ldu(LIVING_DEPTH)),
    facing="north",
    colour=White,
    name="inner_ew_wall",
)

# ---------------------------------------------------------------------------
# Windows  (one Piece object per window insertion)
# ---------------------------------------------------------------------------

# North wall — living room (stud 2) and bedroom (stud 14), sill at 3 bricks up
win_n_living  = Piece(colour=Medium_Azure, position=Vector(0,0,0), rotation=Identity(), part=Window1X4X3WithoutShutterTabs)
win_n_bedroom = Piece(colour=Medium_Azure, position=Vector(0,0,0), rotation=Identity(), part=Window1X4X3WithoutShutterTabs)
north_wall.insert(win_n_living,  at_studs_x=2,  at_plates_y=9)
north_wall.insert(win_n_bedroom, at_studs_x=14, at_plates_y=9)

# East wall — bedroom window (3 studs from north end)
win_east = Piece(colour=Medium_Azure, position=Vector(0,0,0), rotation=Identity(), part=Window1X4X3WithoutShutterTabs)
east_wall.insert(win_east, at_studs_x=3, at_plates_y=9)

# West wall — living room / kitchen window (3 studs from south end in local space)
win_west = Piece(colour=Medium_Azure, position=Vector(0,0,0), rotation=Identity(), part=Window1X4X3WithoutShutterTabs)
west_wall.insert(win_west, at_studs_x=3, at_plates_y=9)

# ---------------------------------------------------------------------------
# Entry door — south wall, centred (stud 8 from east end in south-wall local space)
# ---------------------------------------------------------------------------
entry_door = Piece(colour=Reddish_Brown, position=Vector(0,0,0), rotation=Identity(), part=Door1X4X6Frame)
south_wall.insert(entry_door, at_studs_x=8, at_bricks_y=0)

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
all_walls = [north_wall, south_wall, east_wall, west_wall, inner_ns_wall, inner_ew_wall]
output = "\n".join(repr(w) for w in all_walls)
Path(Path(__file__).parent / "apartment_example.mpd").write_text(output)
