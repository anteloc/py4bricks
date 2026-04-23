"""
Sloped bricks stacked like gables on a roof would do, ridge built by a double sided slope brick.

The current layout causes for both 2nd gables to meet at the top, and the double slope/tile 1x3, placed on top of both, constitutes the ridge.
"""
from py4bricks.colour import Colour
from turtle import right

from pathlib import Path

from py4bricks.library.colours import White, Blue, Red, Green, Medium_Azure
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2, Brick10X10, Brick2X1WithPositioningRockets
from py4bricks.library.parts.slopes import SlopeBrick452X1, SlopeBrick451X1Double, SlopeBrick452X1Double
from py4bricks.library.parts.tiles import Tile1X3

from py4bricks.llm import Scene, Group
from py4bricks.pieces import Piece

def debug_add_origin_marker(scene: Scene, piece: Piece, colour: Colour) -> None:
    origin_marker = Piece(part=Brick1X1, colour=colour)
    origin_marker.position = piece.position
    scene.add(origin_marker)

def build_slope(
    height_blocks: int,
    facing: str,
    colour: Colour,
) -> Group:

    group = Group()

    sign = 1 if facing in ("north", "east") else -1
    back_studs = sign * 1 if facing in ("north", "south") else 0
    right_studs = sign * 1 if facing in ("east", "west") else 0

    slope_1st = Piece(part=SlopeBrick452X1, colour=colour)
    group.place_at(slope_1st, facing=facing)

    prev_slope = slope_1st
    for _ in range(1, height_blocks):
        slope = Piece(part=SlopeBrick452X1, colour=colour)
        group.place_on_top_of(slope, 
                            prev_slope, 
                            right_studs=right_studs, 
                            back_studs=back_studs, 
                            facing=facing)
        prev_slope = slope

    return group

scene = Scene("Gables made of sloped bricks test")

slopes_height_blocks = 5

left_support = Piece(part=Brick1X2, colour=Blue)
scene.place_at(left_support, studs_x=0, plates_y=0, studs_z=0, facing="north")

left_slope = build_slope(scene, left_support, height_blocks=slopes_height_blocks, facing="north", colour=Red)

scene.place_on_top_of(left_slope, left_support, right_studs=0, facing="north")

print(f"Left slope placed with position {left_slope.position} and dimensions {left_slope.studs_x} x {left_slope.plates_y} x {left_slope.studs_z}")

right_support = Piece(part=Brick1X2, colour=Blue)
scene.place_at(right_support, studs_x=left_slope.studs_x, plates_y=0, studs_z=left_slope.studs_z, facing="south")

# right_slope = build_slope(scene, right_support, height_blocks=slopes_height_blocks, facing="south", colour=Red)
# scene.place_on_top_of(right_slope, right_support, right_studs=0, facing="west")

# top = Piece(part=Brick1X1, colour=Red)
# top = Piece(part=SlopeBrick452X1Double, colour=Red)
# scene.place_on_top_of(top, gable_2nd_left, back_studs=1, facing="north")


scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Gables made of sloped bricks test rendered to gables_test.mpd")
