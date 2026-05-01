from __future__ import annotations

from typing import cast
from dataclasses import dataclass

from py4bricks.colour import Colour
from py4bricks.geometry import (
    LDU_PER_STUD,
    PLATES_PER_BRICK_HEIGHT,
    Identity,
    YAxis,
    studs_to_ldu, plates_to_ldu,
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
from py4bricks.llm.types import Facing, Orientation
from py4bricks.pieces import CustomPiece, Piece
from py4bricks.debug import debug_colour_by_orientation, debug_add_origin_marker

debug = True

def slope_colour(requested_colour: Colour, orientation: Orientation) -> Colour:
    if debug:
        return debug_colour_by_orientation(cast(str, orientation))
    return requested_colour


@dataclass(frozen=True)
class _RoofGeometry:
    """Derived roof dimensions, computed once from width/length/ridge_running."""

    ridge_ldu:        float  # length of the ridge in LDU
    ridge_studs:      int    # ridge length in studs (drives tiling)
    perp_ldu:         float  # perpendicular span (wall to wall) in LDU
    slope_depth_ldu:  float  # half of perp_ldu — each slope covers this
    num_rows:         int    # slope rows, also gable height in rows
    gable_base_studs: int    # total gable base width in studs
    even_slope_depth: bool   # True → double-slope cap; False → tile cap


def _compute_geometry(
    width_studs: int, length_studs: int, ridge_running: Orientation,
) -> _RoofGeometry:
    ridge_studs = width_studs if ridge_running == "east-west" else length_studs
    perp_studs  = length_studs if ridge_running == "east-west" else width_studs

    ridge_ldu       = studs_to_ldu(ridge_studs)
    perp_ldu        = studs_to_ldu(perp_studs)
    slope_depth_ldu = perp_ldu / 2

    return _RoofGeometry(
        ridge_ldu        = ridge_ldu,
        ridge_studs      = ridge_studs,
        perp_ldu         = perp_ldu,
        slope_depth_ldu  = slope_depth_ldu,
        num_rows         = int(slope_depth_ldu / LDU_PER_STUD),
        gable_base_studs = int(perp_ldu / LDU_PER_STUD) + 1,
        even_slope_depth = perp_studs % 2 == 0,
    )


def _slope_facings(ridge_running: Orientation) -> tuple[Facing, Facing]:
    """Return (left_facing, right_facing) for the two roof slopes."""
    return ("east", "west") if ridge_running == "north-south" else ("north", "south")


# Per-row offset toward the peak, keyed by slope facing.
# (right_studs, back_studs) — exactly one axis is non-zero.
_PEAK_OFFSET: dict[Facing, tuple[int, int]] = {
    "north": ( 0, +1),
    "south": ( 0, -1),
    "east":  (+1,  0),
    "west":  (-1,  0),
}


def _row_along_ridge(
    # items: list[tuple[Piece | Group, int]], facing: Facing,
    roof: Roof, geo: _RoofGeometry, facing: Facing, top: bool = False,
) -> Group:
    """One gable row: pieces laid along the ridge axis.

    Ridge runs along +X for N/S slopes, along +Z for E/W slopes.
    Each piece is rotated to `facing`; the row Group itself stays unrotated,
    so when rows are stacked their rotations don't compound.
    """
    tiles = _tile_ridge(
            geo.ridge_studs,
            roof.slope_piece_large if not top else roof._top_for_slope[roof.slope_piece_large],
            roof.slope_piece_medium if not top else roof._top_for_slope[roof.slope_piece_medium],
            roof.slope_piece_small if not top else roof._top_for_slope[roof.slope_piece_small],
        )


    row = Group()
    first = tiles[0][0].copy()
    row.place_at(
        first,
        studs_x=0, plates_y=0, studs_z=0,
        facing=facing,
    )

    prev = first
    curr_z = first.studs_z

    for piece, _ in tiles[1:]:
        row.place_at(
            piece.copy(),
            studs_x=0,
            studs_z=curr_z,
            facing=facing,
        )

        prev = piece
        curr_z += piece.studs_z if facing in ("north", "south") else piece.studs_x

    return row


def _tile_ridge(
    ridge_studs: int,
    large: CustomPiece,   # 3 studs wide
    medium: CustomPiece,  # 2 studs wide
    small: CustomPiece,   # 1 stud wide
) -> list[tuple[CustomPiece, int]]:
    """Tile ridge_studs with the fewest pieces, largest first.

    Avoids 1-wide pieces when possible: when N % 3 == 1 and N >= 4,
    uses one fewer large and two medium instead of one small.

      N=4  →  medium + medium       (not large + small)
      N=7  →  large + medium + medium
      N=11 →  large + large + large + medium + medium
    """
    n3, r = divmod(ridge_studs, 3)

    if r == 1 and n3 > 0:
        widths = [3] * (n3 - 1) + [2, 2]
    elif r == 2:
        widths = [3] * n3 + [2]
    elif r == 0:
        widths = [3] * n3
    else:                           # ridge_studs == 1
        widths = [1]

    piece_for_width = {3: large, 2: medium, 1: small}
    tiles, pos = [], 0
    for w in widths:
        tiles.append((piece_for_width[w], pos))
        pos += w
    return tiles


class Roof(Group):
    """A gabled roof assembled from slope bricks and triangular gable walls."""

    def __init__(
        self,
        name: str,
        width_studs: int,   # east-west dimension (X), same convention as Box
        length_studs: int,  # north-south dimension (Z), same convention as Box
        ridge_running: Orientation,
        colour: Colour = Red,
    ) -> None:
        super().__init__(name=name)
        self._init_pieces(colour)
        geo = _compute_geometry(width_studs, length_studs, ridge_running)
        if geo.even_slope_depth:
            self._top_for_slope = {
                self.slope_piece_small:  self.top_double_slope_small,
                self.slope_piece_medium: self.top_double_slope_medium,
                self.slope_piece_large:  self.top_double_slope_large,
            }
        else:
            self._top_for_slope = {
                self.slope_piece_small:  self.top_tile_small,
                self.slope_piece_medium: self.top_tile_medium,
                self.slope_piece_large:  self.top_tile_large,
            }
        left_facing, right_facing = _slope_facings(ridge_running)
        left_slope  = self._build_slope(geo, left_facing)
        right_slope = self._build_slope(geo, right_facing, with_top=True)
        self._place_slopes(
            left_slope, right_slope, ridge_running, width_studs, length_studs,
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
            override_render_pos_offset=lambda p: {"y": p.ldu_y - plates_to_ldu(2)},
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
            studs_x=0, plates_y=0, studs_z=0,
        )

        self.top_tile_large.place_at(
            self.top_tile_small.copy(),
            studs_x=-self.top_double_slope_medium.studs_x, plates_y=0, studs_z=0,
        )

        self.gable_piece = Piece(part=Brick1X1, colour=colour)

    def _place_slopes(
        self,
        left_slope: Group,
        right_slope: Group,
        ridge_running: Orientation,
        width_studs: int,
        length_studs: int,
    ) -> None:
        # Slope groups are not rotated at placement time — the bricks inside
        # already carry the correct orientation.  Rotating the group too would
        # compose rotations and flip the bricks.
        # Each slope sits 1 stud outside the box on its own exterior side.
        if ridge_running == "east-west":
            self.place_at(left_slope,  studs_x=0, plates_y=0, studs_z=-1)
            self.place_at(right_slope, studs_x=0, plates_y=0, studs_z=length_studs)
        else:
            self.place_at(left_slope,  studs_x=-1,          plates_y=0, studs_z=0)
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
                studs_x=0, plates_y=0, studs_z=0, facing="west",
            )
            self.place_at(
                self._build_gable(geo),
                studs_x=width_studs - 1, plates_y=0, studs_z=0, facing="west",
            )
        else:
            # Gables at south/north ends; base already along X, no rotation needed.
            self.place_at(self._build_gable(geo), studs_x=0, plates_y=0, studs_z=0)
            self.place_at(
                self._build_gable(geo),
                studs_x=0, plates_y=0, studs_z=length_studs - 1,
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

    def _build_slope(
        self,
        geo: _RoofGeometry,
        facing: Facing,
        with_top: bool = False,
    ) -> Group:
        """Stack of gable rows: each row runs along the ridge; each row above
        is offset one stud toward the peak."""

        right_studs, back_studs = _PEAK_OFFSET[facing]

        slope = Group()

        # Bottom row sits at the slope's origin.
        bottom = _row_along_ridge(self, geo, facing)
        slope.place_at(bottom)

        # Each subsequent row sits on top of the previous, offset toward the peak.
        prev = bottom
        for _ in range(1, geo.num_rows):
            row = prev.copy()
            slope.place_on_top_of(
                row, prev, right_studs=right_studs, back_studs=back_studs,
            )
            prev = row

        # Cap the peak with a final row of top pieces.
        # if with_top:
        #     top = _row_along_ridge(
        #         roof=self, geo=geo, facing=facing, top=True,
        #     )
        #     slope.place_on_top_of(
        #         top, prev, right_studs=right_studs, back_studs=back_studs,
        #     )

        if debug:
            debug_add_origin_marker(slope, bottom)

        return slope
