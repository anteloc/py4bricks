"""wall_example.py — Generate a brick wall with a window and a door, write to wall.mpd."""

from pathlib import Path

from py4bricks.geometry import Identity, Vector
from py4bricks.library.colours import (
    Dark_Blue,
    Red,
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

# 15 studs wide, 10 brick rows tall — room for a 4-stud window (plates_y=15)
# and a 4-stud door
wall = Wall(studs_width=15, bricks_height=10, facing="north", colour=Red, name="front_wall")

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
wall.insert(window, studs_x=1, plates_y=15)

# Door: 1 stud wide, 16 plates tall — placed at the base, 6 studs from left.
wall.insert(door, studs_x=6, bricks_y=0)

Path(Path(__file__).parent / "wall_example.mpd").write_text(repr(wall))
