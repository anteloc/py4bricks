"""Sloped bricks stacked like gables on a roof would do, ridge built by a double sided slope brick,
on top of symmetrical support bricks.

The current layout causes for both last gables to meet at the top, and the double slope/tile 1x3, 
placed on top of both and joining them together, constitutes the ridge.
"""
from pathlib import Path

from py4bricks.colour import Colour
from py4bricks.library.colours import Blue, Red
from py4bricks.library.parts.bricks import (
    Brick1X1,
    Brick1X2,
)
from py4bricks.library.parts.slopes import (
    SlopeBrick452X1,
    SlopeBrick452X1Double,
)
from py4bricks.llm import Group, Scene
from py4bricks.pieces import Piece


def debug_add_origin_marker(scene: Scene, piece: Piece, colour: Colour) -> None:
    origin_marker = Piece(part=Brick1X1, colour=colour)
    origin_marker.position = piece.position
    scene.add(origin_marker)

def build_slope(
    height_blocks: int,
    facing: str,
    colour: Colour,
    with_top: bool = False,
) -> Group:

    group = Group()
    slope_part = SlopeBrick452X1

    sign = 1 if facing in ("north", "east") else -1
    back_studs = sign * 1 if facing in ("north", "south") else 0
    right_studs = sign * 1 if facing in ("east", "west") else 0

    slope_1st = Piece(part=slope_part, colour=colour)
    group.place_at(slope_1st, facing=facing)

    prev_slope = slope_1st
    for _ in range(1, height_blocks):
        slope = Piece(part=slope_part, colour=colour)
        group.place_on_top_of(slope,
                            prev_slope,
                            right_studs=right_studs,
                            back_studs=back_studs,
                            facing=facing)
        prev_slope = slope

    if with_top:
        top = Piece(part=SlopeBrick452X1Double, colour=colour)
        group.place_on_top_of(top,
                            prev_slope,
                            right_studs=right_studs,
                            back_studs=back_studs,
                            facing=facing)

    return group

scene = Scene("Gables made of sloped bricks test")

slopes_height_blocks = 5
left_slope_facing = "north"
right_slope_facing = "east"

left_support = Piece(part=Brick1X2, colour=Blue)
right_support = Piece(part=Brick1X2, colour=Blue)

left_slope = build_slope(height_blocks=slopes_height_blocks, facing=left_slope_facing, colour=Red)
right_slope = build_slope(height_blocks=slopes_height_blocks, facing=right_slope_facing, colour=Red, with_top=True)

supports_distance_studs = left_slope.studs_z + right_slope.studs_z + 1

# both base bricks are parallel and facing the same way
scene.place_at(left_support, studs_x=0, plates_y=0, studs_z=0, facing=left_slope_facing)
scene.place_at(right_support, studs_x=0, plates_y=0, studs_z=supports_distance_studs, facing=left_slope_facing)

scene.place_on_top_of(left_slope, left_support, back_studs=-1, facing=left_slope_facing)
scene.place_on_top_of(right_slope, right_support, back_studs=1, facing=right_slope_facing)

scene.render_file(Path(__file__).with_suffix(".mpd"))

print(f"Left slope placed with position {left_slope.position} and dimensions {left_slope.studs_x} x {left_slope.plates_y} x {left_slope.studs_z}")
print("Gables made of sloped bricks test rendered to gables_test.mpd")
