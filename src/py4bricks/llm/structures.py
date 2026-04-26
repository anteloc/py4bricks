"""structures.py — LLM-friendly composite structures built from Groups.

Each class here composes primitive pieces into a reusable architectural
element. Like Wall and Slab, every structure extends Group so the Scene
can place, stack, and query it with the same verbs:

    col = Column(height_bricks=8, colour=White, shape="circular")
    scene.place_at(col, studs_x=4, plates_y=0, studs_z=4)

    portico = Column.column_row(col, count=4, spacing_studs=5,
                                with_slabs_colour=Light_Grey)
    scene.place_on_top_of(portico, floor)
"""
from __future__ import annotations
from more_itertools import first
from py4bricks.llm import Roof

from typing import TYPE_CHECKING, Literal

from py4bricks.library.colours import White, Red

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.types import Facing

from py4bricks.geometry import (
    orientation_to_rotation,
)
from py4bricks.library.parts.bricks import Brick1X1, Brick1X1RoundWithoutGroove
from py4bricks.llm.group import Group
from py4bricks.llm.slab import Slab
from py4bricks.pieces import Piece


class Column(Group):
    """A vertical stack of 1x1 bricks, square or circular.

    Extends Group so it can be placed, stacked, and queried exactly like any
    other structure.  All bricks share the same colour and facing; the facing
    rotates each brick around its vertical axis (useful for round bricks that
    have a directional detail).

    Typical usage:

        col = Column(height_bricks=6, colour=Tan, shape="circular")
        scene.place_at(col, studs_x=2, plates_y=0, studs_z=2)

    To build a colonnade with a connecting slab on top:

        portico = Column.column_row(
            prototype=col, count=5, spacing_studs=4,
            with_slabs_colour=Light_Grey,
        )
        scene.place_on_top_of(portico, base_slab)
    """

    @classmethod
    def column_row(
        cls,
        column_prototype: Column,
        count: int,
        spacing_studs: int,
        with_slabs_colour: Colour | None = None,
    ) -> Group:
        """Build a linear row of evenly spaced copies of a prototype column.

        Columns are placed along the X axis, each `spacing_studs` apart.
        When `with_slabs_colour` is given, a Slab is placed on top of the
        entire row — its dimensions are derived from the columns' bounding
        box and automatically transposed when the prototype faces east/west,
        so the slab always spans the correct axes regardless of orientation.

        prototype       — Column instance used as the template; copied `count` times.
        count           — number of columns in the row.
        spacing_studs   — stud distance from the start of one column to the next.
        with_slabs_colour — if set, caps the row with a slab of this colour.

        Returns a Group containing the columns (and optional slab) ready for
        placement in a Scene or parent Group.
        """
        column_row = Group()
        columns = Group()

        for i in range(count):
            column = column_prototype.copy()
            columns.place_at(column, studs_x=i * spacing_studs, plates_y=0, studs_z=0)

        if with_slabs_colour is not None:
            # Swap width/length when columns face east/west so the slab always
            # spans their bounding box correctly irrespective of orientation.
            slab_width  = columns.studs_z if column_prototype.facing in ("east", "west") else columns.studs_x
            slab_length = columns.studs_x if column_prototype.facing in ("east", "west") else columns.studs_z
            slab = Slab(width_studs=slab_width,
                        length_studs=slab_length,
                        colour=with_slabs_colour)
            column_row.add(columns)
            column_row.place_on_top_of(slab, columns, facing=column_prototype.facing)
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
        """Create a column of stacked 1x1 bricks.

        height_bricks   — number of bricks tall.
        colour          — colour applied to every brick.
        facing          — rotates each brick around Y; matters for round bricks
                          with directional surface detail (default "north").
        shape           — "square" uses Brick1X1; "circular" uses
                          Brick1X1RoundWithoutGroove (or `circular_part`).
        circular_part   — override the round brick part identifier.
        square_part     — override the square brick part identifier.
        """
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
        """Return a new independent Column with the same parameters and fresh pieces."""
        return Column(
            height_bricks=self.height_bricks,
            colour=self.colour,
            facing=self.facing,
            shape=self.shape,
            circular_part=self.circular_part,
            square_part=self.square_part,
        )

class Porche(Group):
    """A simple covered porch structure with either a flat or sloped roof supported by columns.

    The porch is a Group composed of a row of columns (built with
    Column.column_row) and a flat slab on top. The columns can be customized
    with any parameters supported by Column, and the slab automatically fits
    the row's bounding box and rotates to match the columns' orientation.
    """
    def __init__(
        self,
        name: str,
        column_prototype: Column,
        width_studs: int,
        length_studs: int,
        roof_colour: Colour = Red,
        roof_type: Literal["flat", "sloped"] = "flat",
    ) -> None:
        """Create a porched structure with the given column parameters and slab colour."""
        super().__init__()

        self.roof_type = roof_type

        


        columns = Group()

        front_left_col = column_prototype.copy()
        front_right_col = column_prototype.copy()
        back_left_col = column_prototype.copy()
        back_right_col = column_prototype.copy()

        columns.place_at(back_left_col, studs_x=0, studs_z=0)
        columns.place_at(back_right_col, studs_x=width_studs, studs_z=0)
        columns.place_at(front_left_col, studs_x=0, studs_z=length_studs)
        columns.place_at(front_right_col, studs_x=width_studs, studs_z=length_studs)
        
        # roof_width  = columns.studs_x if column_prototype.facing in ("east", "west") else columns.studs_x
        # roof_length = columns.studs_x if column_prototype.facing in ("east", "west") else columns.studs_z
        
        roof_width, roof_length = ((columns.studs_z, columns.studs_x) 
                                                                if column_prototype.facing in ("east", "west") 
                                                                else (columns.studs_x, columns.studs_z))
        
        sloped_roof_ridge_running = "north-south" if column_prototype.facing in ("east", "west") else "east-west"


        roof = None
        if roof_type == "flat":
            roof = Slab(name=f"{name}_roof", 
                        width_studs=roof_width, 
                        length_studs=roof_length, 
                        colour=roof_colour)
        elif roof_type == "sloped":
            roof = Roof(name=f"{name}_roof", 
                width_studs=roof_width, 
                length_studs=roof_length, 
                colour=roof_colour,
                ridge_running=sloped_roof_ridge_running)
        

        self.add(columns)
        self.place_on_top_of(roof, columns, facing=column_prototype.facing)