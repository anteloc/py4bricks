"""
# ============================================================
# SKYSCRAPER BUILD PLAN
# ============================================================
#
# "Glass Tower" — 10-floor square tower with a grid of windows.
#
# Footprint: 20 x 20 studs (square)
# Height   : 10 floors x 5 bricks = 50 bricks total
#
# Per-floor window rhythm (5-brick band):
#   brick_row 0   : solid border (floor bottom)
#   brick_row 1-3 : Window1X4X3 (3 bricks tall)
#   brick_row 4   : solid border (floor top / next floor bottom)
#
# Windows: 2 per wall per floor, at studs_x=2 and studs_x=12
#   4 walls x 2 windows x 10 floors = 80 windows total
#
# Colours:
#   Tower walls : Dark_Grey
#   Windows     : Light_Blue
#   Floor slab  : Tan
#
# Build order (bottom-up):
#   1. Floor slab
#   2. Building body
#       a. Tower box (50 bricks tall, windows inserted per floor band)
#   3. Body placed on top of floor slab
# ============================================================
"""
from pathlib import Path

from py4bricks.library.colours import Dark_Grey, Light_Blue, Tan
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Group, Scene, Slab
from py4bricks.pieces import Piece

# ── Dimensions ────────────────────────────────────────────────────────────────

TOWER_WIDTH      = 20   # studs east-west
TOWER_DEPTH      = 20   # studs north-south
FLOORS           = 10
BRICKS_PER_FLOOR = 5

# ── Tower ─────────────────────────────────────────────────────────────────────

def make_tower() -> Box:
    """Square tower: 10 floors of 5 bricks each, 2 windows per wall per floor."""
    tower = Box(
        name="tower",
        width_studs=TOWER_WIDTH,
        length_studs=TOWER_DEPTH,
        height_bricks=FLOORS * BRICKS_PER_FLOOR,
        colour=Dark_Grey,
        bonded=True,
    )
    for floor_num in range(FLOORS):
        window_row = floor_num * BRICKS_PER_FLOOR + 1
        for wall_name in ("south", "north", "east", "west"):
            for studs_x in (2, 12):
                tower[wall_name].insert(
                    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
                    studs_x=studs_x,
                    brick_row=window_row,
                )
    return tower

# ── Floor ─────────────────────────────────────────────────────────────────────

def make_floor() -> Slab:
    """Single-plate ground slab matching the tower footprint."""
    return Slab(
        name="floor",
        width_studs=TOWER_WIDTH,
        length_studs=TOWER_DEPTH,
        colour=Tan,
    )

# ── Scene assembly ────────────────────────────────────────────────────────────

scene = Scene("Glass Tower")

# 1. Floor slab
slab_floor = make_floor()
scene.place_at(slab_floor, studs_x=0, plates_y=0, studs_z=0)

# 2. Building body
body = Group()
body.add(make_tower())

# 3. Place body on top of floor slab
scene.place_on_top_of(body, slab_floor)

# ── Render ────────────────────────────────────────────────────────────────────

output = Path("generated/generated_skyscraper.mpd")
output.parent.mkdir(exist_ok=True)
scene.render_file(output)
print(f"Glass Tower rendered to {output}")
