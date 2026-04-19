"""
Bond wall test — minimal 4-stud-wide, 2-row bond wall.

    Even row:  [--brick--][--brick--]   studs 0-1, 2-3
    Odd row:   [b][--brick--][b]         stud 0, studs 1-2, stud 3

The defining property of a bond wall: odd-row bricks are shifted 1 stud right
so vertical joints never align between rows.

Assertions verify:
    - even row anchor sits at the origin
    - odd row is stacked exactly 1 brick (3 plates) above
    - odd row Brick1X2 is offset 1 stud right  ← the bond
"""

from pathlib import Path

from py4bricks.library.colours import Blue, Red
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2
from py4bricks.llm.scene import Scene
from py4bricks.pieces import Piece

scene = Scene()

# even row: 2 × Brick1X2
even_anchor = Piece(part=Brick1X2, colour=Red)
scene.place_at(piece=even_anchor, studs_x=0, plates_y=0, studs_z=0)
even_anchor.attach(piece=Piece(part=Brick1X2, colour=Red), side="right")

# odd row: Brick1X1 + Brick1X2 (offset 1 stud right) + Brick1X1
odd_filler_left = Piece(part=Brick1X1, colour=Blue)
scene.place_on_top_of(odd_filler_left, even_anchor)

odd_brick = Piece(part=Brick1X2, colour=Blue)
scene.place_on_top_of(odd_brick, even_anchor, right_studs=1)
odd_brick.attach(piece=Piece(part=Brick1X1, colour=Blue), side="right")

# even row anchor is at the origin
assert scene.piece_at(studs_x=0, plates_y=0, studs_z=0) is not None
# odd row is 1 brick (3 plates) above even row
assert scene.piece_at(studs_x=0, plates_y=3, studs_z=0) is not None
# odd row Brick1X2 is offset 1 stud right — the bond
assert scene.piece_at(studs_x=1, plates_y=3, studs_z=0) is not None

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Bond wall test rendered to wall_bond_test.mpd")
