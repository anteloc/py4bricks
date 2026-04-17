from pathlib import Path

from py4bricks.library.colours import Blue, White
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm.box import Box
from py4bricks.llm.roofs import PitchedRoof
from py4bricks.pieces import Piece

# Create a box with specific dimensions and colour
base = Box(
    box_width_studs=12,
    box_depth_studs=20,
    box_height_bricks=12,
    colour=White,
)


roof = PitchedRoof(
    box_to_cover=base,
    ridge_orientation="north-south",
    colour=Blue,
)

reprs = [repr(base), repr(roof)]

Path(Path(__file__).parent / "roofs_demo.mpd").write_text("\n".join(reprs))

