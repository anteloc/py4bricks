from typing import Literal

from py4bricks.colour import Colour
from py4bricks.geometry import studs_to_ldu
from py4bricks.library.colours import Red
from py4bricks.library.parts.slopes import SlopeBrick452X1, SlopeBrick452X1Double
from py4bricks.llm.group import Group
from py4bricks.llm.types import Facing
from py4bricks.pieces import Piece


class Roof(Group):
    def __init__(
        self,
        name: str,
        width_studs: int,   # east-west dimension (X), same convention as Box
        length_studs: int,  # north-south dimension (Z), same convention as Box
        ridge_running: Literal["north-south", "east-west"],
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

        left_slope = self._build_slope(
            height_ldu=slope_depth_ldu,
            ridge_ldu=ridge_ldu,
            facing=left_slope_facing,
            colour=colour,
        )
        right_slope = self._build_slope(
            height_ldu=slope_depth_ldu,
            ridge_ldu=ridge_ldu,
            facing=right_slope_facing,
            colour=colour,
            with_top=True,
        )

        # Bug 2 fix: the slope groups are not rotated at placement time —
        # the bricks inside already carry the correct orientation.  Rotating
        # the group too would compose rotations and flip the bricks.
        # The right slope starts at the far wall and grows inward.
        self.place_at(left_slope, studs_x=0, plates_y=0, studs_z=0)

        if ridge_running == "east-west":
            self.place_at(right_slope, studs_x=0, plates_y=0, studs_z=length_studs)
        else:
            self.place_at(right_slope, studs_x=width_studs, plates_y=0, studs_z=0)

    def _build_slope(
        self,
        height_ldu: float,
        ridge_ldu: float,   # length of the ridge (bricks tile along this axis)
        facing: Facing,
        colour: Colour,
        with_top: bool = False,
    ) -> Group:

        group = Group()
        gable = Piece(part=SlopeBrick452X1, colour=colour)

        # rows climbing up the slope face
        num_rows = int(height_ldu / gable.ldu_y)
        # Bug 3 fix: each brick is 1 stud wide along the ridge (ldu_x = 20);
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
