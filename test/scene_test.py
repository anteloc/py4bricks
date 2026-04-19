"""
Scene test — a 3-brick tower with a 2-brick cap and a side extension.

Exercises every Scene placement method:
    place_at        — ground floor brick at the origin
    place_on_top_of — second and third floor bricks stacked on each other
    place_adjacent_to — side extension flush to the east of the ground floor
    place           — a pre-positioned Group spanning the top of the tower
    piece_at        — verify the ground floor brick is at the expected position
    render_file     — write the LDraw file

Visual layout (facing north, viewed from the side):

    [cap-L][cap-R]   ← white group, pre-positioned at plates_y=9
       [top]         ← blue,   3rd floor
      [middle]       ← yellow, 2nd floor
    [ground][side]   ← red + green, ground floor
"""

from pathlib import Path

from py4bricks.library.colours import Blue, Green, Red, White, Yellow
from py4bricks.library.parts.bricks import Brick1X2
from py4bricks.llm import Group, Scene
from py4bricks.pieces import Piece

scene = Scene()

# ground floor — absolute position at the origin
ground = Piece(part=Brick1X2, colour=Red)
scene.place_at(piece=ground, studs_x=0, plates_y=0, studs_z=0)

# second and third floor — stacked directly on top of each other
middle = Piece(part=Brick1X2, colour=Yellow)
scene.place_on_top_of(middle, ground)

top = Piece(part=Brick1X2, colour=Blue)
scene.place_on_top_of(top, middle)

# side extension — flush to the east of the ground floor brick
side = Piece(part=Brick1X2, colour=Green)
scene.place_adjacent_to(side, ground, side="east")

# cap — a Group of 2 bricks pre-positioned at the top of the 3-brick tower
# 3 bricks × 3 plates each = 9 plates; the Group sets its own Y at construction
cap = Group(studs_x=0, plates_y=9)
cap_left  = Piece(part=Brick1X2, colour=White)
cap_right = Piece(part=Brick1X2, colour=White)
cap.add(cap_left)
cap_left.attach(piece=cap_right, side="right")
scene.place(cap, facing="north")

# verify the ground floor brick sits at the expected position
assert scene.piece_at(studs_x=0, plates_y=0, studs_z=0) is not None, \
    "ground floor brick not found at origin"

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Scene test rendered to scene_test.mpd")
