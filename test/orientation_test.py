"""
Tests for orienting and placing Brick1X2 pieces together:

- In all four orientations
- The origin stud is located at the left of the piece
- This makes the piece asymmetrical relative to its origin stud
- Which affects placement.

When the center piece is facing north:

- north is at the back
- south is at the front
- east is at the right
- west is at the left

"""

from pathlib import Path

from py4bricks.library.colours import Blue as North_Blue
from py4bricks.library.colours import Medium_Azure
from py4bricks.library.colours import Orange as West_Orange
from py4bricks.library.colours import Red as South_Red
from py4bricks.library.colours import White as Center_White
from py4bricks.library.colours import Yellow as East_Yellow
from py4bricks.library.parts.bars import Spike2_4LWith4FinsWithBar0_4L
from py4bricks.library.parts.bricks import Brick1X2
from py4bricks.llm.scene import Scene
from py4bricks.pieces import Piece

scene = Scene()

origin_marker = Piece(part=Spike2_4LWith4FinsWithBar0_4L, colour=Medium_Azure)
Piece.place_at(piece=origin_marker, studs_x=0, plates_y=0, studs_z=0, orientation="north")

# placed at the center of the grid
center = Piece(part=Brick1X2, colour=Center_White)
Piece.place_at(piece=center, studs_x=0, plates_y=0, studs_z=0, orientation="north")

# placed at grid on (0, 0, 1), in touch with center, and rotated to face north
north_piece = Piece(part=Brick1X2, colour=North_Blue)
Piece.place_at(piece=north_piece, studs_x=0, plates_y=0, studs_z=1, orientation="north")

# placed at grid on (0, 0, -1), in touch with center, and rotated to face south
south_piece = Piece(part=Brick1X2, colour=South_Red)
Piece.place_at(piece=south_piece, studs_x=0, plates_y=0, studs_z=-1, orientation="south")

# placed at grid on (2, 0, 0), in touch with center, and rotated to face east
# NOTE: account for the fact that Brick1X2 is 2 studs long, so its origin must be placed 
# at studs_x=2 to avoid overlapping with the center piece at studs_x=0
east_piece = Piece(part=Brick1X2, colour=East_Yellow)
Piece.place_at(piece=east_piece, studs_x=2, plates_y=0, studs_z=0, orientation="east")

# placed at grid on (-1, 0, 0), in touch with center, and rotated to face west
west_piece = Piece(part=Brick1X2, colour=West_Orange)
Piece.place_at(piece=west_piece, studs_x=-1, plates_y=0, studs_z=0, orientation="west")

scene.add_piece(piece=origin_marker)
scene.add_piece(piece=center)
scene.add_piece(piece=north_piece)
scene.add_piece(piece=south_piece)
scene.add_piece(piece=east_piece)
scene.add_piece(piece=west_piece)

scene.render_file(Path(__file__).parent / __file__.replace(".py", ".mpd"))
