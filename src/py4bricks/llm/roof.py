from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from py4bricks.colour import Colour
from py4bricks.debug import debug_add_origin_marker, debug_colour_by_orientation
from py4bricks.geometry import (
    LDU_PER_STUD,
    PLATES_PER_BRICK_HEIGHT,
    Identity,
    YAxis,
    plates_to_ldu,
    studs_to_ldu,
)
from py4bricks.library.colours import Red
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.library.parts.slopes import (
    SlopeBrick452X1,
    SlopeBrick452X1Double,
    SlopeBrick452X2,
    SlopeBrick452X2Double,
    SlopeBrick452X3,
    SlopeBrick452X3Double,
)
from py4bricks.library.parts.tiles import Tile1X3, Tile2X3
from py4bricks.llm.group import Group
from py4bricks.llm.primitives import BricksRow
from py4bricks.llm.types import Facing, Orientation
from py4bricks.pieces import CustomPiece, Piece

debug = True

@dataclass(frozen=True)
class _RoofGeometry:
    """Derived roof dimensions, computed once from width/length/ridge_running."""

    ridge_ldu: float  # length of the ridge in LDU
    ridge_studs: int  # ridge length in studs (drives tiling)
    perp_ldu: float  # perpendicular span (wall to wall) in LDU
    slope_depth_ldu: float  # half of perp_ldu — each slope covers this
    num_rows: int  # slope rows, also gable height in rows
    gable_base_studs: int  # total gable base width in studs
    even_slope_depth: bool  # True → double-slope cap; False → tile cap


def _compute_geometry(
    width_studs: int,
    length_studs: int,
    ridge_running: Orientation,
) -> _RoofGeometry:
    ridge_studs = width_studs if ridge_running == "east-west" else length_studs
    perp_studs = length_studs if ridge_running == "east-west" else width_studs

    ridge_ldu = studs_to_ldu(ridge_studs)
    perp_ldu = studs_to_ldu(perp_studs)
    slope_depth_ldu = perp_ldu / 2

    return _RoofGeometry(
        ridge_ldu=ridge_ldu,
        ridge_studs=ridge_studs,
        perp_ldu=perp_ldu,
        slope_depth_ldu=slope_depth_ldu,
        num_rows=int(slope_depth_ldu / LDU_PER_STUD),
        gable_base_studs=int(perp_ldu / LDU_PER_STUD) + 1,
        even_slope_depth=perp_studs % 2 == 0,
    )


def _slope_facings(ridge_running: Orientation) -> tuple[Facing, Facing]:
    """Return (left_facing, right_facing) for the two roof slopes."""
    return ("east", "west") if ridge_running == "north-south" else ("north", "south")


# Per-row offset toward the peak, keyed by slope facing.
# (right_studs, back_studs) — exactly one axis is non-zero.
_PEAK_OFFSET: dict[Facing, tuple[int, int]] = {
    "north": (0, +1),
    "south": (0, -1),
    "east": (+1, 0),
    "west": (-1, 0),
}


class Roof(Group):
    """A gabled roof assembled from slope bricks and triangular gable walls."""

    def __init__(
        self,
        name: str,
        width_studs: int,  # east-west dimension (X), same convention as Box
        length_studs: int,  # north-south dimension (Z), same convention as Box
        ridge_running: Orientation,
        colour: Colour = Red,
    ) -> None:
        super().__init__(name=name)
        self._init_pieces(colour)
        geo = _compute_geometry(width_studs, length_studs, ridge_running)
        left_facing, right_facing = _slope_facings(ridge_running)
        left_slope = self._build_slope(geo, left_facing)
        right_slope = self._build_slope(geo, right_facing)
        top_row = self._build_top_row(geo)  # ridge finisher

        self._place_slopes(
            left_slope,
            right_slope,
            top_row,
            ridge_running,
            width_studs,
            length_studs,
        )
        self._place_gables(geo, ridge_running, width_studs, length_studs)

    def _init_pieces(self, colour: Colour) -> None:
        self.slope_piece_small = CustomPiece(
            part=SlopeBrick452X1,
            colour=colour,
            override_render_pos_offset=lambda p: {"z": p.ldu_z / 2},
        )

        self.slope_piece_medium = CustomPiece(
            part=SlopeBrick452X2,
            colour=colour,
            override_render_pos_offset=lambda p: {"z": p.ldu_z / 2},
        )

        self.slope_piece_large = CustomPiece(
            part=SlopeBrick452X3,
            colour=colour,
            override_render_pos_offset=lambda p: {"z": p.ldu_z / 2},
        )

        self.top_double_slope_small = CustomPiece(
            part=SlopeBrick452X1Double,
            colour=colour,
            override_render_pos_offset=lambda p: {"y": p.ldu_y},
        )

        self.top_double_slope_medium = CustomPiece(
            part=SlopeBrick452X2Double,
            colour=colour,
            override_render_pos_offset=lambda p: {"y": p.ldu_y - plates_to_ldu(2)},
        )

        self.top_double_slope_large = CustomPiece(
            part=SlopeBrick452X3Double,
            colour=colour,
            override_render_pos_offset=lambda p: {"y": p.ldu_y - plates_to_ldu(2)},
        )

        self.top_tile_small = CustomPiece(
            part=Tile1X3,
            colour=colour,
            transform_by_rotating=Identity().rotate(-90, YAxis),
            override_render_pos_offset=lambda p: {"y": p.ldu_y},
        )

        self.top_tile_medium = CustomPiece(
            part=Tile2X3,
            colour=colour,
            transform_by_rotating=Identity().rotate(-90, YAxis),
            override_render_pos_offset=lambda p: {"y": p.ldu_y},
        )

        # composite top piece, emulating a non-existing Tile3X3
        self.top_tile_large = Group()

        top_tile_large_1st_segment = self.top_tile_medium.copy()

        self.top_tile_large.place_at(
            top_tile_large_1st_segment,
            studs_x=0,
            plates_y=0,
            studs_z=0,
        )

        self.top_tile_large.place_at(
            self.top_tile_small.copy(),
            studs_x=-self.top_double_slope_medium.studs_x,
            plates_y=0,
            studs_z=0,
        )

        self.gable_piece = Piece(part=Brick1X1, colour=colour)

    def _place_slopes(
        self,
        left_slope: Group,
        right_slope: Group,
        top_row: Group,
        ridge_running: Orientation,
        width_studs: int,
        length_studs: int,
    ) -> None:
        # TODO fix top placement, depending on if it is a double slope or a tile one, 
        # the whole top row shifts to one side and front/back, just by a few studs.
        # When adjusting for double slope (ok) it becomes off-center for tiles, and vice versa
        if ridge_running == "east-west":
            self.place_at(left_slope, studs_x=0, plates_y=0, studs_z=-1)
            self.place_on_top_of(
                top_row, left_slope, right_studs=0, back_studs=(left_slope.studs_z - 1)
            )
            self.place_at(
                right_slope, studs_x=(width_studs - 1), plates_y=0, studs_z=length_studs
            )
        else:
            self.place_at(
                left_slope, studs_x=-1, plates_y=0, studs_z=(length_studs - 1)
            )
            self.place_on_top_of(
                top_row,
                left_slope,
                right_studs=(left_slope.studs_x - top_row.studs_z),
                back_studs=0,
                facing="east",
            )
            self.place_at(right_slope, studs_x=width_studs, plates_y=0, studs_z=0)

    def _place_gables(
        self,
        geo: _RoofGeometry,
        ridge_running: Orientation,
        width_studs: int,
        length_studs: int,
    ) -> None:
        if ridge_running == "east-west":
            # Gables at west/east ends; rotate so the locally-X base extends along Z.
            self.place_at(
                self._build_gable(geo),
                studs_x=0,
                plates_y=0,
                studs_z=0,
                facing="west",
            )
            self.place_at(
                self._build_gable(geo),
                studs_x=width_studs - 1,
                plates_y=0,
                studs_z=0,
                facing="west",
            )
        else:
            # Gables at south/north ends; base already along X, no rotation needed.
            self.place_at(self._build_gable(geo), studs_x=0, plates_y=0, studs_z=0)
            self.place_at(
                self._build_gable(geo),
                studs_x=0,
                plates_y=0,
                studs_z=length_studs - 1,
            )

    def _build_gable(self, geo: _RoofGeometry) -> Group:
        """Staircase triangle of 1x1 bricks; base along local +X, growing upward.

        Row i: (gable_base_studs - 2*i) bricks, inset by i studs on each side,
        stacked 3 plates (= 1 brick body) above the row below.
        """
        group = Group()
        for row in range(geo.num_rows):
            row_width = (geo.gable_base_studs - 2 * row) - 2
            if row_width <= 0:
                break
            for col in range(1, row_width):
                group.place_at(
                    self.gable_piece.copy(),
                    studs_x=row + col,
                    plates_y=row * PLATES_PER_BRICK_HEIGHT,
                    studs_z=0,
                )
        return group

    def _build_slope(self, geo: _RoofGeometry, facing: Facing) -> Group:
        """Stack of rows along the ridge; each row above offset one stud toward the peak."""
        right_studs, back_studs = _PEAK_OFFSET[facing]

        slope = Group()

        bottom = BricksRow(
            brick_piece=self.slope_piece_large,
            width_studs=geo.ridge_studs,
            colour=self.slope_piece_large.colour,
            filler_brick_pieces=[self.slope_piece_medium, self.slope_piece_small],
        )

        # rotate entire row to match the slope facing
        slope.place_at(bottom, facing=facing)

        prev = bottom
        for _ in range(1, geo.num_rows):
            row = prev.copy()
            slope.place_on_top_of(
                row, prev, right_studs=right_studs, back_studs=back_studs, facing=facing
            )
            prev = row

        if debug:
            debug_add_origin_marker(
                slope, bottom, colour=debug_colour_by_orientation(facing)
            )

        return slope

    def _build_top_row(self, geo: _RoofGeometry) -> Group:
        """The top row, which may have a different piece if the slope depth is even."""
        top_large = (
            self.top_double_slope_large
            if geo.even_slope_depth
            else self.top_tile_medium
        )
        fillers = (
            [self.top_double_slope_medium, self.top_double_slope_small]
            if geo.even_slope_depth
            else [self.top_tile_small]
        )

        top_row = BricksRow(
            brick_piece=top_large,
            width_studs=geo.ridge_studs,
            colour=top_large.colour,
            filler_brick_pieces=fillers,
        )

        return top_row
