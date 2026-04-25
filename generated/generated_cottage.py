"""
# ============================================================
# COTTAGE BUILD PLAN
# ============================================================
#
# "Stone Cottage" — a small two-room rural dwelling.
#
# Exterior dimensions: 20 studs wide (E-W) × 28 studs deep (N-S)
# Wall height: 8 bricks  |  Roof: red, ridge running N-S
#
# Floor plan (top view):
#
#  z=27 ┌─────────────────────┐
#       │    BEDROOM          │
#       │   (20 × 14 studs)   │  [win N]  [win N]
#  z=14 ├──────────────────────┤  ← bedroom_divider (with doorway)
#       │    LIVING ROOM      │
#       │   (20 × 14 studs)   │
#       │  [win W]   [win E]  │
#  z=0  └─────────────────────┘
#         [win]  [door]  [win]    ← south facade
#
# Exterior openings:
#   South wall : 2 windows flanking the front door
#   North wall : 2 windows (bedroom garden view)
#   East  wall : 1 window  (living room side light)
#   West  wall : 1 window  (living room side light)
#   Total: 6 exterior windows + 1 front door
#
# Interior:
#   Bedroom divider: E-W wall at z=14 with a central doorway
#
# Colours:
#   Exterior walls  : Tan         (warm stone)
#   Bedroom divider : White       (clean plaster)
#   Floor           : Reddish_Brown (dark wood)
#   Windows         : Light_Blue
#   Front door      : Dark_Tan    (aged oak)
#   Roof            : Red
#
# Build order (bottom-up):
#   1. Floor slab
#   2. Building body
#       - Exterior box
#       - Interior bedroom divider wall
#   3. Building with roof
#       - Roof on top of body
# ============================================================
"""
from math import floor
from pathlib import Path

from py4bricks.library.colours import (
    Dark_Tan,
    Light_Blue,
    Red,
    Reddish_Brown,
    Tan,
    White,
)
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Roof, Scene, Slab, Wall, Group
from py4bricks.pieces import Piece

# ── Dimensions ────────────────────────────────────────────────────────────────

COTTAGE_WIDTH  = 20   # studs east-west
COTTAGE_DEPTH  = 28   # studs north-south
WALL_HEIGHT    = 8    # bricks

# Interior partition: bedroom starts at this Z
BEDROOM_Z = 14        # studs

# ── Part factories ────────────────────────────────────────────────────────────

def make_window() -> Piece:
    return Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue)

def make_door() -> Piece:
    return Piece(part=Door1X4X6Frame, colour=Dark_Tan)

# ── Exterior shell ────────────────────────────────────────────────────────────

def make_exterior() -> Box:
    """Stone cottage exterior with all windows and the front door."""
    box = Box(
        name="cottage_exterior",
        width_studs=COTTAGE_WIDTH,
        length_studs=COTTAGE_DEPTH,
        height_bricks=WALL_HEIGHT,
        colour=Tan,
        bonded=True,
    )

    # South wall (travels east, studs_x 0=west): front door centred + side windows
    box["south"].insert(piece=make_door(),   studs_x=8,  brick_row=0)
    box["south"].insert(piece=make_window(), studs_x=2,  brick_row=4)
    box["south"].insert(piece=make_window(), studs_x=13, brick_row=4)

    # North wall (travels west, studs_x 0=east): bedroom garden windows
    box["north"].insert(piece=make_window(), studs_x=2,  brick_row=4)
    box["north"].insert(piece=make_window(), studs_x=13, brick_row=4)

    # East wall (travels north, studs_x 0=south): living room side window
    box["east"].insert(piece=make_window(), studs_x=5, brick_row=4)

    # West wall (travels south, studs_x 0=north): living room side window
    box["west"].insert(piece=make_window(), studs_x=5, brick_row=4)

    return box

# ── Interior: bedroom divider ─────────────────────────────────────────────────

def make_bedroom_divider(exterior: Box) -> Wall:
    """E-W interior wall separating bedroom from living room.

    Placed at z=BEDROOM_Z; a central doorway connects the two rooms.
    """
    wall = Wall.divider_wall(
        from_wall=exterior["east"],
        at_width_studs=BEDROOM_Z,
        to_parallel_wall=exterior["west"],
        colour=White,
        bonded = True,
    )

    # Central doorway (4 studs wide, 6 bricks tall)
    wall.opening(studs_x=8, brick_row=0, width_studs=4, height_bricks=6)
    return wall


# ── Floor ─────────────────────────────────────────────────────────────────────

def make_floor() -> Slab:
    return Slab(
        name="floor",
        width_studs=COTTAGE_WIDTH,
        length_studs=COTTAGE_DEPTH,
        colour=Reddish_Brown,
    )

# ── Scene assembly ────────────────────────────────────────────────────────────

scene = Scene("Stone Cottage")

# 1. Floor
slab_floor = make_floor()
scene.place_at(slab_floor, studs_x=0, plates_y=0, studs_z=0)

# 2. Building body
body = Group()

exterior = make_exterior()
body.add(exterior)

bedroom_divider = make_bedroom_divider(exterior)
body.add(bedroom_divider)


# 3. Building with roof
roof = Roof(
    name="cottage_roof",
    width_studs=exterior.width_studs,
    length_studs=exterior.length_studs,
    ridge_running="north-south",
    colour=Red,
)

body_with_roof = Group()
body_with_roof.add(body)
body_with_roof.place_on_top_of(roof, body)

# Place everything on the floor slab
scene.place_on_top_of(body_with_roof, slab_floor)

# ── Render ────────────────────────────────────────────────────────────────────

output = Path("generated/generated_cottage.mpd")
output.parent.mkdir(exist_ok=True)
scene.render_file(output)
print(f"Cottage rendered to {output}")
