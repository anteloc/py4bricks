
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.types import Facing

from py4bricks.geometry import (
    orientation_to_rotation,
)
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.llm.group import Group
from py4bricks.pieces import Piece, CustomPiece


class BricksRow(Group):
    """A simple row of evenly spaced 1x1 bricks, useful for building walls and other structures."""

    def __init__(
        self,
        brick_piece: Piece | CustomPiece,
        width_studs: int,   # east-west dimension (X), same convention as Wall, Box, etc.
        colour: Colour,
        filler_brick_pieces: list[Piece | CustomPiece] = [], # extra fillers in addition to brick 1x1, must be studs_z = brick_piece's studs_z
        facing: Facing = "north", # bricks will be individually rotated to be facing this direction, not the whole row
    ) -> None:
        """Create a row of evenly spaced bricks with the given parameters."""
        super().__init__()

        self._brick_piece = brick_piece
        self.width_studs = width_studs
        self.colour = colour
        self._filler_brick_pieces = filler_brick_pieces
        self.facing = facing

        # prototype brick
        self.brick = brick_piece.copy()
        self.brick.colour = colour
        self.brick.rotation = orientation_to_rotation(facing)

        self.length_studs = self.brick.studs_z # length (thickness) of the row is determined by the brick's depth

        self._build_filler_bricks()
        self._build_fallback_filler()

        self._build_bricks_row()

    def _build_filler_bricks(self) -> None:
        self.filler_bricks = [
            piece.copy()
            for piece in self._filler_brick_pieces
        ]

        for brick in self.filler_bricks:
            brick.colour = self.colour
            brick.rotation = orientation_to_rotation(self.facing)

        # sort filler bricks by width in descending order to try larger pieces first when filling gaps
        self.filler_bricks.sort(key=lambda b: b.studs_x, reverse=True)

    def _build_fallback_filler(self) -> None:
        # fallback: if no other bricks will be provided to fill gaps, this "composite filler" will do
        self.fallback_filler = Group()

        fallback_unit = Piece(
            part=Brick1X1,
            colour=self.colour,
            rotation=orientation_to_rotation(self.facing),
        )

        for i in range(self.length_studs):
            self.fallback_filler.place_at(fallback_unit.copy(), studs_z=i)

    def _build_bricks_row(self) -> None:
        """Internal method to build the row of bricks, filling gaps as needed."""
        # Calculate how many whole bricks fit and the remaining gap
        whole_bricks_count = self.width_studs // self.brick.studs_x
        remaining_studs_count = self.width_studs % self.brick.studs_x

        bricks = []

        bricks_whole = [self.brick.copy() for _ in range(whole_bricks_count)]

        # select filler bricks to fill the remaining gap, trying larger fillers first and using the fallback if needed
        def max_filler(gap: int) -> Piece | None:
            """Return the largest filler brick that can fit in the given gap, or None if no filler can fit."""
            for filler in self.filler_bricks:
                if filler.studs_x <= gap:
                    return filler.copy()
            return None

        bricks_filler = []

        while remaining_studs_count > 0:
            filler = max_filler(remaining_studs_count)
            if filler is not None:
                bricks_filler.append(filler)
                remaining_studs_count -= filler.studs_x
            else:
                bricks_filler.append(self.fallback_filler.copy())
                remaining_studs_count -= self.fallback_filler.studs_x

        # TODO in order to avoid all fillers being placed at the end of the row,
        # implement a smarter distribution of fillers to make the row look more uniform
        bricks.extend(bricks_whole)
        bricks.extend(bricks_filler)

        acc_studs_x = 0
        for brick in bricks:
            self.place_at(brick, studs_x=acc_studs_x)
            acc_studs_x += brick.studs_x

    def copy(self) -> BricksRow:
        """Return a new independent BricksRow with the same parameters and fresh pieces."""
        return BricksRow(
            brick_piece=self._brick_piece,
            width_studs=self.width_studs,
            colour=self.colour,
            filler_brick_pieces=self._filler_brick_pieces,
            facing=self.facing,
        )
