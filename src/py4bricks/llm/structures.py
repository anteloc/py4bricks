from __future__ import annotations
from py4bricks.library.colours import White
from pygments.token import Literal
from os import name
from turtle import distance, position

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.types import Facing

from py4bricks.geometry import (
    LDU_PER_BRICK_HEIGHT,
    LDU_PER_STUD_HEIGHT,
    PLATES_PER_BRICK_HEIGHT,
    Vector,
    orientation_to_rotation,
    plates_to_ldu,
    studs_to_ldu, ldu_to_studs,
)
from py4bricks.library.parts.bricks import Brick1X1, Brick1X2, Brick1X1RoundWithoutGroove
from py4bricks.llm.group import Group
from py4bricks.llm.slab import Slab

from py4bricks.pieces import Piece


class Column(Group):

    @classmethod
    def column_row(cls, 
                    prototype: Column, 
                    count: int, 
                    spacing_studs: int, 
                    with_slabs_colour: Colour | None = None
        ) -> Group:

        column_row = Group()

        columns = Group()

        for i in range(count):
            column = prototype.copy()
            columns.place_at(column, studs_x=i * spacing_studs, plates_y=0, studs_z=0)

        if with_slabs_colour is not None:
            slab_width = columns.studs_z if prototype.facing in ("east", "west") else columns.studs_x
            slab_length = columns.studs_x if prototype.facing in ("east", "west") else columns.studs_z
            slab = Slab(width_studs=slab_width, 
                        length_studs=slab_length, 
                        colour=with_slabs_colour)

            column_row.add(columns)
            column_row.place_on_top_of(slab, columns, facing=prototype.facing)
        else:
            column_row.add(columns)
            
        return column_row

    def __init__(
        self,
        height_bricks: int,
        colour: Colour = White,
        facing: Facing = "north",
        shape: Literal["circular", "square"] = "square",
        circular_part: str = Brick1X1RoundWithoutGroove,
        square_part: str = Brick1X1,
    ) -> None:
        super().__init__()

        self.height_bricks = height_bricks
        self.colour = colour
        self.facing = facing
        self.shape = shape
        self.circular_part = circular_part
        self.square_part = square_part

        part = square_part if shape == "square" else circular_part

        first_piece = Piece(
            part=part,
            colour=colour,
            rotation=orientation_to_rotation(facing),
        )


        self.add(first_piece)

        prev_piece = first_piece

        for _ in range(1, height_bricks):
            p = prev_piece.copy()
            self.place_on_top_of(p, prev_piece, facing=self.facing)
            prev_piece = p
    
    def copy(self) -> Column:
        return Column(
            height_bricks=self.height_bricks,
            colour=self.colour,
            facing=self.facing,
            shape=self.shape,
            circular_part=self.circular_part,
            square_part=self.square_part,
        )
