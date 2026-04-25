"""
APARTMENT PLAN
==============

Layout (top view, X=east, Z=north, Y=up):

    Z=30 (north)
    ┌────────────────────┬────────────────────┐
    │                    │    Bathroom         │
    │   Living Room      │  (X=20..40,        │
    │   (X=0..20,        │   Z=15..30)        │
    │    Z=0..30)        ├────────────────────┤
    │                    │    Kitchen         │
    │                    │  (X=20..40,        │
    │                    │   Z=0..15)         │
    └────────────────────┴────────────────────┘
    Z=0 (south/front)   X=20               X=40

Exterior: 40 studs wide (E-W) × 30 studs deep (N-S) × 10 bricks tall

Colours:
  exterior walls: Light_Grey (bonded)    interior walls: White
  floor: Tan                             windows: Light_Blue   door: Dark_Tan

Exterior openings (5 windows + 1 door):
  South wall (travels east, X=0→40):
    door    studs_x=4,  brick_row=0  (living room entrance, X=4..8)
    window1 studs_x=12, brick_row=4  (living room,          X=12..16)
    window2 studs_x=26, brick_row=4  (kitchen,              X=26..30)
  North wall (travels west, X=40→0):
    window3 studs_x=28, brick_row=4  (→ abs X=12..16 living room)
    window4 studs_x=10, brick_row=4  (→ abs X=30..34 kitchen)
  East wall (travels north, Z=0→30):
    window5 studs_x=4,  brick_row=4  (kitchen/bathroom, Z=4..8)

Interior walls:
  1. Living-room / east-section divider  — N-S wall at X=20, facing east
     doorway at studs_x=12, brick_row=0, 4 studs wide, 6 bricks tall
  2. Kitchen / bathroom divider          — E-W wall at Z=15, facing north
     doorway at studs_x=4,  brick_row=0, 4 studs wide, 6 bricks tall
"""

from pathlib import Path

from py4bricks.library.colours import Dark_Tan, Light_Blue, Light_Grey, Tan, White
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Scene, Wall
from py4bricks.llm.box import Box
from py4bricks.llm.slab import Slab
from py4bricks.pieces import Piece

# ── Dimensions ───────────────────────────────────────────────────────────────
APARTMENT_WIDTH  = 40   # studs, east-west  (X)
APARTMENT_DEPTH  = 30   # studs, north-south (Z)
APARTMENT_HEIGHT = 10   # bricks

EAST_SECTION_X   = 20   # X where east section (kitchen + bathroom) starts
BATHROOM_SPLIT_Z = 15   # Z where kitchen ends and bathroom begins

# Interior wall spans (inside the 1-stud-thick exterior walls)
INTERIOR_DEPTH   = APARTMENT_DEPTH - 2          # 28 studs along Z
INTERIOR_E_WIDTH = APARTMENT_WIDTH - EAST_SECTION_X - 1  # 19 studs along X

DOORWAY_WIDTH  = 4   # studs
DOORWAY_HEIGHT = 6   # bricks (matches Door1X4X6Frame height)

# ── Scene ────────────────────────────────────────────────────────────────────
scene = Scene()

# 1. Floor — 1 plate thick, ground level
floor = Slab(width_studs=APARTMENT_WIDTH, length_studs=APARTMENT_DEPTH, colour=Tan)
scene.place_at(floor, studs_x=0, plates_y=0, studs_z=0)

# 2. Exterior walls
box = Box(
    width_studs=APARTMENT_WIDTH,
    length_studs=APARTMENT_DEPTH,
    height_bricks=APARTMENT_HEIGHT,
    colour=Light_Grey,
    bonded=True,
)

# Exterior door — south wall, living room entrance
box["south"].insert(
    piece=Piece(part=Door1X4X6Frame, colour=Dark_Tan),
    studs_x=4,
    brick_row=0,
)

# Exterior windows — south wall: living room + kitchen
box["south"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=12,
    brick_row=4,
)
box["south"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=26,
    brick_row=4,
)

# Exterior windows — north wall: living room (abs X=12..16) + kitchen (abs X=30..34)
box["north"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=28,
    brick_row=4,
)
box["north"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=10,
    brick_row=4,
)

# Exterior window — east wall: kitchen/bathroom area (Z=4..8)
box["east"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=4,
    brick_row=4,
)

scene.place_on_top_of(box, floor)

# 3. Interior wall: living room / east-section divider (N-S, runs along Z)
divider_lr_east = Wall(
    width_studs=INTERIOR_DEPTH,
    height_bricks=APARTMENT_HEIGHT,
    colour=White,
    facing="east",
)
divider_lr_east.opening(
    studs_x=12,
    brick_row=0,
    width_studs=DOORWAY_WIDTH,
    height_bricks=DOORWAY_HEIGHT,
)
scene.place_at(divider_lr_east, studs_x=EAST_SECTION_X, plates_y=1, studs_z=1, facing="east")

# 4. Interior wall: kitchen / bathroom divider (E-W, runs along X)
divider_kit_bath = Wall(
    width_studs=INTERIOR_E_WIDTH,
    height_bricks=APARTMENT_HEIGHT,
    colour=White,
    facing="north",
)
divider_kit_bath.opening(
    studs_x=4,
    brick_row=0,
    width_studs=DOORWAY_WIDTH,
    height_bricks=DOORWAY_HEIGHT,
)
scene.place_at(
    divider_kit_bath,
    studs_x=EAST_SECTION_X + 1,
    plates_y=1,
    studs_z=BATHROOM_SPLIT_Z,
    facing="north",
)

# ── Render ───────────────────────────────────────────────────────────────────
output = Path(__file__).with_suffix(".mpd")
scene.render_file(output)
print(f"Apartment rendered to {output}")
