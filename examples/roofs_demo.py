
from py4bricks.geometry import Vector
from py4bricks.library.colours import Blue, White
from py4bricks.llm.box import Box
from py4bricks.llm.roofs import PitchedRoof

# Create a box with specific dimensions and colour
base = Box(
    box_width_studs=12,
    box_depth_studs=20,
    box_height_bricks=12,
    position=Vector(100, 0, 0),
    colour=White,
)


roof = PitchedRoof(
    box_to_cover=base,
    ridge_orientation="east-west",
    colour=Blue,
)

reprs = [repr(base), repr(roof)]



