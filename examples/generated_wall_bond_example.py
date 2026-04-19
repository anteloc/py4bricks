"""
Wall with running bond pattern, primarily made of Brick1X2 pieces.

Plan:
- Dimensions: 10 studs wide (X), 1 stud deep (Z=0), 5 bricks high
- Colour: Red throughout
- Even rows (0, 2, 4): 5 × Brick1X2 at studs 0-1, 2-3, 4-5, 6-7, 8-9
- Odd rows  (1, 3)  : Brick1X1 filler at stud 0
                      + 4 × Brick1X2 at studs 1-2, 3-4, 5-6, 7-8
                      + Brick1X1 filler at stud 9
- Horizontal chaining: scene.attach_to(..., side="right")
- Vertical stacking  : Piece.place_on_top(of=<leftmost piece of previous row>)
                       using offset_lr_studs to shift the new row's anchor ±1 stud
- prev_row_leftmost always points to stud 0 of the previous row so Y stacks cleanly
"""

from pathlib import Path

from py4bricks.library.colours import Red
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2
from py4bricks.llm.scene import Scene
from py4bricks.pieces import Piece

# --- constants ---
WALL_WIDTH_STUDS = 10
WALL_HEIGHT_BRICKS = 5

EVEN_ROW_BRICKS = WALL_WIDTH_STUDS // 2              # 5 × Brick1X2
ODD_ROW_BRICKS  = (WALL_WIDTH_STUDS - 2) // 2        # 4 × Brick1X2 + 2 × Brick1X1 fillers

scene = Scene()

# --- row 0 (even): place anchor, then attach right ---
row0_anchor = Piece(part=Brick1X2, colour=Red)
scene.place_at(piece=row0_anchor, studs_x=0, plates_y=0, studs_z=0, orientation="north")

prev = row0_anchor
for _ in range(EVEN_ROW_BRICKS - 1):
    brick = Piece(part=Brick1X2, colour=Red)
    prev = scene.attach_to(piece=brick, to=prev, side="right")

# leftmost piece of row 0 is the anchor (Brick1X2 at stud 0)
prev_row_leftmost = row0_anchor

# --- rows 1 to WALL_HEIGHT_BRICKS-1 ---
for row in range(1, WALL_HEIGHT_BRICKS):
    if row % 2 == 1:
        # Odd row: Brick1X1 filler at stud 0, then 4×Brick1X2, then Brick1X1 filler at stud 9

        # left filler — sits directly above stud 0 of the row below
        left_filler = Piece(part=Brick1X1, colour=Red)
        Piece.place_on_top(piece=left_filler, of=prev_row_leftmost)
        scene.add_piece(left_filler)

        # first Brick1X2 of this row — shifted 1 stud right from the leftmost below
        row_anchor = Piece(part=Brick1X2, colour=Red)
        Piece.place_on_top(piece=row_anchor, of=prev_row_leftmost, right_studs=1)
        scene.add_piece(row_anchor)

        prev = row_anchor
        for _ in range(ODD_ROW_BRICKS - 1):
            brick = Piece(part=Brick1X2, colour=Red)
            prev = scene.attach_to(piece=brick, to=prev, side="right")

        # right filler — attach to the rightmost Brick1X2 of this row
        right_filler = Piece(part=Brick1X1, colour=Red)
        scene.attach_to(piece=right_filler, to=prev, side="right")

        # leftmost piece of this odd row is the Brick1X1 left filler at stud 0
        prev_row_leftmost = left_filler

    else:
        # Even row: same layout as row 0, stacked on top of the leftmost piece below
        row_anchor = Piece(part=Brick1X2, colour=Red)
        Piece.place_on_top(piece=row_anchor, of=prev_row_leftmost)
        scene.add_piece(row_anchor)

        prev = row_anchor
        for _ in range(EVEN_ROW_BRICKS - 1):
            brick = Piece(part=Brick1X2, colour=Red)
            prev = scene.attach_to(piece=brick, to=prev, side="right")

        # leftmost piece of this even row is the Brick1X2 anchor at stud 0
        prev_row_leftmost = row_anchor

scene.render_file(Path(__file__).parent / "generated_wall_bond_example.mpd")
print("Bond wall rendered to generated_wall_bond_example.mpd")
