"""wall.py — Generate a brick wall with a window and a door, write to wall.mpd."""

from pathlib import Path

from py4bricks.geometry import Identity, Vector
from py4bricks.library.colours import Dark_Blue, Red, White
from py4bricks.library.parts.doors import Door1X4X5LeftWithTransClearGlass, Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3, Window1X4X3WithoutShutterTabs
from py4bricks.llm.wall import Wall
from py4bricks.pieces import Piece

# 10 studs wide, 8 brick rows tall — room for a 4-stud window (plates_y=10)
# and a 1-stud door (plates_y=16, i.e. ~5⅓ rows).
wall = Wall(length=20, height=8, facing="north", colour=Red, name="front_wall")

window = Piece(
    colour=White,
    position=Vector(0, 0, 0),
    rotation=Identity(),
    part=Window1X4X3WithoutShutterTabs,
    # part=Window1X4X3,
)
door = Piece(
    colour=Dark_Blue,
    position=Vector(0, 0, 0),
    rotation=Identity(),
    part=Door1X4X6Frame,
    # part=Door1X4X5LeftWithTransClearGlass,
)

# Window: 4 studs wide, 10 plates tall — placed 1 stud from left, 3 rows up.
wall.insert(window, x=1, y=3)

# Door: 1 stud wide, 16 plates tall — placed at the base, 6 studs from left.
wall.insert(door, x=15, y=0)

Path(Path(__file__).parent / "wall_example.mpd").write_text(repr(wall))
