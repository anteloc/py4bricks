"""
Tests for placing Brick1X1 pieces together, in all four orientations, and with different parts and colours.
For this case, all pieces are symmetrical.

When the center piece is facing north:

- north is at the back
- south is at the front
- east is at the right
- west is at the left

"""
from pathlib import Path

from py4bricks.library.colours import Blue as North_Blue
from py4bricks.library.colours import Orange as West_Orange
from py4bricks.library.colours import Red as South_Red
from py4bricks.library.colours import White as Center_White
from py4bricks.library.colours import Yellow as East_Yellow
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.llm.scene import Scene
from py4bricks.pieces import Piece

# Other systems, such as the Toronto PATH map, use Blue (North), Red (South), Yellow (East), and Orange (West)

scene = Scene("Orientation test - 1-stud bricks")

# placed at the center of the grid
center = Piece(part=Brick1X1, colour=Center_White)
scene.place_at(center, studs_x=0, plates_y=0, studs_z=0, facing="north")

# placed at grid on (studs_x, plates_y, studs_z), in touch with center, and rotated to face north
north_piece = Piece(part=Brick1X1, colour=North_Blue)
scene.place_at(north_piece, studs_x=0, plates_y=0, studs_z=1, facing="north")

# placed at grid on (studs_x, plates_y, studs_z), in touch with center, and rotated to face south
south_piece = Piece(part=Brick1X1, colour=South_Red)
scene.place_at(south_piece, studs_x=0, plates_y=0, studs_z=-1, facing="south")

# placed at grid on (studs_x, plates_y, studs_z), in touch with center, and rotated to face east
east_piece = Piece(part=Brick1X1, colour=East_Yellow)
scene.place_at(east_piece, studs_x=1, plates_y=0, studs_z=0, facing="east")

# placed at grid on (studs_x, plates_y, studs_z), in touch with center, and rotated to face west
west_piece = Piece(part=Brick1X1, colour=West_Orange)
scene.place_at(west_piece, studs_x=-1, plates_y=0, studs_z=0, facing="west")

scene.add(center)
scene.add(north_piece)
scene.add(south_piece)
scene.add(east_piece)
scene.add(west_piece)

scene.render_file(Path(__file__).parent / __file__.replace(".py", ".mpd"))
