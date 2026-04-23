from pympler.asizeof import leng
from turtle import left
from typing import Literal
from py4bricks.colour import Colour
from py4bricks.library.colours import Blue, Red
from py4bricks.library.parts.bricks import (
    Brick1X1,
    Brick1X2,
)
from py4bricks.library.parts.slopes import (
    SlopeBrick452X1,
    SlopeBrick452X1Double,
)
from py4bricks.llm import Group, Scene, Facing
from py4bricks.pieces import Piece
from py4bricks.geometry import studs_to_ldu, plates_to_ldu, ldu_to_brick_height

class Roof(Group):
    def __init__(
        self,
        name: str,
        width_studs: int,
        length_studs: int,
        ridge_running: Literal["north-south", "east-west"],
        colour: Colour,
    ) -> None:
        super().__init__(name=name)

        left_slope_facing, right_slope_facing = (
            (Facing.NORTH, Facing.EAST) 
            if ridge_running == "north-south"
            else (Facing.SOUTH, Facing.WEST)
        )

        # TODO calculate height: pythagorean theorem, width_studs / 2 is the base, 45 deg the angle
        width_ldu = studs_to_ldu(width_studs)
        length_ldu = studs_to_ldu(length_studs)

        slopes_height_ldu = width_ldu / 2
        
        left_slope = self._build_slope(height_ldu=slopes_height_ldu, 
                                            length_ldu=length_ldu,
                                            facing=left_slope_facing, 
                                            colour=colour)

        right_slope = self._build_slope(height_ldu=slopes_height_ldu, 
                                             length_ldu=length_ldu,
                                             facing=right_slope_facing, 
                                             colour=colour, with_top=True)

        supports_distance_studs = left_slope.studs_z + right_slope.studs_z + 1

        # both base bricks are parallel and facing the same way
        self.place_at(left_slope, 
                        studs_x=0, 
                        plates_y=0, 
                        studs_z=0, 
                        facing=left_slope_facing)
        self.place_at(right_slope, 
                        studs_x=0, 
                        plates_y=0, 
                        studs_z=supports_distance_studs, 
                        facing=left_slope_facing)

    def _build_slope(
        self,
        height_ldu: float,
        length_ldu: float,
        facing: Facing,
        colour: Colour,
        with_top: bool = False,
    ) -> Group:

        group = Group()
        slope_part = SlopeBrick452X1

        gable = Piece(part=slope_part, colour=colour)

        # number of rows running parallel to roof's ridge
        num_rows = height_ldu // gable.ldu_y
        slopes_per_row = length_ldu // gable.ldu_z


        sign = 1 if facing in (Facing.NORTH, Facing.EAST) else -1
        back_studs = sign * 1 if facing in (Facing.NORTH, Facing.SOUTH) else 0
        right_studs = sign * 1 if facing in (Facing.EAST, Facing.WEST) else 0

        slope_1st = gable.copy()
        group.place_at(slope_1st, facing=facing)

        prev_slope = slope_1st
        for _ in range(1, num_rows):
            slope = gable.copy()
            group.place_on_top_of(slope,
                                prev_slope,
                                right_studs=right_studs,
                                back_studs=back_studs,
                                facing=facing)
            prev_slope = slope

        if with_top:
            top = Piece(part=SlopeBrick452X1Double, colour=colour)
            group.place_on_top_of(top,
                                prev_slope,
                                right_studs=right_studs,
                                back_studs=back_studs,
                                facing=facing)

        return group