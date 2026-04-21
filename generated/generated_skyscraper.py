"""
Skyscraper Layout Plan
======================

Footprint : 20×20 studs (square tower)
Stories   : 10 floors × 5 bricks each = 50 bricks total
Floor slab: 1 plate thick, Tan

Per floor (5-brick window rhythm):
  brick_row=0  : solid border (bottom of floor)
  brick_row=1-3: Window1X4X3 (3 bricks high)
  brick_row=4  : solid border (top of floor / bottom of next)

Windows (Light_Blue):
  2 per wall per floor, at studs_x=2 and studs_x=12
  4 walls × 2 windows × 10 floors = 80 windows total

Colors:
  Walls  : Dark_Grey
  Windows: Light_Blue
  Floor  : Tan
"""

from pathlib import Path

from py4bricks.library.colours import Dark_Grey, Light_Blue, Tan
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Scene
from py4bricks.llm.box import Box
from py4bricks.llm.slab import Slab
from py4bricks.pieces import Piece

FLOORS           = 10
BRICKS_PER_FLOOR = 5

scene = Scene()

# --- Ground floor slab ---
floor = Slab(width_studs=20, length_studs=20, colour=Tan)
scene.place_at(floor, studs_x=0, plates_y=0, studs_z=0)

# --- Exterior tower walls ---
tower = Box(
    width_studs=20,
    length_studs=20,
    height_bricks=FLOORS * BRICKS_PER_FLOOR,
    colour=Dark_Grey,
    bonded=True,
)

# Windows: 2 per wall per floor, 1 brick from the bottom of each floor band
for floor_num in range(FLOORS):
    window_row = floor_num * BRICKS_PER_FLOOR + 1
    for wall_name in ("south", "north", "east", "west"):
        for studs_x in (2, 12):
            tower[wall_name].insert(
                piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
                studs_x=studs_x,
                brick_row=window_row,
            )

scene.place_on_top_of(tower, floor)

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Skyscraper rendered to generated_skyscraper.mpd")
