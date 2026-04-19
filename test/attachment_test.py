"""Tests for attaching pieces to each other, in all six directions.

When the center piece is facing north:

- back   is oriented towards north  (positive Z)
- front  is oriented towards south  (negative Z)
- right  is oriented towards east   (positive X)
- left   is oriented towards west   (negative X)
- top    is stacked flush on top    (positive Y)
- bottom is stacked flush below     (negative Y)

"""


from pathlib import Path

from py4bricks.library.colours import Blue as Back_Blue
from py4bricks.library.colours import Brown as Bottom_Brown
from py4bricks.library.colours import Green as Top_Green
from py4bricks.library.colours import Medium_Azure
from py4bricks.library.colours import Orange as Left_Orange
from py4bricks.library.colours import Red as Front_Red
from py4bricks.library.colours import White as Center_White
from py4bricks.library.colours import Yellow as Right_Yellow
from py4bricks.library.parts.bars import Spike2_4LWith4FinsWithBar0_4L
from py4bricks.library.parts.bricks import Brick1X2
from py4bricks.llm.scene import Scene
from py4bricks.pieces import Piece

scene = Scene()

origin_marker = Piece(part=Spike2_4LWith4FinsWithBar0_4L, colour=Medium_Azure)
scene.place_at(piece=origin_marker, studs_x=0, plates_y=0, studs_z=0, facing="north")

center = Piece(part=Brick1X2, colour=Center_White)
scene.place_at(piece=center, studs_x=0, plates_y=0, studs_z=0, facing="north")

back_piece   = Piece(part=Brick1X2, colour=Back_Blue)
front_piece  = Piece(part=Brick1X2, colour=Front_Red)
right_piece  = Piece(part=Brick1X2, colour=Right_Yellow)
left_piece   = Piece(part=Brick1X2, colour=Left_Orange)
top_piece    = Piece(part=Brick1X2, colour=Top_Green)
bottom_piece = Piece(part=Brick1X2, colour=Bottom_Brown)

center.attach(piece=back_piece,   side="back")
center.attach(piece=front_piece,  side="front")
center.attach(piece=right_piece,  side="right")
center.attach(piece=left_piece,   side="left")
center.attach(piece=top_piece,    side="top")
center.attach(piece=bottom_piece, side="bottom")

# piece.attach() auto-registers each new piece into the scene via scene.add_piece()
scene.render_file(Path(__file__).parent / __file__.replace(".py", ".mpd"))
