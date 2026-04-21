"""
Sloped bricks stacked like gables on a roof would do, ridge built by a double sided slope brick.
Base for both sides of the roof are 2 × Brick1X2, then 2 × SlopeBrick452X1, then the SlopeBrick451X1Double as the ridge.

Sloped bricks have two anti-studs at the bottom, and one stud on top, being the other supressed and replaced by the slope.
To correctly stack them as if it were gables on a roof, the slopes must be displaced by 1 stud relative to the support bricks (for the 1st gable) 
and relative to the underlying slope (for the 2nd gable).

The current layout causes for both 2nd gables to meet at the top, and the double slope, placed on top of both, constitutes the ridge.
"""
from turtle import right

from pathlib import Path

from py4bricks.library.colours import Blue, Red
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2
from py4bricks.library.parts.slopes import SlopeBrick452X1, SlopeBrick451X1Double, SlopeBrick452X1Double

from py4bricks.llm import Scene
from py4bricks.pieces import Piece

scene = Scene("Gables made of sloped bricks test")

# even row: 2 × Brick1X2
left_support = Piece(part=Brick1X2, colour=Blue)
scene.place_at(left_support, studs_x=0, plates_y=0, studs_z=0, facing="east")

gable_1st_left = Piece(part=SlopeBrick452X1, colour=Red)
scene.place_on_top_of(gable_1st_left, left_support, right_studs=-0.5, facing="east")

gable_2nd_left = Piece(part=SlopeBrick452X1, colour=Red )
scene.place_on_top_of(gable_2nd_left, gable_1st_left, right_studs=1, facing="east")


right_support = Piece(part=Brick1X2, colour=Blue)
scene.place_at(right_support, studs_x=2*left_support.studs_x - 1, plates_y=0, studs_z=0, facing="east")

gable_1st_right = Piece(part=SlopeBrick452X1, colour=Red)
scene.place_on_top_of(gable_1st_right, right_support, right_studs=0.5, facing="west")

gable_2nd_right = Piece(part=SlopeBrick452X1, colour=Red)
scene.place_on_top_of(gable_2nd_right, gable_1st_right, right_studs=-1, facing="west")

top = Piece(part=SlopeBrick452X1Double, colour=Red)
scene.place_on_top_of(top, gable_2nd_left, right_studs=0.5, facing="east")


scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Gables made of sloped bricks test rendered to gables_test.mpd")
