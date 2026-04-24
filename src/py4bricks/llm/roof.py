from typing import Literal

from py4bricks.colour import Colour
from py4bricks.geometry import LDU_PER_STUD, PLATES_PER_BRICK_HEIGHT, studs_to_ldu
from py4bricks.library.colours import Red
from py4bricks.library.parts.bricks import Brick1X1
from py4bricks.library.parts.slopes import SlopeBrick452X1, SlopeBrick452X1Double
from py4bricks.llm.group import Group
from py4bricks.llm.types import Facing, Orientation
from py4bricks.pieces import Piece


class Roof(Group):
    def __init__(
        self,
        name: str,
        width_studs: int,   # east-west dimension (X), same convention as Box
        length_studs: int,  # north-south dimension (Z), same convention as Box
        ridge_running: Orientation,
        colour: Colour = Red,
    ) -> None:
        super().__init__(name=name)

        # Bug 1 fix: correct facing directions for each ridge orientation.
        # "east-west" ridge → slopes rise from south wall (north-facing) and
        # north wall (south-facing).
        # "north-south" ridge → slopes rise from west wall (east-facing) and
        # east wall (west-facing).
        left_slope_facing, right_slope_facing = (
            ("east", "west")
            if ridge_running == "north-south"
            else ("north", "south")
        )

        width_ldu  = studs_to_ldu(width_studs)
        length_ldu = studs_to_ldu(length_studs)

        # The ridge runs along one axis; slopes span the perpendicular axis.
        # Each slope covers half that perpendicular span.
        ridge_ldu       = width_ldu if ridge_running == "east-west" else length_ldu
        perp_ldu        = length_ldu if ridge_running == "east-west" else width_ldu
        slope_depth_ldu = perp_ldu / 2
        # Row count shared by slopes and gables: both rise the same number of rows.
        num_rows        = int(slope_depth_ldu / LDU_PER_STUD)

        left_slope = self._build_slope(
            slope_depth_ldu=slope_depth_ldu,
            ridge_ldu=ridge_ldu,
            facing=left_slope_facing,
            colour=colour,
        )
        right_slope = self._build_slope(
            slope_depth_ldu=slope_depth_ldu,
            ridge_ldu=ridge_ldu,
            facing=right_slope_facing,
            colour=colour,
            with_top=True,
        )

        # Slope groups are not rotated at placement time — the bricks inside
        # already carry the correct orientation.  Rotating the group too would
        # compose rotations and flip the bricks.
        # Each slope sits 1 stud outside the box on its own exterior side, so
        # the left/right placements are symmetric about the ridge.
        if ridge_running == "east-west":
            self.place_at(left_slope,  studs_x=0, plates_y=0, studs_z=-1)
            self.place_at(right_slope, studs_x=0, plates_y=0, studs_z=length_studs)
        else:
            self.place_at(left_slope,  studs_x=-1,          plates_y=0, studs_z=0)
            self.place_at(right_slope, studs_x=width_studs, plates_y=0, studs_z=0)

        # Triangular gable walls close off the two open ends of the ridge.
        # Base width = perp span + 1: slopes span from -1 to perp_studs on their
        # respective overhangs, i.e. (perp_studs + 1) studs total.
        # Height = num_rows, so the gable rises to the same level as the slopes.
        gable_base_studs = int(perp_ldu / LDU_PER_STUD) + 1

        if ridge_running == "east-west":
            # Gables at west/east ends; rotate so the locally-X base extends along Z.
            self.place_at(
                self._build_gable(gable_base_studs, num_rows, colour),
                studs_x=0, plates_y=0, studs_z=0, facing="west",
            )
            self.place_at(
                self._build_gable(gable_base_studs, num_rows, colour),
                studs_x=width_studs - 1, plates_y=0, studs_z=0, facing="west",
            )
        else:
            # Gables at south/north ends; base already along X, no rotation needed.
            self.place_at(
                self._build_gable(gable_base_studs, num_rows, colour),
                studs_x=0, plates_y=0, studs_z=0,
            )
            self.place_at(
                self._build_gable(gable_base_studs, num_rows, colour),
                studs_x=0, plates_y=0, studs_z=length_studs - 1,
            )

    def _build_gable(self, base_studs: int, num_rows: int, colour: Colour) -> Group:
        """Staircase triangle of 1x1 bricks; base along local +X, growing upward.

        Row i: (base_studs - 2*i) bricks, inset by i studs on each side,
        stacked 3 plates (= 1 brick body) above the row below.
        """
        group = Group()
        for row in range(num_rows):
            row_width = (base_studs - 2 * row) - 2
            if row_width <= 0:
                break
            for col in range(1, row_width):
                group.place_at(
                    Piece(part=Brick1X1, colour=colour),
                    studs_x=row + col,
                    plates_y=row * PLATES_PER_BRICK_HEIGHT,
                    studs_z=0,
                )
        return group

    def _build_slope(
        self,
        slope_depth_ldu: float,  # horizontal span from wall to ridge
        ridge_ldu: float,        # length of the ridge (bricks tile along this axis)
        facing: Facing,
        colour: Colour,
        with_top: bool = False,
    ) -> Group:

        group = Group()
        gable = Piece(part=SlopeBrick452X1, colour=colour)

        # Each row advances 1 stud horizontally; first brick contributes 2 studs
        num_rows = int(slope_depth_ldu / LDU_PER_STUD)
        # iterate columns to cover the full ridge length.
        slopes_per_row = int(ridge_ldu / gable.ldu_x)

        # per-row offset in the slope direction (into the slope, away from the wall)
        sign       = 1 if facing in ("north", "east") else -1
        back_studs = sign * 1 if facing in ("north", "south") else 0
        right_studs = sign * 1 if facing in ("east", "west") else 0

        # per-column offset along the ridge
        col_right = 1 if facing in ("north", "south") else 0  # X for N/S slopes
        col_back  = 1 if facing in ("east",  "west")  else 0  # Z for E/W slopes

        for col in range(slopes_per_row):
            slope_1st = gable.copy()
            group.place_at(
                slope_1st,
                studs_x=col * col_right,
                studs_z=col * col_back,
                facing=facing,
            )

            prev_slope = slope_1st
            for _ in range(1, num_rows):
                slope = gable.copy()
                group.place_on_top_of(
                    slope,
                    prev_slope,
                    right_studs=right_studs,
                    back_studs=back_studs,
                    facing=facing,
                )
                prev_slope = slope

            if with_top:
                top = Piece(part=SlopeBrick452X1Double, colour=colour)
                group.place_on_top_of(
                    top,
                    prev_slope,
                    right_studs=right_studs,
                    back_studs=back_studs,
                    facing=facing,
                )

        return group
