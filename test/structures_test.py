"""Structures test for different structural elements like e.g. columns, etc."""

from pathlib import Path

from py4bricks.library.colours import (
    Blue,
    Green,
    Light_Orange,
    Red,
    Rubber_Dark_Azure,
    White,
    Yellow,
)
from py4bricks.library.parts.bricks import (
    Brick1X2,
    Brick2X2,
    Brick2X2RoundWithoutReinforcement,
    Brick2X10,
)
from py4bricks.llm import Balcony, BricksRow, Column, Porch, Scene

scene = Scene("Small structures samples")

# A round column, using the default circular part
round_column = Column(height_bricks=10, colour=Green, facing="east", shape="circular")
scene.place_at(round_column, studs_x=0, studs_z=0, facing="east")

# A thicker round column, using a 2x2 custom circular part
thick_round_column = Column(
    height_bricks=10,
    colour=Green,
    facing="east",
    shape="circular",
    circular_part=Brick2X2RoundWithoutReinforcement,
)
scene.place_at(thick_round_column, studs_x=20, studs_z=0, facing="east")

# A square column, using the default square part
square_column = Column(height_bricks=10, colour=Red, facing="east", shape="square")
scene.place_at(square_column, studs_x=0, studs_z=20, facing="west")

# A thicker square column, using a 2x10 custom square part
pillar = Column(
    height_bricks=10, colour=Red, facing="east", shape="square", square_part=Brick2X10,
)
scene.place_at(pillar, studs_x=0, studs_z=40, facing="west")

# A row of columns
col_row_item = Column(height_bricks=10, colour=Blue, facing="east", shape="square")
col_row = Column.column_row(column_prototype=col_row_item, count=5, spacing_studs=4)
scene.place_at(col_row, studs_x=20, studs_z=20, facing="east")

# A row of columns with slabs on top
col_row_slabs_item = Column(
    height_bricks=10,
    colour=Rubber_Dark_Azure,
    facing="north",
    shape="square",
    square_part=Brick1X2,
)
col_row_slabs = Column.column_row(
    column_prototype=col_row_slabs_item,
    count=7,
    spacing_studs=4,
    with_slabs_colour=Yellow,
)
scene.place_at(col_row_slabs, studs_x=40, studs_z=20, facing="west")

# A porche with a blue sloped roof
porche_col_prototype = Column(
    height_bricks=8, colour=Yellow, facing="north", shape="circular",
)
sloped_porche = Porch(
    name="Porche",
    column_prototype=porche_col_prototype,
    width_studs=16,
    length_studs=5,
    roof_type="sloped",
    roof_colour=Blue,
)
scene.place_at(sloped_porche, studs_x=75, studs_z=40, facing="east")

# A porche with a red flat roof
flat_porche = Porch(
    name="Porche",
    column_prototype=porche_col_prototype,
    width_studs=16,
    length_studs=6,
    roof_type="flat",
    roof_colour=Red,
)
scene.place_at(flat_porche, studs_x=40, studs_z=75, facing="north")

# A balcony
col_balcony_prototype = Column(
    height_bricks=4, colour=Yellow, facing="north", shape="square",
)

balcony = Balcony(
    name="Balcony",
    column_prototype=col_balcony_prototype,
    width_studs=16,
    length_studs=5,
    floor_colour=White,
    railing_colour=Blue,
)

scene.place_at(balcony, studs_x=75, studs_z=75, facing="south")

file_path = Path(__file__).with_suffix(".mpd")
scene.render_file(file_path)
print(f"Structures test rendered to {file_path.name}")
