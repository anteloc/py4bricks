from __future__ import annotations
import math
from typing import Literal

from py4bricks.colour import Colour
from py4bricks.library.colours import Red
from py4bricks.library.parts.slopes import SlopeBrick452X1
from py4bricks.llm.box import Box
from py4bricks.geometry import LDU_PER_STUD_HEIGHT, Identity, Vector, YAxis, brick_height_to_ldu, ldu_to_plates, studs_to_ldu, plates_to_ldu
from py4bricks.pieces import Group, Piece

# Roof types: https://blog.rooroofing.com.au/guide-pitched-roofs

class PitchedRoof(Group):
    """A pitched roof is a roof with two sloping sides that meet at a ridge. 
    
    The slope of the roof is 45 degrees, set by the slope bricks used to build it.
    
    """

    def __init__(self, 
                 box_to_cover: Box,
                 ridge_orientation: Literal["north-south", "east-west"] = "north-south",
                 # roof_type: Literal["gable", "hip", "mansard"] = "gable",
                 colour: Colour = Red,
    ) -> None:
        
        ref_wall = box_to_cover["north_wall"] if ridge_orientation == "north-south" else box_to_cover["west_wall"]

        # roof will be positioned just on top of the box, i.e. at the height of a wall
        roof_pos = ref_wall.position + Vector(0, brick_height_to_ldu(ref_wall.bricks_height), 0)

        super().__init__(position=roof_pos, rotation=ref_wall.rotation)


        self.box_to_cover = box_to_cover
        self.ridge_orientation = ridge_orientation
        self.colour = colour

        self.box_width_ldu = studs_to_ldu(box_to_cover.box_width_studs)
        self.box_depth_ldu = studs_to_ldu(box_to_cover.box_depth_studs)

        self._roof_calculations(slope_part=SlopeBrick452X1, slope_angle=45)

        self._build_side_slope("left")
        self._build_side_slope("right")

        # TODO fill in the gable triangles on the non-sloped walls

    def _roof_calculations(self, slope_part: str, slope_angle: float) -> None:
        """Calculate the number of slope pieces needed to cover the roof, and the position of each piece on top of the box."""
        piece = Piece(part=slope_part, colour=self.colour)
        self.piece_height_ldu = piece.ldu_y - LDU_PER_STUD_HEIGHT # studs are connection points, they don't contribute to the height
        # After rotation, piece.ldu_x (1 stud) aligns along the ridge
        self.piece_step_along_ridge = piece.ldu_x
        # Horizontal run per row going up the slope (1 stud for a 45° slope brick)
        self.piece_step_across_ridge = piece.ldu_x

        match self.ridge_orientation:
            case "north-south":
                # Ridge along Z; slopes face east/west (X axis)
                self.roof_along_ridge_ldu = self.box_depth_ldu
                self.roof_across_ridge_ldu = self.box_width_ldu
                self.ridge_axis = "z"
                self.piece_rotations = {
                    "left": Identity().rotate(90, YAxis),
                    "right": Identity().rotate(-90, YAxis)
                }
            case "east-west":
                # Ridge along X; slopes face north/south (Z axis)
                self.roof_along_ridge_ldu = self.box_width_ldu
                self.roof_across_ridge_ldu = self.box_depth_ldu
                self.ridge_axis = "x"
                self.piece_rotations = {
                    "left": Identity().rotate(0, YAxis),
                    "right": Identity().rotate(180, YAxis)
                }

        # Roof height from the across-ridge half-span
        half_across = self.roof_across_ridge_ldu / 2
        self.roof_height_ldu = half_across * math.tan(math.radians(slope_angle))

        self.num_pieces_along_ridge = math.ceil(
            self.roof_along_ridge_ldu / self.piece_step_along_ridge
        )
        self.num_rows_per_side = math.ceil(
            half_across / self.piece_step_across_ridge
        )

    def _build_side_slope(self, slope_side: Literal["left", "right"]) -> None:
        """Build the slope on one side of the roof, either left or right, and place it on top of the side of the box."""
        piece = Piece(part=SlopeBrick452X1,
                      rotation=self.piece_rotations[slope_side],
                      colour=self.colour)

        self._fill_region(
            piece=piece,
            slope_side=slope_side,
        )

    def _fill_region(self,
                     piece: Piece,
                     slope_side: Literal["left", "right"],
    ) -> None:
        """Fill one slope side with slope bricks, row by row from eave to ridge."""
        for row in range(self.num_rows_per_side):
            for col in range(self.num_pieces_along_ridge):
                p = piece.copy()

                y = row * self.piece_height_ldu
                along_pos = col * self.piece_step_along_ridge

                # Each row steps inward from the eave toward the ridge
                if slope_side == "left":
                    across_pos = (row - 1.5) * self.piece_step_across_ridge
                    along_pos += studs_to_ldu(1)
                    piece.colour = Red
                else:
                    across_pos = (
                        self.roof_across_ridge_ldu
                        - (row + 0.5) * self.piece_step_across_ridge
                    )

                if self.ridge_axis == "z":
                    x, z = across_pos, along_pos
                else:
                    x, z = along_pos, across_pos

                p.position = Vector(x=x, y=y, z=z)
                self.add_piece(p)


# class FlatRoof:
#     """A flat roof is a roof that is almost level, with a slight slope for drainage. 
#     Flat roofs are often used in commercial buildings and modern architecture."""

#     def __init__(self) -> None:
#         pass