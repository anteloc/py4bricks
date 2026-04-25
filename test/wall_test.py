"""
Wall different wall features tests — using the Wall API.

"""

from pathlib import Path

from py4bricks.library.colours import Light_Blue, Light_Grey, Tan
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Scene, Wall
from py4bricks.pieces import Piece

scene = Scene("Wall with window and door frame test")

wall = Wall(width_studs=40, height_bricks=35, colour=Light_Grey, bonded=True)

scene.place_at(wall, studs_x=0, plates_y=0, studs_z=0, facing="east")

parallel_wall = wall.parallel_wall(
    name="parallel wall",
    to_wall=wall,
    at_distance_studs=-25, # negative = on the opposite side of wall's facing direction
    colour=Light_Blue)

scene.add(parallel_wall)

divider_wall = wall.divider_wall(
    from_wall=wall,
    at_width_studs=5,
    to_parallel_wall=parallel_wall,
    colour=Tan)

scene.add(divider_wall)

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Wall test rendered to wall_test.mpd")
