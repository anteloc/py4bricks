"""A Box with a Roof on top, made of sloped bricks."""
from pathlib import Path

from py4bricks.colour import Colour
from py4bricks.library.colours import White, Red
from py4bricks.library.parts.bricks import (
    Brick1X1,
    Brick1X2,
)
from py4bricks.library.parts.slopes import (
    SlopeBrick452X1,
    SlopeBrick452X1Double,
)
from py4bricks.llm import Group, Scene, Box, Roof
from py4bricks.pieces import Piece


def debug_add_origin_marker(scene: Scene, piece: Piece, colour: Colour) -> None:
    origin_marker = Piece(part=Brick1X1, colour=colour)
    origin_marker.position = piece.position
    scene.add(origin_marker)


scene = Scene("A Box with a Roof on top, made of sloped bricks test")

box = Box(name="Box", 
          width_studs=10, 
          length_studs=20, 
          height_bricks=3, 
          colour=White, 
          bonded=True)

scene.add(box)

roof = Roof(name="Roof", 
            width_studs=box.width_studs, 
            length_studs=box.length_studs, 
            # ridge_running="east-west", 
            ridge_running="north-south", 
            colour=Red)

scene.place_on_top_of(roof, box)

scene.render_file(Path(__file__).with_suffix(".mpd"))

print("A Box with a Roof on top, made of sloped bricks test rendered to roof_test.mpd")
