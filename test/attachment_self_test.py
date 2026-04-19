"""Tests for:
- Attaching pieces relative to each other in all four directions
- Chaining attachments.

When the center piece is facing north:

- back is oriented towards north
- front is oriented towards south
- right is oriented towards east
- left is oriented towards west

"""


from pathlib import Path

from py4bricks.library.colours import Blue as Back_Blue
from py4bricks.library.colours import Dark_Green as Third_Green
from py4bricks.library.colours import Green as Second_Green
from py4bricks.library.colours import Light_Green as First_Green
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

# these two marker and center are implicitly added to the scene
origin_marker = Piece(part=Spike2_4LWith4FinsWithBar0_4L, colour=Medium_Azure)
scene.place_at(piece=origin_marker, studs_x=0, plates_y=0, studs_z=0, orientation="north")

# attach several pieces to the center piece, in all four directions
# pieces attached to others already present in the scene will be added to the scene automatically, so we don't need to explicitly add them
center = Piece(part=Brick1X2, colour=Center_White)
scene.place_at(piece=center, studs_x=0, plates_y=0, studs_z=0, orientation="north")

back_piece = Piece(part=Brick1X2, colour=Back_Blue)
center.attach(piece=back_piece, side="back")

front_piece = Piece(part=Brick1X2, colour=Front_Red)
center.attach(piece=front_piece, side="front")

right_piece = Piece(part=Brick1X2, colour=Right_Yellow)
center.attach(piece=right_piece, side="right")

left_piece = Piece(part=Brick1X2, colour=Left_Orange)
center.attach(piece=left_piece, side="left")


# attach pieces sequentially, in a fluent interface style
# the first piece is not in the scene, which makes mandatory adding all of them to
# the scene explicitly, which is a good test of that functionality
first_piece = Piece(part=Brick1X2, colour=First_Green)
Piece.place_at(piece=first_piece, studs_x=20, plates_y=0, studs_z=0, orientation="east")

second_piece = Piece(part=Brick1X2, colour=Second_Green)
third_piece = Piece(part=Brick1X2, colour=Third_Green)

first_piece.attach(piece=second_piece, side="right").attach(piece=third_piece, side="right")

scene.add_piece(piece=first_piece)
scene.add_piece(piece=second_piece)
scene.add_piece(piece=third_piece)

scene.render_file(Path(__file__).parent / __file__.replace(".py", ".mpd"))
