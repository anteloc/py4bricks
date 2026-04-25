"""
# ============================================================
# HUGE COTTAGE BUILD PLAN
# ============================================================
#
# "Grand Country Cottage" — a spacious four-room manor cottage.
#
# Exterior: 60 studs wide (E-W) × 80 studs deep (N-S) × 14 bricks tall
#
# Floor plan (top view):
#
#  z=79 ┌──────────────────────────────────────────────────────────┐
#       │                │                                         │
#       │  BEDROOM 1     │       BEDROOM 2                        │
#       │  (30 × 35)     │       (30 × 35)                        │
#       │  [win W]       │  [win N][win N]        [win E]         │
#  z=45 ├────────────────┼─────────────────────────────────────────┤ ← room_divider
#       │                │                                         │
#       │  KITCHEN       │       LIVING ROOM                      │
#       │  (30 × 45)     │       (30 × 45)                        │
#       │  [win W]       │  [win S][win S]        [win E]         │
#  z=0  └──────────────────────────────────────────────────────────┘
#                [door S]      [win S]
#               x=0            x=30                             x=60
#                    ↑
#              wing_divider (N-S, full depth)
#
# Exterior openings (13 windows + 1 front door):
#   South wall (59 studs): 1 door + 3 windows
#   North wall (59 studs): 3 windows
#   East  wall (79 studs): 3 windows
#   West  wall (79 studs): 3 windows
#
# Interior dividers:
#   room_divider : E-W wall at z=45, 2 doorways (kitchen→bed1, living→bed2)
#   wing_divider : N-S wall at x=30 full depth, 2 doorways (kitchen↔living, bed1↔bed2)
#
# Colours:
#   Exterior walls : White          (grand manor render)
#   room_divider   : Tan            (warm plaster)
#   wing_divider   : Light_Bluish_Grey (cool corridor wall)
#   Floor slab     : Dark_Tan       (aged oak boards)
#   Windows        : Light_Blue
#   Front door     : Reddish_Brown  (heavy oak)
#   Roof           : Red
#
# Build order (bottom-up):
#   1. Floor slab
#   2. Building body
#       a. Exterior box (all openings)
#       b. room_divider  (E-W, from box["east"] to box["west"])
#       c. wing_divider  (N-S, from box["south"] to box["north"])
#   3. Building with roof
#       a. Roof on top of body
# ============================================================
"""
from pathlib import Path

from py4bricks.library.colours import (
    Dark_Tan,
    Light_Blue,
    Light_Bluish_Grey,
    Red,
    Reddish_Brown,
    Tan,
    White,
)
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Group, Roof, Scene, Slab, Wall
from py4bricks.pieces import Piece

# ── Dimensions ────────────────────────────────────────────────────────────────

COTTAGE_WIDTH  = 60   # studs east-west
COTTAGE_DEPTH  = 80   # studs north-south
WALL_HEIGHT    = 14   # bricks

# E-W split: kitchen/living (south) vs bedrooms (north)
ROOM_DIVIDER_Z = 45   # studs from south

# N-S split: west wing (kitchen/bed1) vs east wing (living/bed2)
WING_DIVIDER_X = 30   # studs from west

# ── Part factories ────────────────────────────────────────────────────────────

def make_window() -> Piece:
    return Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue)

def make_door() -> Piece:
    return Piece(part=Door1X4X6Frame, colour=Reddish_Brown)

# ── Exterior shell ────────────────────────────────────────────────────────────

def make_exterior() -> Box:
    """Grand cottage exterior: 13 windows + front door."""
    box = Box(
        name="cottage_exterior",
        width_studs=COTTAGE_WIDTH,
        length_studs=COTTAGE_DEPTH,
        height_bricks=WALL_HEIGHT,
        colour=White,
        bonded=True,
    )

    # South wall (59 studs, travels east, studs_x 0=west):
    #   door centred in west wing + 3 windows spread across facade
    box["south"].insert(piece=make_door(),   studs_x=12, brick_row=0)
    box["south"].insert(piece=make_window(), studs_x=3,  brick_row=7)
    box["south"].insert(piece=make_window(), studs_x=35, brick_row=7)
    box["south"].insert(piece=make_window(), studs_x=50, brick_row=7)

    # North wall (59 studs, travels west, studs_x 0=east):
    #   3 windows — one per zone across the garden facade
    box["north"].insert(piece=make_window(), studs_x=5,  brick_row=7)
    box["north"].insert(piece=make_window(), studs_x=25, brick_row=7)
    box["north"].insert(piece=make_window(), studs_x=48, brick_row=7)

    # East wall (79 studs, travels north, studs_x 0=south):
    #   3 windows — kitchen, mid, bedroom views
    box["east"].insert(piece=make_window(), studs_x=10, brick_row=7)
    box["east"].insert(piece=make_window(), studs_x=35, brick_row=7)
    box["east"].insert(piece=make_window(), studs_x=60, brick_row=7)

    # West wall (79 studs, travels south, studs_x 0=north):
    #   3 windows — bedroom, mid, kitchen views
    box["west"].insert(piece=make_window(), studs_x=10, brick_row=7)
    box["west"].insert(piece=make_window(), studs_x=35, brick_row=7)
    box["west"].insert(piece=make_window(), studs_x=60, brick_row=7)

    return box

# ── Interior: E-W room divider (kitchen+living ↔ bedrooms) ───────────────────

def make_room_divider(exterior: Box) -> Wall:
    """E-W wall at z=ROOM_DIVIDER_Z spanning the full interior width.

    Two doorways: one for each wing (kitchen→bedroom1, living→bedroom2).
    Derived from box["east"] ↔ box["west"] — no manual positioning needed.
    """
    wall = Wall.divider_wall(
        from_wall=exterior["east"],
        at_width_studs=ROOM_DIVIDER_Z,
        to_parallel_wall=exterior["west"],
        colour=Tan,
        bonded=True,
    )
    # Doorway for west wing (kitchen → bedroom 1): studs_x≈43 (east end of divider = x≈60, studs_x increases westward)
    wall.opening(studs_x=13, brick_row=0, width_studs=4, height_bricks=6)
    # Doorway for east wing (living room → bedroom 2)
    wall.opening(studs_x=43, brick_row=0, width_studs=4, height_bricks=6)
    return wall

# ── Interior: N-S wing divider (west wing ↔ east wing) ───────────────────────

def make_wing_divider(exterior: Box) -> Wall:
    """N-S wall at x=WING_DIVIDER_X spanning the full interior depth.

    Two doorways: one for south rooms (kitchen↔living), one for north rooms (bed1↔bed2).
    Derived from box["south"] ↔ box["north"] — no manual positioning needed.
    """
    wall = Wall.divider_wall(
        from_wall=exterior["south"],
        at_width_studs=WING_DIVIDER_X,
        to_parallel_wall=exterior["north"],
        colour=Light_Bluish_Grey,
        bonded=True,
    )
    # Doorway in south section (kitchen ↔ living room): ≈ z=22 from south
    wall.opening(studs_x=20, brick_row=0, width_studs=4, height_bricks=6)
    # Doorway in north section (bedroom 1 ↔ bedroom 2): ≈ z=62 from south
    wall.opening(studs_x=60, brick_row=0, width_studs=4, height_bricks=6)
    return wall

# ── Floor ─────────────────────────────────────────────────────────────────────

def make_floor() -> Slab:
    return Slab(
        name="floor",
        width_studs=COTTAGE_WIDTH,
        length_studs=COTTAGE_DEPTH,
        colour=Dark_Tan,
    )

# ── Scene assembly ────────────────────────────────────────────────────────────

scene = Scene("Grand Country Cottage")

# 1. Floor slab
slab_floor = make_floor()
scene.place_at(slab_floor, studs_x=0, plates_y=0, studs_z=0)

# 2. Building body: exterior + all interior dividers
body = Group()

exterior = make_exterior()
body.add(exterior)

body.add(make_room_divider(exterior))   # E-W: floor plan top half vs bottom half
body.add(make_wing_divider(exterior))   # N-S: west wing vs east wing

# 3. Roof + body as a single unit, then placed on top of the floor
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

scene.place_on_top_of(body_with_roof, slab_floor)

# ── Render ────────────────────────────────────────────────────────────────────

output = Path("generated/generated_huge_cottage.mpd")
output.parent.mkdir(exist_ok=True)
scene.render_file(output)
print(f"Grand Country Cottage rendered to {output}")
