from pathlib import Path

from py4bricks.library.colours import Blue, White
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm.box import Box
from py4bricks.pieces import Piece

# Create a box with specific dimensions and colour
box = Box(
    box_width_studs=10,
    box_depth_studs=20,
    box_height_bricks=12,
    colour=White,
)

# add a window on the north wall of the box
north_wall = box.wall_layout["north_wall"]
window_piece = Piece(
    colour=Blue,
    part=Window1X4X3WithoutShutterTabs,
)
north_wall.insert(window_piece, at_studs_x=2, at_bricks_y=1)

Path(Path(__file__).parent / "box_demo.mpd").write_text(repr(box))

