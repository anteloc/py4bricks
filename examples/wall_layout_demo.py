from pathlib import Path

from py4bricks.geometry import Vector
from py4bricks.library.colours import Blue, White
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm.wall_layout import WallLayout
from py4bricks.pieces import Piece

# Create a wall layout with specific dimensions and colour
wall_layout = WallLayout(
    walls_height_bricks=10,
    first_wall_position=Vector(0, 0, 0),
    colour=White,
)

wall_layout.append_wall(name="a_first_wall", wall_width_studs=4, facing="north")
wall_layout.append_wall(name="some_second_wall_following", wall_width_studs=8, facing="east")
wall_layout.append_wall(name="a_third_wall_following_the_second", wall_width_studs=16, facing="north")
wall_layout.append_wall(name="wall_with_window", wall_width_studs=32, facing="west")

# get the wall with window and insert a window in it
wall_with_window = wall_layout["wall_with_window"]
window_piece = Piece(
    colour=Blue,
    part=Window1X4X3WithoutShutterTabs,
)

wall_with_window.insert(window_piece, at_studs_x=2, at_bricks_y=1)

Path(Path(__file__).parent / "wall_layout_demo.mpd").write_text(repr(wall_layout))


