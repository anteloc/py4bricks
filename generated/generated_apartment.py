"""
# ============================================================
# APARTMENT BUILD PLAN
# ============================================================
#
# Layout (top view, X = east, Z = north):
#
#  z=49 ┌─────────────────────────────────────────────────────┐
#       │                                                     │
#       │              LIVING ROOM                           │
#       │         (60 studs wide × 30 studs deep)            │
#       │  [win N]                          [win N]          │
#  z=20 ├──────────────┬──────────────────────────────────────┤
#       │  KITCHEN     │      BATHROOM                       │
#       │  (30×20)     │      (30×20)                        │
#       │  [win W]     │      [win E]                        │
#  z=0  └──────────────┴──────────────────────────────────────┘
#         [door S] [win S]
#        x=0      x=30                                    x=60
#
# Exterior: 5 windows + 1 door
#   - south wall : 1 door (x≈6)  +  1 window (x≈38)
#   - north wall : 2 windows (x≈10 and x≈42)
#   - east  wall : 1 window (depth≈10)
#   - west  wall : 1 window (depth≈32)
#
# Interior dividers:
#   - living_divider  : east-west at z=20, 2 doorways (kitchen + bathroom)
#   - kitchen_bath_div: north-south at x=30, z=0..20 (solid wall)
#
# Parts:
#   Door1X4X6Frame               (4 studs wide, 6 bricks tall)
#   Window1X4X3WithoutShutterTabs (4 studs wide, 3 bricks tall)
#
# Colours:
#   Exterior walls    : Medium_Blue
#   Floor             : Dark_Tan
#   Living divider    : Salmon
#   Kitchen/bath div  : Light_Green
#   Windows           : Light_Blue
#   Door              : Reddish_Brown
#
# Build order (bottom-up):
#   1. Floor slab
#   2. Building body
#       a. Exterior box (all 4 walls, windows + door)
#       b. living_divider  (E-W, divider_wall from box["east"] → box["west"])
#       c. kitchen_bath_div (N-S, divider_wall from box["south"] → living_divider)
#   3. Body placed on top of floor slab
# ============================================================
"""
from pathlib import Path

from py4bricks.library.colours import (
    Dark_Tan,
    Light_Blue,
    Light_Green,
    Medium_Blue,
    Reddish_Brown,
    Salmon,
)
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Group, Scene, Slab, Wall
from py4bricks.pieces import Piece

# ── Dimensions ────────────────────────────────────────────────────────────────

APARTMENT_WIDTH  = 60   # studs east-west
APARTMENT_DEPTH  = 50   # studs north-south
WALL_HEIGHT      = 12   # bricks

# Z coordinate where living room starts (south rooms below, living room above)
SOUTH_DEPTH = 20        # studs

# X coordinate splitting kitchen (west) from bathroom (east)
SOUTH_SPLIT_X = APARTMENT_WIDTH // 2

# ── Part factories (each call returns a fresh Piece) ─────────────────────────

def make_window() -> Piece:
    return Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue)

def make_door() -> Piece:
    return Piece(part=Door1X4X6Frame, colour=Reddish_Brown)

# ── Exterior shell ────────────────────────────────────────────────────────────

def make_exterior() -> Box:
    """Closed 4-wall box with all exterior windows and the front door."""
    box = Box(
        width_studs=APARTMENT_WIDTH,
        length_studs=APARTMENT_DEPTH,
        height_bricks=WALL_HEIGHT,
        colour=Medium_Blue,
        bonded=True,
        name="exterior",
    )

    # South wall (left→right = west→east): front door + 1 window
    box["south"].insert(piece=make_door(),   studs_x=6,  brick_row=0)
    box["south"].insert(piece=make_window(), studs_x=38, brick_row=4)

    # North wall (left→right = east→west): 2 windows for living room
    box["north"].insert(piece=make_window(), studs_x=10, brick_row=4)
    box["north"].insert(piece=make_window(), studs_x=42, brick_row=4)

    # East wall (left→right = south→north): bathroom window
    box["east"].insert(piece=make_window(), studs_x=10, brick_row=4)

    # West wall (left→right = north→south): kitchen window
    box["west"].insert(piece=make_window(), studs_x=32, brick_row=4)

    return box

# ── Interior: living room divider ────────────────────────────────────────────

def make_living_divider(exterior: Box) -> Wall:
    """East-west wall at z=SOUTH_DEPTH; separates living room from south rooms.

    Derived from box["east"] ↔ box["west"]: position, rotation and length are
    all automatic. Two doorways: one per south room (kitchen + bathroom).
    """
    wall = Wall.divider_wall(
        from_wall=exterior["east"],
        at_width_studs=SOUTH_DEPTH,
        to_parallel_wall=exterior["west"],
        colour=Salmon,
        bonded=True,
    )
    # Kitchen doorway: centre of the west half (x=0..30)
    wall.opening(studs_x=13, brick_row=0, width_studs=4, height_bricks=6)
    # Bathroom doorway: centre of the east half (x=30..60)
    wall.opening(studs_x=43, brick_row=0, width_studs=4, height_bricks=6)
    return wall

# ── Interior: kitchen / bathroom divider ─────────────────────────────────────

def make_kitchen_bath_divider(exterior: Box, living_divider: Wall) -> Wall:
    """North-south wall at x=SOUTH_SPLIT_X; divides kitchen (west) from bathroom (east).

    Uses living_divider as the north boundary so the wall stops exactly there,
    rather than spanning the full apartment depth.
    """
    return Wall.divider_wall(
        from_wall=exterior["south"],
        at_width_studs=SOUTH_SPLIT_X,
        to_parallel_wall=living_divider,
        colour=Light_Green,
        bonded=True,
    )

# ── Floor ─────────────────────────────────────────────────────────────────────

def make_floor() -> Slab:
    return Slab(
        name="floor",
        width_studs=APARTMENT_WIDTH,
        length_studs=APARTMENT_DEPTH,
        colour=Dark_Tan,
    )

# ── Assemble scene ────────────────────────────────────────────────────────────

scene = Scene("Apartment")

# 1. Floor
slab_floor = make_floor()
scene.place_at(slab_floor, studs_x=0, plates_y=0, studs_z=0)

# 2. Building body: exterior + interior dividers
body = Group()

exterior = make_exterior()
body.add(exterior)

living_divider = make_living_divider(exterior)
body.add(living_divider)

body.add(make_kitchen_bath_divider(exterior, living_divider))

# 3. Place body on top of floor slab
scene.place_on_top_of(body, slab_floor)

# ── Render ────────────────────────────────────────────────────────────────────

output = Path("generated/generated_apartment.mpd")
output.parent.mkdir(exist_ok=True)
scene.render_file(output)
print(f"Apartment rendered to {output}")
