from pathlib import Path

from py4bricks.library.colours import Blue, Green, Red, Rubber_Dark_Azure, Yellow, White, Light_Orange
from py4bricks.library.parts.bricks import (
    Brick1X2,
    Brick2X2RoundWithoutReinforcement,
    Brick2X10,
    Brick2X2,
)
from py4bricks.llm import Column, Porch, Balcony, Scene, BricksRow
from py4bricks.pieces import Piece

scene = Scene("Primitives structures samples")

bricks_row = BricksRow(
    brick_piece=Piece(part=Brick2X10, colour=Light_Orange),
    width_studs=13,
    filler_brick_pieces=[Piece(part=Brick2X2, colour=Light_Orange)],
    colour=Light_Orange,
)

scene.place_at(bricks_row, studs_x=100, studs_z=100, facing="east")

file_path = Path(__file__).with_suffix(".mpd")
scene.render_file(file_path)
print(f"Primitives test rendered to {file_path.name}")
