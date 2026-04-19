"""
Wall made of Brick1X1 pieces.

Plan:
- Dimensions : 10 studs wide (X axis), 1 stud deep (Z=0), 5 bricks high
- Brick1X1 height: 3 plates, so rows are at plates_y = 0, 3, 6, 9, 12
- All bricks face north (wall face looks south toward viewer)
- Colour: Red — classic brick wall look
- Origin: bottom-left corner at (studs_x=0, plates_y=0, studs_z=0)
- Layout: double loop — outer over height rows, inner over width columns
"""

from pathlib import Path

from py4bricks.library.colours import Red
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.llm.scene import Scene
from py4bricks.pieces import Piece

# --- constants ---
WALL_WIDTH_STUDS = 10
WALL_HEIGHT_BRICKS = 5
BRICK_HEIGHT_PLATES = 3   # standard LEGO brick = 3 plates tall

scene = Scene()

for row in range(WALL_HEIGHT_BRICKS):
    for col in range(WALL_WIDTH_STUDS):
        brick = Piece(part=Brick1X1, colour=Red)
        scene.place_at(
            piece=brick,
            studs_x=col,
            plates_y=row * BRICK_HEIGHT_PLATES,
            studs_z=0,
            orientation="north",
        )

scene.render_file(Path(__file__).parent / "generated_wall_example.mpd")
print("Wall rendered to generated_wall_example.mpd")
