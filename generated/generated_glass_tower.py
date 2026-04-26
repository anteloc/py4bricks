"""
# ============================================================
# GLASS TOWER BUILD PLAN
# ============================================================
#
# "Prism Tower" — a setback glass-and-steel skyscraper.
#
# Three-section setback profile (south elevation):
#
#              |  |          <- Metallic Silver antenna
#         ┌────┘  └────┐     <- crown roof slab
#         │    CROWN   │     <- 12x12,  3 floors, all Red
#        ─┴────────────┴─    <- shaft terrace slab (Silver)
#       ┌─┴────────────┴─┐   <- shaft (20x20, 12 floors)
#       │  Silver + Red  │      Red bands every 4th floor
#      ─┴────────────────┴─  <- podium terrace slab (Silver)
#     ┌─┴────────────────┴─┐ <- podium (30x30, 2 floors)
#     │  Red lobby + Silver│    floor 0 = Red + entrance door
#     └────────────────────┘
#
# Window curtain wall rhythm (6-brick floor band):
#   row 0-1 : solid frame (Silver or Red wall colour)
#   row 2-4 : Window1X4X3 (blue or clear glass)
#   row 5   : solid lintel
#
# Window grids (same on all 4 walls — square sections):
#   Podium (29-stud wall) : studs_x = 2, 8, 14, 20, 26  (5/floor)
#   Shaft  (19-stud wall) : studs_x = 2, 8, 14           (3/floor)
#   Crown  (11-stud wall) : studs_x = 2, 7               (2/floor)
#
# Colours:
#   Frame (Silver)   : Light_Bluish_Grey
#   Accent (Red)     : Red  — podium lobby + every 4th shaft floor + crown
#   Blue glass       : Trans_Light_Blue  (standard floors)
#   Clear glass      : Trans_Clear       (Red accent floors, lobby)
#   Floor slabs      : Dark_Tan
#   Setback terraces : Light_Bluish_Grey (2-plate thick ledges)
#   Terrain          : Tan
#   Antenna          : Metallic_Silver column
#
# Build order:
#   1. Assemble body top-down stacking with setback terraces:
#        podium -> podium_terrace -> shaft -> shaft_terrace
#        -> crown -> crown_roof -> antenna
#   2. Terrain auto-derived from body.studs_x x body.studs_z
#   3. Body placed on top of terrain
# ============================================================
"""
from pathlib import Path
from typing import Callable

from py4bricks.library.colours import (
    Dark_Tan,
    Light_Bluish_Grey,
    Metallic_Silver,
    Red,
    Reddish_Brown,
    Tan,
    Trans_Clear,
    Trans_Light_Blue,
)
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Column, Group, Scene, Slab
from py4bricks.pieces import Piece

# ── Dimensions ────────────────────────────────────────────────────────────────

BRICKS_PER_FLOOR = 6    # bricks per floor (door fits exactly at 6)
WIN_ROW          = 2    # brick_row for all windows within a 6-brick band

PODIUM_W         = 30   # studs — widest section
PODIUM_D         = 30
PODIUM_FLOORS    = 2

SHAFT_W          = 20   # studs — mid section
SHAFT_D          = 20
SHAFT_FLOORS     = 12
SHAFT_INSET      = (PODIUM_W - SHAFT_W) // 2   # = 5

CROWN_W          = 12   # studs — top section
CROWN_D          = 12
CROWN_FLOORS     = 3
CROWN_INSET      = (SHAFT_W - CROWN_W) // 2    # = 4

# Window positions per wall per floor (all sections are square)
WIN_X_PODIUM = (2, 8, 14, 20, 25)   # 5 windows on 29-stud walls (max x = wall_len-4 = 25)
WIN_X_SHAFT  = (2, 8, 14)           # 3 windows on 19-stud walls
WIN_X_CROWN  = (2, 7)               # 2 windows on 11-stud walls

# ── Part factories ────────────────────────────────────────────────────────────

def win(colour) -> Piece:
    """Fresh window piece in the given glass colour."""
    return Piece(part=Window1X4X3WithoutShutterTabs, colour=colour)

def make_door() -> Piece:
    """Central entrance door."""
    return Piece(part=Door1X4X6Frame, colour=Reddish_Brown)

# ── Level construction ────────────────────────────────────────────────────────

def make_level_walls(
    width: int,
    depth: int,
    wall_colour,
    glass_colour,
    win_x: tuple,
    has_door: bool = False,
) -> Box:
    """One floor of walls: dense window grid on all four faces.

    When has_door=True, the central entrance door is added to the south wall
    and any window that would overlap with it is skipped automatically.
    """
    box = Box(
        name="walls",
        width_studs=width,
        length_studs=depth,
        height_bricks=BRICKS_PER_FLOOR,
        colour=wall_colour,
        bonded=True,
    )

    if has_door:
        door_x = (width - 1) // 2 - 1          # centred on south wall
        box["south"].insert(piece=make_door(), studs_x=door_x, brick_row=0)
        # Skip windows whose 4-stud span would overlap the door
        south_wins = tuple(x for x in win_x if x + 3 < door_x or x > door_x + 3)
        for x in south_wins:
            box["south"].insert(piece=win(glass_colour), studs_x=x, brick_row=WIN_ROW)
        for wall in ("north", "east", "west"):
            for x in win_x:
                box[wall].insert(piece=win(glass_colour), studs_x=x, brick_row=WIN_ROW)
    else:
        for wall in ("south", "north", "east", "west"):
            for x in win_x:
                box[wall].insert(piece=win(glass_colour), studs_x=x, brick_row=WIN_ROW)

    return box


def make_level(
    width: int,
    depth: int,
    wall_colour,
    glass_colour,
    win_x: tuple,
    has_door: bool = False,
) -> Group:
    """One complete floor: Dark_Tan slab + walls placed on top."""
    level = Group(name="level")
    slab = Slab(width_studs=width, length_studs=depth, colour=Dark_Tan)
    level.add(slab)
    walls = make_level_walls(width, depth, wall_colour, glass_colour, win_x, has_door)
    level.place_on_top_of(walls, slab)
    return level

# ── Tower sections ────────────────────────────────────────────────────────────

def make_tower_section(
    width: int,
    depth: int,
    floors: int,
    win_x: tuple,
    colour_fn: Callable[[int], object],
    glass_fn: Callable[[int], object],
    has_door_on_first: bool = False,
) -> Group:
    """Stack `floors` levels, deriving wall/glass colour from per-floor callables.

    colour_fn(i) and glass_fn(i) receive the 0-based floor index so callers
    can express patterns like 'Red every 4th floor' as a simple lambda.
    """
    section = Group()
    prev_level = None
    for i in range(floors):
        level = make_level(
            width, depth,
            colour_fn(i), glass_fn(i),
            win_x,
            has_door=(has_door_on_first and i == 0),
        )
        if prev_level is None:
            section.add(level)
        else:
            section.place_on_top_of(level, prev_level)
        prev_level = level
    return section


def make_podium() -> Group:
    """Base: 2 floors, 30x30. Ground = Red lobby + entrance. Upper = Silver."""
    return make_tower_section(
        PODIUM_W, PODIUM_D, PODIUM_FLOORS, WIN_X_PODIUM,
        colour_fn=lambda i: Red if i == 0 else Light_Bluish_Grey,
        glass_fn =lambda i: Trans_Clear if i == 0 else Trans_Light_Blue,
        has_door_on_first=True,
    )


def make_shaft() -> Group:
    """Main tower: 12 floors, 20x20. Red accent bands every 4th floor."""
    return make_tower_section(
        SHAFT_W, SHAFT_D, SHAFT_FLOORS, WIN_X_SHAFT,
        colour_fn=lambda i: Red if i % 4 == 0 else Light_Bluish_Grey,
        glass_fn =lambda i: Trans_Clear if i % 4 == 0 else Trans_Light_Blue,
    )


def make_crown() -> Group:
    """Top cap: 3 floors, 12x12, all Red with clear glass."""
    return make_tower_section(
        CROWN_W, CROWN_D, CROWN_FLOORS, WIN_X_CROWN,
        colour_fn=lambda i: Red,
        glass_fn =lambda i: Trans_Clear,
    )

# ── Terrain ───────────────────────────────────────────────────────────────────

def make_terrain(constructed: Group) -> Slab:
    """Terrain slab auto-sized to the full footprint of the constructed body."""
    return Slab(
        name="terrain",
        width_studs=constructed.studs_x,
        length_studs=constructed.studs_z,
        colour=Tan,
    )

# ── Scene assembly ────────────────────────────────────────────────────────────

scene = Scene("Prism Tower")

body = Group()

# ── Setback stack ─────────────────────────────────────────────────────────────

podium = make_podium()
body.add(podium)

podium_terrace = Slab(
    name="podium_terrace",
    width_studs=PODIUM_W, length_studs=PODIUM_D,
    colour=Light_Bluish_Grey, height_plates=2,
)
body.place_on_top_of(podium_terrace, podium)

shaft = make_shaft()
body.place_on_top_of(shaft, podium_terrace,
                     right_studs=SHAFT_INSET, back_studs=SHAFT_INSET)

shaft_terrace = Slab(
    name="shaft_terrace",
    width_studs=SHAFT_W, length_studs=SHAFT_D,
    colour=Light_Bluish_Grey, height_plates=2,
)
body.place_on_top_of(shaft_terrace, shaft)

crown = make_crown()
body.place_on_top_of(crown, shaft_terrace,
                     right_studs=CROWN_INSET, back_studs=CROWN_INSET)

crown_roof = Slab(
    name="crown_roof",
    width_studs=CROWN_W, length_studs=CROWN_D,
    colour=Light_Bluish_Grey, height_plates=2,
)
body.place_on_top_of(crown_roof, crown)

# Metallic antenna centred on crown roof
body.place_on_top_of(
    Column(height_bricks=8, colour=Metallic_Silver, shape="square"),
    crown_roof,
    right_studs=CROWN_W // 2 - 1,
    back_studs=CROWN_D // 2 - 1,
)

# ── Terrain + final placement ─────────────────────────────────────────────────

terrain = make_terrain(body)
scene.place_at(terrain, studs_x=0, plates_y=0, studs_z=0)
scene.place_on_top_of(body, terrain)

# ── Render ────────────────────────────────────────────────────────────────────

output = Path("generated/generated_glass_tower.mpd")
output.parent.mkdir(exist_ok=True)
scene.render_file(output)
print(f"Prism Tower rendered to {output}")
