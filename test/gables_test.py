"""
Sloped bricks stacked like gables on a roof would do, ridge built by a double sided slope brick.
Base for both sides of the roof are 2 × Brick1X2, then 2 × SlopeBrick452X1, then the SlopeBrick451X1Double as the ridge.

Sloped bricks have two anti-studs at the bottom, and one stud on top, being the other supressed and replaced by the slope.
To correctly stack them as if it were gables on a roof, the slopes must be displaced by 1 stud relative to the support bricks (for the 1st gable) 
and relative to the underlying slope (for the 2nd gable).

The current layout causes for both 2nd gables to meet at the top, and the double slope, placed on top of both, constitutes the ridge.
"""
from py4bricks.colour import Colour
from turtle import right

from pathlib import Path

from py4bricks.library.colours import Blue, Red, Medium_Azure
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2, Brick10X10, Brick2X1WithPositioningRockets
from py4bricks.library.parts.slopes import SlopeBrick452X1, SlopeBrick451X1Double, SlopeBrick452X1Double

from py4bricks.llm import Scene
from py4bricks.pieces import Piece

def add_origin_marker(scene: Scene, piece: Piece, colour: Colour) -> None:
    origin_marker = Piece(part=Brick1X1, colour=colour)
    origin_marker.position = piece.position
    scene.add(origin_marker)

# SlopeBrick452X1
# "3040b": { "ldu_x": 20.0, "ldu_y": 28.0, "ldu_z": 40.0, "studs_x": 1, "studs_y": 2, "plates_y": 4, "studs_z": 2, },
# Brick1X2
# "3004": { "ldu_x": 40.0, "ldu_y": 28.0, "ldu_z": 20.0, "studs_x": 2, "studs_y": 2, "plates_y": 4, "studs_z": 1, },

scene = Scene("Gables made of sloped bricks test")

# even row: 2 × Brick1X2
# left_support = Piece(part=Brick1X1, colour=Blue)
# left_support = Piece(part=Brick1X2, colour=Blue)
# left_support = Piece(part=Brick10X10, colour=Blue)
# scene.place_at(left_support, studs_x=0, plates_y=0, studs_z=0, facing="east")

# add_origin_marker(scene, left_support, Medium_Azure)

# gable_1st_left = Piece(part=Brick1X2, colour=Red)
gable_1st_left = Piece(part=SlopeBrick452X1, colour=Red)
# gable_1st_left = Piece(part=Brick2X1WithPositioningRockets, colour=Red)
scene.place_at(gable_1st_left, studs_x=0, plates_y=0, studs_z=0, facing="north")
# scene.place_on_top_of(gable_1st_left, left_support, facing="north")

add_origin_marker(scene, gable_1st_left, Medium_Azure)

gable_2nd_left = Piece(part=SlopeBrick452X1, colour=Red )
scene.place_on_top_of(gable_2nd_left, gable_1st_left, back_studs=1, facing="north")


# right_support = Piece(part=Brick1X2, colour=Blue)
# scene.place_at(right_support, studs_x=2*left_support.studs_x - 1, plates_y=0, studs_z=0, facing="east")

# gable_1st_right = Piece(part=SlopeBrick452X1, colour=Red)
# scene.place_on_top_of(gable_1st_right, right_support, right_studs=1, facing="west")

# gable_2nd_right = Piece(part=SlopeBrick452X1, colour=Red)
# scene.place_on_top_of(gable_2nd_right, gable_1st_right, right_studs=-1, facing="west")

# top = Piece(part=Brick1X1, colour=Red)
top = Piece(part=SlopeBrick452X1Double, colour=Red)
scene.place_on_top_of(top, gable_2nd_left, back_studs=1, facing="north")


scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Gables made of sloped bricks test rendered to gables_test.mpd")
