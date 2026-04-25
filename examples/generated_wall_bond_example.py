"""
Wall with running bond pattern, primarily made of Brick1X2 pieces.

Plan:
- Dimensions: 10 studs wide (X), 1 stud deep (Z=0), 5 bricks high
- Colour: Red throughout
- Even rows (0, 2, 4): 5 × Brick1X2 at studs 0-1, 2-3, 4-5, 6-7, 8-9
- Odd rows  (1, 3)  : Brick1X1 filler at stud 0
                      + 4 × Brick1X2 at studs 1-2, 3-4, 5-6, 7-8
                      + Brick1X1 filler at stud 9
- Horizontal chaining: piece.attach(side="right") — auto-registers to scene
- Vertical stacking  : scene.place_on_top_of with right_studs=1 for odd-row offset
- prev_row_leftmost always points to stud 0 of the previous row so Y stacks cleanly
"""

from pathlib import Path

from py4bricks.library.colours import Red
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2
from py4bricks.llm.scene import Scene
from py4bricks.pieces import Piece

# --- constants ---
WALL_WIDTH_STUDS   = 10
WALL_HEIGHT_BRICKS = 5

EVEN_ROW_BRICKS = WALL_WIDTH_STUDS // 2          # 5 × Brick1X2
ODD_ROW_BRICKS  = (WALL_WIDTH_STUDS - 2) // 2    # 4 × Brick1X2 + 2 × Brick1X1 fillers

scene = Scene()

# --- row 0 (even): place anchor at origin, then chain right ---
row0_anchor = Piece(part=Brick1X2, colour=Red)
scene.place_at(piece=row0_anchor, studs_x=0, plates_y=0, studs_z=0)

prev = row0_anchor
for _ in range(EVEN_ROW_BRICKS - 1):
    brick = Piece(part=Brick1X2, colour=Red)
    prev = prev.attach(piece=brick, side="right")  # auto-registers to scene

prev_row_leftmost = row0_anchor

# --- rows 1 to WALL_HEIGHT_BRICKS-1 ---
for row in range(1, WALL_HEIGHT_BRICKS):
    if row % 2 == 1:
        # Odd row: Brick1X1 filler at stud 0, then 4×Brick1X2, then Brick1X1 filler at stud 9

        # left filler — directly above stud 0 of the row below
        left_filler = Piece(part=Brick1X1, colour=Red)
        scene.place_on_top_of(left_filler, prev_row_leftmost)

        # first Brick1X2 — shifted 1 stud right so joints don't align with the row below
        row_anchor = Piece(part=Brick1X2, colour=Red)
        scene.place_on_top_of(row_anchor, prev_row_leftmost, right_studs=1)

        prev = row_anchor
        for _ in range(ODD_ROW_BRICKS - 1):
            brick = Piece(part=Brick1X2, colour=Red)
            prev = prev.attach(piece=brick, side="right")  # auto-registers to scene

        # right filler — attached to the last Brick1X2 of this row
        right_filler = Piece(part=Brick1X1, colour=Red)
        prev.attach(piece=right_filler, side="right")  # auto-registers to scene

        prev_row_leftmost = left_filler

    else:
        # Even row: same layout as row 0, directly above the leftmost piece below
        row_anchor = Piece(part=Brick1X2, colour=Red)
        scene.place_on_top_of(row_anchor, prev_row_leftmost)

        prev = row_anchor
        for _ in range(EVEN_ROW_BRICKS - 1):
            brick = Piece(part=Brick1X2, colour=Red)
            prev = prev.attach(piece=brick, side="right")  # auto-registers to scene

        prev_row_leftmost = row_anchor

scene.render_file(Path(__file__).parent / "generated_wall_bond_example.mpd")
print("Bond wall rendered to generated_wall_bond_example.mpd")
