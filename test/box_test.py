"""
Box test — closed 20×15 rectangular perimeter with pieces on every wall.

Layout (top view, Y up):

    z=15  [north wall, 20 studs, travelling west ←]
          |                                       |
          |                                       |
    z=0   [south wall, 20 studs, travelling east →]
         x=0                                    x=20

Walls:
    "south"  east  20 studs  — Door1X4X6Frame at studs_x=8,  brick_row=0
    "east"   north 15 studs  — Window1X4X3    at studs_x=4,  brick_row=3
    "north"  west  20 studs  — Window1X4X3    at studs_x=6,  brick_row=3
    "west"   south 15 studs  — Window1X4X3    at studs_x=4,  brick_row=3
"""

from pathlib import Path

from py4bricks.library.colours import Light_Blue, Light_Grey, Tan
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Scene
from py4bricks.llm.box import Box
from py4bricks.pieces import Piece

scene = Scene("Box test")

box = Box(
    width_studs=20,
    length_studs=15,
    height_bricks=8,
    colour=Light_Grey,
    bonded=True,
)

box["south"].insert(
    piece=Piece(part=Door1X4X6Frame, colour=Tan),
    studs_x=8,
    brick_row=0,
)
box["east"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=4,
    brick_row=3,
)
box["north"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=6,
    brick_row=3,
)
box["west"].insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=4,
    brick_row=3,
)

scene.place_at(box, studs_x=0, plates_y=0, studs_z=0)

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Box test rendered to box_test.mpd")
