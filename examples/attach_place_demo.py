from py4bricks.pieces import Piece
from py4bricks.library.colours import Red, Green, Blue, Yellow, White
from py4bricks.library.parts.bricks import Brick1X1
from pathlib import Path
from py4bricks.geometry import Identity, XAxis, YAxis, ZAxis

central_piece = Piece(part=Brick1X1, colour=White)
central_piece.rotation = Identity().rotate(49, axis=YAxis)

north_piece = Piece(part=Brick1X1, colour=Red)
south_piece = Piece(part=Brick1X1, colour=Green)
east_piece = Piece(part=Brick1X1, colour=Blue)
west_piece = Piece(part=Brick1X1, colour=Yellow)

Piece.attach(north_piece, to=central_piece, side="front")
Piece.attach(south_piece, to=central_piece, side="back")
Piece.attach(east_piece, to=central_piece, side="right")
# Piece.attach(west_piece, to=central_piece, side="left")
Piece.place_on_top(piece=west_piece, of=central_piece)
reprs = [repr(central_piece), repr(north_piece), repr(south_piece), repr(east_piece), repr(west_piece)]

Path(Path(__file__).parent / "attach_place_demo.mpd").write_text("\n".join(reprs))

