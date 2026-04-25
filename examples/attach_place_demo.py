from pathlib import Path

from py4bricks.geometry import Identity, YAxis
from py4bricks.library.colours import Blue, Green, Red, White, Yellow
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.pieces import Piece

central_piece = Piece(part=Brick1X1, colour=White)
central_piece.rotation = Identity().rotate(49, axis=YAxis)

front_piece = Piece(part=Brick1X1, colour=Red)
back_piece = Piece(part=Brick1X1, colour=Green)
right_piece = Piece(part=Brick1X1, colour=Blue)
top_piece = Piece(part=Brick1X1, colour=Yellow)

Piece.attach_to(front_piece, to=central_piece, side="front")
Piece.attach_to(back_piece, to=central_piece, side="back")
Piece.attach_to(right_piece, to=central_piece, side="right")
# Piece.attach(left_piece, to=central_piece, side="left")
Piece.place_on_top(piece=top_piece, of=central_piece)
reprs = [repr(central_piece), repr(front_piece), repr(back_piece), repr(right_piece), repr(top_piece)]

Path(Path(__file__).parent / "attach_place_demo.mpd").write_text("\n".join(reprs))

