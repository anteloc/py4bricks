"""
WallLayout test — 5-wall L-shaped perimeter with doors, windows, and an opening.

Layout (top view, Y up):

    z=15  [north wall, 20 studs wide going west]
          |                                    |
    z=5   [west, 10s south] [step, 12s east --→]
          |
    z=0   [south wall, 20 studs wide going east]
         x=0                             x=20

Walls:
    "south"  east  20 studs  →  length 21  (first wall, shares corner with east)
    "east"   north 15 studs  →  length 16  (shares corner with south)
    "north"  west  20 studs  →  length 21  (shares corner with east)
    "west"   south 10 studs  →  length 11  (shares corner with north)
    "step"   east  12 studs  →  length 12  (contributes corner to west, but no other shares corner with it)

Inserts / openings:
    south : Door1X4X6Frame        at studs_x=8,  brick_row=0
    east  : Window1X4X3           at studs_x=4,  brick_row=3
    north : Window1X4X3           at studs_x=6,  brick_row=3
    west  : bare opening 4×3      at studs_x=2,  brick_row=2
    step  : Window1X4X3           at studs_x=3,  brick_row=3
"""

from pathlib import Path

from py4bricks.library.colours import Light_Blue, Light_Grey, Tan
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Scene, WallLayout
from py4bricks.pieces import Piece

scene = Scene("WallLayout test")

layout = WallLayout(height_bricks=8, colour=Light_Grey, bonded=True)

layout.add_wall(name="south", length_studs=20, direction="east")
layout.add_wall(name="east",  length_studs=15, direction="north")
layout.add_wall(name="north", length_studs=20, direction="west")
layout.add_wall(name="west",  length_studs=10, direction="south")
layout.add_wall(name="step",  length_studs=12, direction="east")

layout["south"].insert(
    piece=Piece(part=Door1X4X6Frame, colour=Tan),
    studs_x=8,
    brick_row=0,
)
layout["east"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=4,
    brick_row=3,
)
layout["north"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=6,
    brick_row=3,
)
layout["west"].opening(
    studs_x=2,
    brick_row=2,
    width_studs=4,
    height_bricks=3,
)
layout["step"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=3,
    brick_row=3,
)

scene.place_at(layout, studs_x=0, plates_y=0, studs_z=0)

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("WallLayout test rendered to wall_layout_test.mpd")
