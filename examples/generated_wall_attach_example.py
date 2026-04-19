"""
Wall made of Brick1X1 pieces, built by attaching bricks to each other.

Plan:
- Dimensions : 10 studs wide (X axis), 1 stud deep (Z=0), 5 bricks high
- All bricks face north (wall face looks south toward viewer)
- Colour: Red — classic brick wall look
- Origin: bottom-left corner anchor at (studs_x=0, plates_y=0, studs_z=0)
- Layout:
    - Each row is built by attaching bricks to the right of the previous one
    - Each row above is started by placing its anchor on top of the row below's anchor
      via Piece.place_on_top, then attaching right across
"""

from pathlib import Path

from py4bricks.library.colours import Red
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.llm.scene import Scene
from py4bricks.pieces import Piece

# --- constants ---
WALL_WIDTH_STUDS = 10
WALL_HEIGHT_BRICKS = 5

scene = Scene()

# Place the bottom-left anchor brick
anchor = Piece(part=Brick1X1, colour=Red)
scene.place_at(piece=anchor, studs_x=0, plates_y=0, studs_z=0, orientation="north")

row_anchors = [anchor]

# Build each row
for row in range(WALL_HEIGHT_BRICKS):
    if row == 0:
        row_anchor = anchor
    else:
        # Start this row by stacking on top of the previous row's anchor
        row_anchor = Piece(part=Brick1X1, colour=Red)
        Piece.place_on_top(piece=row_anchor, of=row_anchors[row - 1])
        scene.add_piece(row_anchor)
        row_anchors.append(row_anchor)

    # Attach bricks to the right across the row
    prev = row_anchor
    for _ in range(WALL_WIDTH_STUDS - 1):
        brick = Piece(part=Brick1X1, colour=Red)
        prev = scene.attach_to(piece=brick, to=prev, side="right")

scene.render_file(Path(__file__).parent / "generated_wall_attach_example.mpd")
print("Wall rendered to generated_wall_attach_example.mpd")
