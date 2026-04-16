"""wall_demo.py — Generate brick walls at different positions, in different ways.

Wall: rectangular brick wall

A Wall is a rectangular surface of bricks, defined by:
  - length (studs along its face)
  - height (brick rows)
  - facing (north/south/east/west)
  - It lives in its own local coordinate space:
    - X axis: along the wall face, 0 = left end, length = right end (studs)
    - Y axis: up from the wall base, 0 = bottom (plates or bricks)
    - Z axis: wall thickness, depending on the bricks used (LDU)

Public Methods:
  ----------
  __init__(name: str, studs_width: int = 0, bricks_height: int = 0, plates_height: int = 0, position: Vector = Origin(), facing: Literal["north", "south", "east", "west"] = "north", colour: Colour = White) -> Wall
      Create a new wall. Provide either bricks_height or plates_height for height, but not both.

  from_dimensions(name: str, studs_width: int, bricks_height: int = 0, plates_height: int = 0, colour: Colour = White) -> Wall
      Create a wall from explicit width and height dimensions.

  from_references(name: str, same_width_as: Group | Piece, same_height_as: Group | Piece, colour: Colour = White) -> Wall
      Create a wall by copying width and height dimensions from reference objects.

  insert(piece: Piece, at_studs_x: int, at_plates_y: int = -1, at_bricks_y: int = -1) -> None
      Place a piece (e.g. window, door...) and remove bricks to make room for it. Params plates_y and bricks_y are mutually exclusive.

  opening(at_studs_x: int, studs_width: int, at_plates_y: int = -1, plates_height: int = 0, at_bricks_y: int = -1, bricks_height: int = 0) -> None
      Create an opening on the wall with the given width and height. On Y coordinates, choose to work either on bricks or plates, but not both.

  place(at: Vector, facing: Literal["north", "south", "east", "west"]) -> None
      Place the wall at the given world position and facing direction.

  place_parallel_to(other_wall: Wall, distance_studs: int) -> None
      Place this wall parallel to a reference wall at the given distance (in studs). Positive distance places wall in front; negative places behind. Both walls share the same facing direction.
"""


from pathlib import Path

from py4bricks.geometry import Vector, proportional
from py4bricks.library.colours import (
    Dark_Blue,
    Neon_Yellow,
    Red,
    Rose_Pink,
    Sand_Green,
    White,
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

window2 = window.copy()

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


one_sixth_x = proportional(north_wall.studs_width, (1, 6))
three_fifths_y = proportional(north_wall.plates_height, (3, 5))

# OK: this is perfectly aligned and placed in the wall
north_wall.insert(window, at_studs_x=one_sixth_x, at_plates_y=three_fifths_y)

# doors are always at_bricks_y=0, standing on the ground
door_center_x = proportional(north_wall.studs_width, (1, 2)) + proportional(door.studs_x, (1, 2))
north_wall.insert(door, at_studs_x=door_center_x, at_bricks_y=0)

# Oriented west, same dimensions as north wall, this time we will change the wall's position and rotation
west_wall = Wall.from_references(name="west_wall", 
                                 same_height_as=north_wall, 
                                 same_width_as=north_wall, 
                                 colour=Dark_Blue)
west_wall.place(at=Vector(-20, 0, 0), facing="west")


# BUG: this places a window outside the wall plane and displaced relative to the opening it belongs to
west_wall.insert(window2, at_studs_x=one_sixth_x, at_plates_y=three_fifths_y)


# Same dimensions as west_wall, parallel to west wall at a distance of 20 studs in front of west_wall
parallel_west_front = Wall.from_references(name="parallel_west_front", 
                                           same_height_as=west_wall, 
                                           same_width_as=west_wall, 
                                           colour=Rose_Pink)
parallel_west_front.place_parallel_to(other_wall=west_wall, distance_studs=20)

# Create an opening at ground level, at an arbitrary horizontal position
parallel_west_front.opening(at_studs_x=2, at_bricks_y=0, studs_width=4, bricks_height=9)

# Half the width of west wall, double the height of north wall, parallel to west wall at a distance of 30 studs behind west wall
half_w_w_width = proportional(west_wall.studs_width, (1, 2))
dbl_n_w_height = proportional(north_wall.plates_height, (2, 1))
parallel_west_behind= Wall.from_dimensions(name="parallel_west_behind", 
                                          studs_width=half_w_w_width, 
                                          plates_height=dbl_n_w_height, 
                                          colour=Neon_Yellow)
parallel_west_behind.place_parallel_to(other_wall=west_wall, distance_studs=-30)

east_wall = Wall.from_references(name="east_wall", 
                                 same_height_as=north_wall, 
                                 same_width_as=north_wall, 
                                 colour=Sand_Green)
east_wall.place(at=Vector(200, 0, 100), facing="east")

south_wall = Wall.from_references(name="south_wall", 
                                 same_height_as=north_wall, 
                                 same_width_as=north_wall, 
                                 colour=White)
south_wall.place(at=Vector(-50, 0, -20), facing="south")


reprs = [
    repr(north_wall), 
    repr(west_wall), 
    repr(parallel_west_front), 
    repr(parallel_west_behind),
    repr(east_wall),
    repr(south_wall)
]
Path(Path(__file__).parent / "wall_demo.mpd").write_text("\n".join(reprs))
