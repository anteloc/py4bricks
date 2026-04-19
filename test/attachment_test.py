"""Tests for attaching pieces to each other, in all four directions.

When the center piece is facing north:

- back is oriented towards north
- front is oriented towards south
- right is oriented towards east
- left is oriented towards west

"""


from pathlib import Path

from py4bricks.library.colours import Blue as Back_Blue
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
scene.place_at(piece=origin_marker, studs_x=0, plates_y=0, studs_z=0, orientation="north")

center = Piece(part=Brick1X2, colour=Center_White)
scene.place_at(piece=center, studs_x=0, plates_y=0, studs_z=0, orientation="north")

back_piece = Piece(part=Brick1X2, colour=Back_Blue)
scene.attach_to(piece=back_piece, to=center, side="back")

front_piece = Piece(part=Brick1X2, colour=Front_Red)
scene.attach_to(piece=front_piece, to=center, side="front")

right_piece = Piece(part=Brick1X2, colour=Right_Yellow)
scene.attach_to(piece=right_piece, to=center, side="right")

left_piece = Piece(part=Brick1X2, colour=Left_Orange)
scene.attach_to(piece=left_piece, to=center, side="left")

# no need to explicitly add pieces to the scene, since place_at and attach_to already add them
scene.render_file(Path(__file__).parent / __file__.replace(".py", ".mpd"))
