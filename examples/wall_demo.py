"""wall_demo.py — Generate brick walls at different positions, in different ways."""

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

# No need to specify position or rotation, the Wall will take care of that
window = Piece(
    colour=White,
    part=Window1X4X3WithoutShutterTabs,
)

door = Piece(
    colour=Dark_Blue,
    part=Door1X4X6Frame,
)

# Oriented north, with a window and door
north_wall = Wall(name="north_wall", 
                  studs_width=15, 
                  bricks_height=10, 
                  facing="north", 
                  colour=Red)
# north_wall.insert(window, at_studs_x=1, at_plates_y=15)
# doors are always at_bricks_y=0, standing on the ground
# north_wall.insert(door, at_studs_x=6, at_bricks_y=0)

# Oriented west, same dimensions as north wall, this time we will change the wall's position and rotation
west_wall = Wall.from_references(name="west_wall", 
                                 same_height_as=north_wall, 
                                 same_width_as=north_wall, 
                                 colour=Dark_Blue)
west_wall.place(at=Vector(-200, 0, 0), facing="west")

# Same dimensions as west_wall, parallel to west wall at a distance of 20 studs to west_wall's right
parallel_west_right = Wall.from_references(name="parallel_west_right", 
                                           same_height_as=west_wall, 
                                           same_width_as=west_wall, 
                                           colour=Rose_Pink)
parallel_west_right.place_parallel_to(ref_wall=west_wall, distance_studs=20)

# Half the width of west wall, double the height of north wall, parallel to west wall at a distance of 30 studs to west wall's left
HALF_WEST_WALL_WIDTH = west_wall.studs_width // 2
DOUBLE_NORTH_WALL_HEIGHT = north_wall.plates_height * 2
parallel_west_left = Wall.from_dimensions(name="parallel_west_left", 
                                          studs_width=HALF_WEST_WALL_WIDTH, 
                                          plates_height=DOUBLE_NORTH_WALL_HEIGHT, 
                                          colour=Neon_Yellow)
parallel_west_left.place_parallel_to(ref_wall=west_wall, distance_studs=-30)

reprs = [
    repr(north_wall), 
    repr(west_wall), 
    repr(parallel_west_right), 
    repr(parallel_west_left)

]
Path(Path(__file__).parent / "wall_demo.mpd").write_text("\n".join(reprs))
