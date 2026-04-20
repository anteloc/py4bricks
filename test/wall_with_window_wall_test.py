"""
Wall with window and door frame test — using the Wall API.

Same scenario as wall_with_window_test.py, rewritten with Wall:
    Wall: 40 studs wide, 35 bricks high, non-bonded, Light_Grey
    Window1X4X3 at studs 8-11, rows 16-18  (mid-height, left of centre)
    Door1X4X6   at studs 20-23, rows 0-5   (ground level, right of centre)
"""

from pathlib import Path

from py4bricks.library.colours import Light_Blue, Light_Grey, Tan
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Scene, Wall
from py4bricks.pieces import Piece

scene = Scene()

wall = Wall(width_studs=40, height_bricks=35, colour=Light_Grey)

wall.insert(
    piece=Piece(part=Window1X4X3WithoutShutterTabs, colour=Light_Blue),
    studs_x=8,
    brick_row=16,
)
wall.insert(
    piece=Piece(part=Door1X4X6Frame, colour=Tan),
    studs_x=20,
    brick_row=0,
)

scene.place_at(wall, studs_x=0, plates_y=0, studs_z=0, facing="north")

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Wall with window wall test rendered to wall_with_window_wall_test.mpd")
