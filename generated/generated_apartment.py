"""
# Apartment Build Plan
# ====================
#
# LAYOUT (top-down, Z = 0 south → 40 north, X = 0 west → 50 east):
#
#   X=0        X=18           X=50
#   +----------+--------------+    Z=40 (north wall, 2 windows)
#   |          |              |
#   | BATHROOM | KITCHEN      |    north half (Z=20..40)
#   | 18 × 20  | 32 × 20      |
#   |          |              |
#   +----[dw]--+--------------+    Z=20 (internal E-W wall, doorway opening)
#   |                         |
#   |     LIVING ROOM         |    south half (Z=0..20)
#   |     50 × 20             |
#   +--[D]--[W]-----------[W]-+    Z=0 (south wall: 1 door + 2 windows)
#
#   East wall  (X=50): 1 window (living-room side)
#   North wall (Z=40): 2 windows (kitchen + bathroom)
#
# PARTS:
#   Door1X4X6Frame              (4W × 6H bricks) — 1 exterior door
#   Window1X4X3WithoutShutterTabs (4W × 3H bricks) — 5 exterior windows
#   wall.opening()              — 2 interior doorways (living → kitchen, living → bathroom)
#
# BUILD ORDER (bottom-up):
#   1. Floor slab         (Tan,        50×40,  1 plate)
#   2. Outer Box          (Light_Grey, 50×40×10 bricks, bonded)
#   3. E-W divider wall   (Light_Grey, 48×10,  facing north, at z=20)
#   4. N-S divider wall   (Light_Grey, 18×10,  facing west,  at x=18, z=21)
"""

from pathlib import Path

from py4bricks.library.colours import Light_Blue, Light_Grey, Tan
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Scene, Slab, Wall, proportional
from py4bricks.pieces import Piece

# ── Apartment dimensions ────────────────────────────────────────────────────
APT_WIDTH    = 50   # studs, east-west
APT_DEPTH    = 40   # studs, south-north
WALL_HEIGHT  = 10   # bricks
FLOOR_PLATES = 1    # plates (Slab default height)

# Interior split coordinates
SPLIT_Z = 20        # Z dividing living room (south) from kitchen+bathroom (north)
SPLIT_X = 18        # X dividing bathroom (west) from kitchen (east) in north half


# ── Section 1: Floor ────────────────────────────────────────────────────────

def make_floor() -> Slab:
    return Slab(
        width_studs=APT_WIDTH,
        length_studs=APT_DEPTH,
        colour=Tan,
        name="floor",
    )


# ── Section 2: Outer Walls ──────────────────────────────────────────────────

def make_outer_walls() -> Box:
    """Closed exterior perimeter with 1 door (south) and 5 windows."""
    walls = Box(
        width_studs=APT_WIDTH,
        length_studs=APT_DEPTH,
        height_bricks=WALL_HEIGHT,
        colour=Light_Grey,
        bonded=True,
        name="outer_walls",
    )

    # South wall: door on the left side, two windows further right (D-W-W)
    walls["south"].insert(piece=Piece(part=Door1X4X6Frame, colour=Tan),
                          studs_x=4, brick_row=0)
    walls["south"].insert(piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
                          studs_x=18, brick_row=4)
    walls["south"].insert(piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
                          studs_x=38, brick_row=4)

    # East wall: 1 window on the living-room side
    walls["east"].insert(piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
                         studs_x=10, brick_row=4)

    # North wall: 2 windows — studs_x=0 is east corner, increases westward
    walls["north"].insert(piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
                          studs_x=8, brick_row=4)   # kitchen side
    walls["north"].insert(piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
                          studs_x=30, brick_row=4)  # bathroom side

    return walls


# ── Section 3: Internal Walls ───────────────────────────────────────────────

def make_ew_divider() -> Wall:
    """E-W wall separating living room (south) from kitchen+bathroom (north).

    Width fits between outer west and east walls (APT_WIDTH - 2).
    A doorway opening near the east end gives access to the upper rooms.
    """
    wall = Wall(
        width_studs=APT_WIDTH - 2,
        height_bricks=WALL_HEIGHT,
        colour=Light_Grey,
        facing="north",
        name="ew_divider",
    )
    # Doorway: toward the kitchen side so bathroom is still enclosed
    doorway_x = proportional(APT_WIDTH - 2, (3, 4)) - 2
    wall.opening(studs_x=doorway_x, brick_row=0, width_studs=4, height_bricks=6)
    return wall


def make_ns_divider() -> Wall:
    """N-S wall separating bathroom (west) from kitchen (east) in the north half.

    Runs from the E-W divider to just before the north outer wall.
    facing='west' passed to place_at() makes the wall extend along the +Z axis.
    Doorway opening near the north end gives bathroom access from the kitchen.
    """
    north_section_depth = APT_DEPTH - SPLIT_Z - 2  # fits between E-W divider and north wall
    wall = Wall(
        width_studs=north_section_depth,
        height_bricks=WALL_HEIGHT,
        colour=Light_Grey,
        name="ns_divider",
    )
    # Doorway for bathroom access (near north end of divider)
    doorway_z = north_section_depth - 8
    wall.opening(studs_x=doorway_z, brick_row=0, width_studs=4, height_bricks=6)
    return wall


# ── Assemble ────────────────────────────────────────────────────────────────

scene = Scene("Apartment")

floor = make_floor()
scene.place_at(floor, studs_x=0, plates_y=0, studs_z=0)

outer_walls = make_outer_walls()
scene.place_on_top_of(outer_walls, floor)

# Internal walls sit on top of the floor (plates_y = FLOOR_PLATES)
ew_divider = make_ew_divider()
scene.place_at(ew_divider, studs_x=1, plates_y=FLOOR_PLATES, studs_z=SPLIT_Z)

ns_divider = make_ns_divider()
# facing="west" is required here: place_at() sets the rotation, overriding
# whatever was passed to Wall(). "west" = 270° around Y → local X maps to world +Z.
scene.place_at(
    ns_divider,
    studs_x=SPLIT_X, plates_y=FLOOR_PLATES, studs_z=SPLIT_Z + 1,
    facing="west",  # "west" = 270° around Y → local X maps to world +Z (N-S direction)
)

# ── Render ──────────────────────────────────────────────────────────────────

output = Path("generated/generated_apartment.mpd")
scene.render_file(output)
print(f"Apartment rendered to {output}")
