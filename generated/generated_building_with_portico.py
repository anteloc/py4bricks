"""
# ============================================================
# 3-STORY BUILDING WITH PORTICO
# ============================================================
#
# "Neoclassical Office" — a three-floor stone building with a
# classical columned portico framing the entrance.
#
# Footprint: 40 studs wide (E-W) x 30 studs deep (N-S)
# Height   : 3 floors x 6 bricks = 18 bricks total
#
# Per-floor window rhythm (6-brick band):
#   brick_row 0-1 : solid border (base / sill)
#   brick_row 2-4 : Window1X4X3 (3 bricks tall)
#   brick_row 5   : solid border (lintel / next floor base)
#
# Exterior openings per floor:
#   South wall (39 studs): 2 windows (+ door on floor 0 only)
#   North wall (39 studs): 2 windows
#   East  wall (29 studs): 2 windows
#   West  wall (29 studs): 2 windows
#   Total: 24 windows + 1 front door
#
# Portico (ground floor only):
#   4 circular White columns, 6 bricks tall
#   Spacing: 10 studs — columns at x=4, 14, 24, 34
#   flanking the door centred at x=18..21
#
# Colours:
#   Exterior walls : Tan              (warm stone)
#   Floor slabs    : Dark_Tan         (stone flags)
#   Flat roof      : Light_Bluish_Grey (concrete)
#   Columns + cap  : White            (classical marble)
#   Windows        : Light_Blue
#   Front door     : Reddish_Brown    (heavy oak)
#
# Build order (bottom-up):
#   1. Building body — 3 levels stacked with place_on_top_of
#       Each level (make_building_level) contains:
#           a. Floor slab
#           b. Walls (Box, 6 bricks) placed on top of slab
#           c. [floor 0 only] Portico placed in front of south wall
#           d. [top floor only] Flat roof placed on top of walls
#   2. Body placed at scene origin
# ============================================================
"""
from pathlib import Path

from py4bricks.library.colours import (
    Dark_Tan,
    Light_Blue,
    Light_Bluish_Grey,
    Reddish_Brown,
    Tan,
    White,
)
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Column, Group, Scene, Slab
from py4bricks.pieces import Piece

# ── Dimensions ────────────────────────────────────────────────────────────────

BUILDING_WIDTH   = 40   # studs east-west
BUILDING_DEPTH   = 30   # studs north-south
BRICKS_PER_FLOOR = 6    # bricks per level
FLOORS           = 3

# Portico: 4 columns at x=4,14,24,34 — frames the door at x=18..21
PORTICO_COLS     = 4
PORTICO_SPACING  = 10   # studs between column centres
PORTICO_OFFSET_X = 4    # studs from west end
PORTICO_OFFSET_Z = -2   # studs in front of south wall

# ── Part factories ────────────────────────────────────────────────────────────

def make_window() -> Piece:
    """Fresh Light_Blue window piece."""
    return Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue)

def make_door() -> Piece:
    """Fresh Reddish_Brown door frame piece."""
    return Piece(part=Door1X4X6Frame, colour=Reddish_Brown)

# ── Per-floor walls ───────────────────────────────────────────────────────────

def make_floor_walls(floor_num: int) -> Box:
    """One floor of exterior walls: 6 bricks tall, 2 windows per wall.

    Windows sit at brick_row=2 within the 6-brick band (rows 2-4),
    leaving a solid sill below and a solid lintel above.
    The front door is inserted only on floor 0.
    """
    box = Box(
        name=f"floor_{floor_num}_walls",
        width_studs=BUILDING_WIDTH,
        length_studs=BUILDING_DEPTH,
        height_bricks=BRICKS_PER_FLOOR,
        colour=Tan,
        bonded=True,
    )

    if floor_num == 0:
        box["south"].insert(piece=make_door(), studs_x=18, brick_row=0)

    box["south"].insert(piece=make_window(), studs_x=4,  brick_row=2)
    box["south"].insert(piece=make_window(), studs_x=30, brick_row=2)
    box["north"].insert(piece=make_window(), studs_x=4,  brick_row=2)
    box["north"].insert(piece=make_window(), studs_x=30, brick_row=2)
    box["east"].insert(piece=make_window(),  studs_x=4,  brick_row=2)
    box["east"].insert(piece=make_window(),  studs_x=20, brick_row=2)
    box["west"].insert(piece=make_window(),  studs_x=4,  brick_row=2)
    box["west"].insert(piece=make_window(),  studs_x=20, brick_row=2)

    return box

# ── Portico ───────────────────────────────────────────────────────────────────

def make_portico() -> Group:
    """4 circular columns capped with a connecting slab, 1 floor tall."""
    prototype = Column(
        height_bricks=BRICKS_PER_FLOOR,
        colour=White,
        shape="circular",
    )
    return Column.column_row(
        prototype=prototype,
        count=PORTICO_COLS,
        spacing_studs=PORTICO_SPACING,
        with_slabs_colour=White,
    )

# ── Building level ────────────────────────────────────────────────────────────

def make_building_level(floor_num: int, is_top_floor: bool = False) -> Group:
    """One complete building floor: floor slab + walls + optional extras.

    The slab is the base; walls are stacked on top with place_on_top_of so
    vertical alignment is automatic regardless of slab thickness.

    floor_num    — 0-based floor index; determines door placement and name.
    is_top_floor — when True, adds a flat roof slab on top of the walls.
    """
    level = Group(name=f"floor_{floor_num}")

    # Base: floor slab
    floor_slab = Slab(
        name=f"slab_{floor_num}",
        width_studs=BUILDING_WIDTH,
        length_studs=BUILDING_DEPTH,
        colour=Dark_Tan,
    )
    level.add(floor_slab)

    # Walls for this floor, stacked on the slab
    walls = make_floor_walls(floor_num)
    level.place_on_top_of(walls, floor_slab)

    # Ground floor: portico in front of south entrance
    if floor_num == 0:
        level.place_at(
            make_portico(),
            studs_x=PORTICO_OFFSET_X,
            plates_y=0,
            studs_z=PORTICO_OFFSET_Z,
        )

    # Top floor: flat roof closing the building
    if is_top_floor:
        roof = Slab(
            name="roof",
            width_studs=BUILDING_WIDTH,
            length_studs=BUILDING_DEPTH,
            colour=Light_Bluish_Grey,
            height_plates=2,
        )
        level.place_on_top_of(roof, walls)

    return level

# ── Scene assembly ────────────────────────────────────────────────────────────

scene = Scene("Neoclassical Office")

# Stack all floors: each level placed on top of the previous one
body = Group()

levels = [
    make_building_level(i, is_top_floor=(i == FLOORS - 1))
    for i in range(FLOORS)
]

body.add(levels[0])
for i in range(1, FLOORS):
    body.place_on_top_of(levels[i], levels[i - 1])

scene.place_at(body, studs_x=0, plates_y=0, studs_z=0)

# ── Render ────────────────────────────────────────────────────────────────────

output = Path("generated/generated_building_with_portico.mpd")
output.parent.mkdir(exist_ok=True)
scene.render_file(output)
print(f"Neoclassical Office rendered to {output}")
