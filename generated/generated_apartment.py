"""
Apartment Layout Plan
=====================

Top view (X right, Z back, Y up):

   x=0        x=20           x=40
   z=0  +-----+--------------+
        |Bath |              |
        |     |   Living     |
   z=20 +-----+    Room      |
        |     |              |
        |Kitch|              |
   z=30 +-----+--------------+

Footprint : 40 studs wide (X) × 30 studs deep (Z)
Height    : 10 bricks

Rooms:
  Bathroom  — x=0..20, z=0..20   (northwest)
  Kitchen   — x=0..20, z=20..30  (southwest)
  Living Rm — x=20..40, z=0..30  (east half)

Interior walls (White, 10 bricks, non-bonded):
  Wall B: north-south divider at x=20, 30 studs long, facing east
  Wall A: east-west divider at z=20, 20 studs long, facing north

Exterior (Light_Grey, bonded, 10 bricks):
  South: 1 door (center, ground level) + 2 windows (brick_row=4)
  North: 1 window
  East : 1 window
  West : 1 window
  Total: 5 exterior windows + 1 exterior door

Colors:
  Floor         : Tan
  Exterior walls: Light_Grey
  Interior walls: White
  Windows       : Light_Blue
  Door          : Tan
"""

from pathlib import Path

from py4bricks.library.colours import Light_Blue, Light_Grey, Tan, White
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Scene, Wall
from py4bricks.llm.box import Box
from py4bricks.llm.slab import Slab
from py4bricks.pieces import Piece

scene = Scene()

# --- Floor ---
floor = Slab(width_studs=40, length_studs=30, colour=Tan)
scene.place_at(floor, studs_x=0, plates_y=0, studs_z=0)

# --- Exterior walls ---
exterior = Box(
    width_studs=40,
    length_studs=30,
    height_bricks=10,
    colour=Light_Grey,
    bonded=True,
)

# South wall: entrance door (center) + 2 windows (kitchen side and living room side)
exterior["south"].insert(
    piece=Piece(part=Door1X4X6Frame, colour=Tan),
    studs_x=18,
    brick_row=0,
)
exterior["south"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=5,
    brick_row=4,
)
exterior["south"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=30,
    brick_row=4,
)

# North wall: 1 window into living room
exterior["north"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=15,
    brick_row=4,
)

# East wall: 1 window into living room
exterior["east"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=10,
    brick_row=4,
)

# West wall: 1 window into bathroom / kitchen
exterior["west"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=5,
    brick_row=4,
)

scene.place_on_top_of(exterior, floor)

# --- Interior wall B: north-south divider at x=20 (east/west room split) ---
wall_b = Wall(width_studs=30, height_bricks=10, colour=White)
scene.place_on_top_of(wall_b, floor, right_studs=20, facing="east")

# --- Interior wall A: east-west divider at z=20 (bathroom / kitchen split) ---
wall_a = Wall(width_studs=20, height_bricks=10, colour=White)
scene.place_on_top_of(wall_a, floor, back_studs=20, facing="north")

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Apartment rendered to generated_apartment.mpd")
