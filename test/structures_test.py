"""Structures test for different structural elements like e.g. columns, etc.

"""

from pathlib import Path

from py4bricks.library.colours import Blue, Red, Green, Yellow
from py4bricks.library.parts.bricks import Brick2X2, Brick2X10, Brick2X2RoundWithoutReinforcement
from py4bricks.llm import Scene, Column

scene = Scene("Small structures samples")

round_column = Column(height_bricks=10, colour=Green, facing="east", shape="circular")
scene.place_at(round_column, studs_x=0, plates_y=0, studs_z=0, facing="east")

thick_round_column = Column(height_bricks=10, colour=Green, facing="east", 
                            shape="circular", circular_part=Brick2X2RoundWithoutReinforcement)
scene.place_at(thick_round_column, studs_x=20, plates_y=0, studs_z=0, facing="east")

square_column = Column(height_bricks=10, colour=Red, facing="east", shape="square")
scene.place_at(square_column, studs_x=0, plates_y=0, studs_z=20, facing="west")

pillar = Column(height_bricks=10, colour=Red, facing="east", shape="square", square_part=Brick2X10)
scene.place_at(pillar, studs_x=0, plates_y=0, studs_z=40, facing="west")

colum_row_item = Column(height_bricks=10, colour=Blue, facing="east", shape="square")
column_row = Column.column_row(prototype=colum_row_item, count=5, spacing_studs=4)
scene.place_at(column_row, studs_x=20, plates_y=0, studs_z=20, facing="east")

file_path = Path(__file__).with_suffix(".mpd")
scene.render_file(file_path)
print(f"Structures test rendered to {file_path.name}")
