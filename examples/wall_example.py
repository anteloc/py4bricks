"""wall_example.py — Generate a brick wall with a window and a door, write to wall.mpd."""

from pathlib import Path

from py4bricks.geometry import Identity, Vector
from py4bricks.library.colours import (
    Dark_Blue,
    Sand_Green,
    Rose_Pink,
    Red,
    White,
    Neon_Yellow,
)
from py4bricks.library.parts.doors import (
    Door1X4X6Frame,
)
from py4bricks.library.parts.windows import (
    Window1X4X3WithoutShutterTabs,
)
from py4bricks.llm.wall import Wall
from py4bricks.pieces import Piece

# 15 studs wide, 10 brick rows tall — room for a 4-stud window (plates_y=15)
# and a 4-stud door
north_wall = Wall(studs_width=15, bricks_height=10, facing="north", colour=Red, name="north_wall")
# the other cardinal directions will have the same dimensions as the north wall, but different colours
west_wall = Wall(same_height_as=north_wall, same_width_as=north_wall, facing="west", colour=Dark_Blue, name="west_wall")
south_wall = Wall(same_height_as=north_wall, same_width_as=north_wall, facing="south", colour=Sand_Green, name="south_wall")
east_wall = Wall(same_height_as=north_wall, same_width_as=north_wall, facing="east", colour=Neon_Yellow, name="east_wall")

parallel_east = Wall(same_height_as=east_wall, same_width_as=east_wall, parallel_to=(east_wall, -10), colour=Rose_Pink, name="parallel_east_wall")

window = Piece(
    colour=White,
    position=Vector(0, 0, 0),
    rotation=Identity(),
    part=Window1X4X3WithoutShutterTabs,
)
door = Piece(
    colour=Dark_Blue,
    position=Vector(0, 0, 0),
    rotation=Identity(),
    part=Door1X4X6Frame,
)

# Window: 4 studs wide, 10 plates tall — placed 1 stud from left, 3 rows up.
east_wall.insert(window, at_studs_x=1, at_plates_y=15)

# Door: 1 stud wide, 16 plates tall — placed at the base, 6 studs from left.
east_wall.insert(door, at_studs_x=6, at_bricks_y=0)



Path(Path(__file__).parent / "wall_example.mpd").write_text(repr(north_wall) + "\n" + repr(west_wall) + "\n" + repr(south_wall) + "\n" + repr(east_wall) + "\n" + repr(parallel_east))
