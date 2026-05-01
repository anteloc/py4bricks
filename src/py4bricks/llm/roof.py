from dataclasses import dataclass

from py4bricks.colour import Colour
from py4bricks.geometry import (
    LDU_PER_STUD,
    PLATES_PER_BRICK_HEIGHT,
    Identity,
    YAxis,
    studs_to_ldu,
)
from py4bricks.library.colours import Red
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.library.parts.slopes import SlopeBrick452X1, SlopeBrick452X1Double
from py4bricks.library.parts.tiles import Tile1X3
from py4bricks.llm.group import Group
from py4bricks.llm.types import Facing, Orientation
from py4bricks.pieces import CustomPiece, Piece


@dataclass(frozen=True)
class _RoofGeometry:
    """Derived roof dimensions, computed once from width/length/ridge_running."""

    ridge_ldu:        float  # length of the ridge in LDU
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
        perp_ldu         = perp_ldu,
        slope_depth_ldu  = slope_depth_ldu,
        num_rows         = int(slope_depth_ldu / LDU_PER_STUD),
        gable_base_studs = int(perp_ldu / LDU_PER_STUD) + 1,
        even_slope_depth = perp_studs % 2 == 0,
    )


def _slope_facings(ridge_running: Orientation) -> tuple[Facing, Facing]:
    """Return (left_facing, right_facing) for the two roof slopes."""
    return ("east", "west") if ridge_running == "north-south" else ("north", "south")


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
        self.top_piece = (
            self.top_double_slope if geo.even_slope_depth else self.top_tile
        )
        left_facing, right_facing = _slope_facings(ridge_running)
        left_slope  = self._build_slope(geo, left_facing)
        right_slope = self._build_slope(geo, right_facing, with_top=True)
        self._place_slopes(
            left_slope, right_slope, ridge_running, width_studs, length_studs,
        )
        self._place_gables(geo, ridge_running, width_studs, length_studs)

    def _init_pieces(self, colour: Colour) -> None:
        self.slope_piece = CustomPiece(
            part=SlopeBrick452X1,
            colour=colour,
            override_render_pos_offset=lambda p: {"z": p.ldu_z / 2},
        )
        self.top_double_slope = CustomPiece(
            part=SlopeBrick452X1Double,
            colour=colour,
            override_render_pos_offset=lambda p: {"y": p.ldu_y},
        )
        self.top_tile = CustomPiece(
            part=Tile1X3,
            colour=colour,
            transform_by_rotating=Identity().rotate(-90, YAxis),
            override_render_pos_offset=lambda p: {"y": p.ldu_y},
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
        group = Group()

        slopes_per_row = int(geo.ridge_ldu / self.slope_piece.ldu_x)

        # Per-row step in the slope direction (away from the wall).
        sign        = 1 if facing in ("north", "east") else -1
        back_studs  = sign if facing in ("north", "south") else 0
        right_studs = sign if facing in ("east",  "west")  else 0

        # Per-column step along the ridge.
        col_right = 1 if facing in ("north", "south") else 0  # X for N/S slopes
        col_back  = 1 if facing in ("east",  "west")  else 0  # Z for E/W slopes

        for col in range(slopes_per_row):
            slope_1st = self.slope_piece.copy()
            group.place_at(
                slope_1st,
                studs_x=col * col_right,
                studs_z=col * col_back,
                facing=facing,
            )

            prev_slope = slope_1st
            for _ in range(1, geo.num_rows):
                slope = self.slope_piece.copy()
                group.place_on_top_of(
                    slope, prev_slope,
                    right_studs=right_studs,
                    back_studs=back_studs,
                    facing=facing,
                )
                prev_slope = slope

            if with_top:
                group.place_on_top_of(
                    self.top_piece.copy(), prev_slope,
                    right_studs=right_studs,
                    back_studs=back_studs,
                    facing=facing,
                )

        return group
