r"""
# ============================================================
# LIGHTHOUSE BUILD PLAN
# ============================================================
#
# "Cape Colour Lighthouse" — a tall, classic striped lighthouse tower.
#
# Tower footprint: 10 × 10 studs (all sections share the same footprint)
# Total tower height: 26 bricks + sloped roof
#
# Side view (south-facing):
#
#      /--\      ← Red sloped roof (ridge: N-S)
#     |YYYY|     ← Yellow lantern room, 4 bricks
#     |    |       Windows (Light_Blue) on all 4 walls
#     |RRRR|     ← Red band, 2 bricks
#     |    |
#     |WWWW|     ← White upper section, 6 bricks
#     |  w |       1 window on south wall (mid-height)
#     |RRRR|     ← Red band, 2 bricks
#     |    |
#     |WWWW|     ← White lower section, 6 bricks
#     |    |
#     |LLLL|     ← Light_Grey base, 6 bricks
#     |  D |       Door on south wall
#   ========     ← Dark_Grey foundation slab (10×10, 2 plates thick)
#
# Sections (bottom to top):
#   1. foundation    Dark_Grey slab, 10×10, 2 plates
#   2. base          Light_Grey box, 10×10, 6 bricks  [door on south]
#   3. lower_white   White box, 10×10, 6 bricks
#   4. red_band_1    Red box, 10×10, 2 bricks
#   5. upper_white   White box, 10×10, 6 bricks       [window on south, mid-height]
#   6. red_band_2    Red box, 10×10, 2 bricks
#   7. lantern_room  Yellow box, 10×10, 4 bricks       [windows on all 4 walls]
#   8. roof          Red, ridge north-south
#
# Colours:
#   Foundation  : Dark_Grey
#   Base        : Light_Grey
#   White body  : White
#   Bands       : Red
#   Lantern     : Yellow
#   Windows     : Light_Blue
#   Door        : Dark_Tan
#   Roof        : Red
#
# Build order (bottom-up):
#   1. Foundation slab (placed in scene)
#   2. Tower group: base → lower_white → red_band_1 → upper_white
#                → red_band_2 → lantern_room → roof
#      (each section stacked via place_on_top_of — no Y math needed)
#   3. Tower placed on top of foundation
# ============================================================
"""
from pathlib import Path

from py4bricks.library.colours import (
    Dark_Grey,
    Dark_Tan,
    Light_Blue,
    Light_Grey,
    Red,
    White,
    Yellow,
)
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Group, Roof, Scene, Slab
from py4bricks.pieces import Piece

# ── Dimensions ─────────────────────────────────────────────────────────────────

TOWER_WIDTH = 10   # studs — all sections share this footprint
TOWER_DEPTH = 10   # studs

# Centering a 4-stud piece in a 9-stud wall (width_studs-1 = 9):
#   (9 - 4) / 2 = 2.5  →  studs_x=3 gives center at 4.5 (exact wall center)
WALL_CENTER = 3

# Floors sit 1 stud inside each wall face → 8x8 interior for a 10x10 tower
FLOOR_COLOUR        = Dark_Tan    # warm wood planks (base, lower, upper)
LANTERN_FLOOR_COLOUR = Light_Grey  # metal grating at the beacon level

# ── Part factories (each call returns a fresh Piece) ──────────────────────────

def make_window() -> Piece:
    return Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue)

def make_door() -> Piece:
    return Piece(part=Door1X4X6Frame, colour=Dark_Tan)

# ── Foundation ─────────────────────────────────────────────────────────────────

def make_foundation() -> Slab:
    return Slab(
        name="foundation",
        width_studs=TOWER_WIDTH,
        length_studs=TOWER_DEPTH,
        colour=Dark_Grey,
        height_plates=2,
    )

# ── Interior floor helper ──────────────────────────────────────────────────────

def add_interior_floor(box: Box, colour) -> None:
    """Lay a floor slab on the inside of a box section (1 stud inside each wall)."""
    floor = Slab(
        name=f"{box.name}_floor",
        width_studs=TOWER_WIDTH - 2,
        length_studs=TOWER_DEPTH - 2,
        colour=colour,
    )
    box.place_at(floor, studs_x=1, plates_y=0, studs_z=1)

# ── Tower sections ─────────────────────────────────────────────────────────────

def make_section(name: str, colour, height_bricks: int) -> Box:
    """Plain solid box section — no openings."""
    return Box(
        name=name,
        width_studs=TOWER_WIDTH,
        length_studs=TOWER_DEPTH,
        height_bricks=height_bricks,
        colour=colour,
        bonded=True,
    )

def make_base_section() -> Box:
    """Light_Grey stone base with a door on the south wall."""
    box = make_section("base", Light_Grey, 6)
    box["south"].insert(piece=make_door(), studs_x=WALL_CENTER, brick_row=0)
    add_interior_floor(box, FLOOR_COLOUR)
    return box

def make_lower_white() -> Box:
    """White lower tower section with a floor."""
    box = make_section("lower_white", White, 6)
    add_interior_floor(box, FLOOR_COLOUR)
    return box

def make_upper_white() -> Box:
    """White upper section with a window on the south wall and a floor."""
    box = make_section("upper_white", White, 6)
    box["south"].insert(piece=make_window(), studs_x=WALL_CENTER, brick_row=2)
    add_interior_floor(box, FLOOR_COLOUR)
    return box

def make_lantern_room() -> Box:
    """Yellow lantern room: Light_Blue windows on all four walls, metal floor."""
    box = make_section("lantern_room", Yellow, 4)
    box["south"].insert(piece=make_window(), studs_x=WALL_CENTER, brick_row=0)
    box["north"].insert(piece=make_window(), studs_x=WALL_CENTER, brick_row=0)
    box["east"].insert(piece=make_window(),  studs_x=WALL_CENTER, brick_row=0)
    box["west"].insert(piece=make_window(),  studs_x=WALL_CENTER, brick_row=0)
    add_interior_floor(box, LANTERN_FLOOR_COLOUR)
    return box

# ── Roof ───────────────────────────────────────────────────────────────────────

def make_roof() -> Roof:
    return Roof(
        name="lighthouse_roof",
        width_studs=TOWER_WIDTH,
        length_studs=TOWER_DEPTH,
        ridge_running="north-south",
        colour=Red,
    )

# ── Scene assembly ─────────────────────────────────────────────────────────────

scene = Scene("Cape Colour Lighthouse")

# 1. Foundation slab
foundation = make_foundation()
scene.place_at(foundation, studs_x=0, plates_y=0, studs_z=0)

# 2. Tower group: sections stacked bottom-up via place_on_top_of
tower = Group(name="tower")

base        = make_base_section()
lower_white = make_lower_white()
red_band_1  = make_section("red_band_1", Red, 2)
upper_white = make_upper_white()
red_band_2  = make_section("red_band_2", Red, 2)
lantern     = make_lantern_room()
roof        = make_roof()

tower.add(base)
tower.place_on_top_of(lower_white, base)
tower.place_on_top_of(red_band_1,  lower_white)
tower.place_on_top_of(upper_white, red_band_1)
tower.place_on_top_of(red_band_2,  upper_white)
tower.place_on_top_of(lantern,     red_band_2)
tower.place_on_top_of(roof,        lantern)

# 3. Place tower on top of foundation
scene.place_on_top_of(tower, foundation)

# ── Render ─────────────────────────────────────────────────────────────────────

output = Path("generated/generated_lighthouse.mpd")
output.parent.mkdir(exist_ok=True)
scene.render_file(output)
print(f"Lighthouse rendered to {output}")
