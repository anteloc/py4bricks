from __future__ import annotations
import math
from typing import Literal

from py4bricks.colour import Colour
from py4bricks.library.colours import Red
from py4bricks.library.parts.slopes import SlopeBrick452X1
from py4bricks.llm.box import Box
from py4bricks.geometry import Identity, Vector, YAxis, brick_height_to_ldu, ldu_to_plates, studs_to_ldu
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
        
        ref_wall = box_to_cover["west_wall"] if ridge_orientation == "north-south" else box_to_cover["south_wall"]

        # roof will be positioned just on top of the box, i.e. at the height of a wall
        roof_pos = ref_wall.position + Vector(0, brick_height_to_ldu(ref_wall.bricks_height), 0)

        super().__init__(position=roof_pos, rotation=ref_wall.rotation)


        self.box_to_cover = box_to_cover
        self.ridge_orientation = ridge_orientation
        self.colour = colour

        self.box_width_ldu = studs_to_ldu(box_to_cover.box_width_studs)
        self.box_depth_ldu = studs_to_ldu(box_to_cover.box_depth_studs)

        self._roof_calculations(slope_part=SlopeBrick452X1, slope_angle=45)

        self._build_side_slope("left", asc_desc="asc")
        # self._build_side_slope("right", asc_desc="desc") 


        # TODO implement a similar algorithm to Wall to position the slopes (both sides of the ridge) 
        # and then to fill in the gap to the non-sloped walls

    def _roof_calculations(self, slope_part: str, slope_angle: float) -> None:
        """Calculate the number of slope pieces needed to cover the roof, and the position of each piece on top of the box."""
        piece = Piece(part=slope_part, colour=self.colour)
        piece_height_ldu = piece.ldu_y
        piece_width_ldu = piece.ldu_z # will be aligned either in the x or z axis depending on the ridge orientation


        # arbirarily define the width and depth of the roof based on the ridge orientation, to simplify the calculations
        match self.ridge_orientation:
            case "north-south":
                self.roof_width_ldu, self.roof_depth_ldu = self.box_depth_ldu, self.box_width_ldu
                self.ridge_axis = "z"
                self.piece_rotations = {
                    "left": Identity().rotate(-90, YAxis),
                    "right": Identity().rotate(90, YAxis)
                }
            case "east-west":
                self.roof_width_ldu, self.roof_depth_ldu = self.box_width_ldu, self.box_depth_ldu
                self.ridge_axis = "x"
                self.piece_rotations = {
                    "left": Identity().rotate(0, YAxis),
                    "right": Identity().rotate(180, YAxis)
                }
        
        def height_from_slope(c1, slope):
            slope_rad = math.radians(slope)
            t = math.tan(slope_rad)
            c2 = c1 * t**2
            return c2
        
        c1 = self.roof_width_ldu / 2
        self.roof_height_ldu = height_from_slope(c1, slope_angle)

        self.num_pieces_high = math.ceil(self.roof_height_ldu / piece_height_ldu)
        self.num_pieces_wide = math.ceil(self.roof_depth_ldu / piece_width_ldu)


    def _build_side_slope(self, slope_side: Literal["left", "right"], asc_desc: Literal["asc", "desc"]) -> None:
        """Build the slope on one side of the roof, either left or right, and place it on top of the side of the box."""
        
        # (north, south) or (east, west) depending on ridge orientation
        # arbitrarily: left = 1st element of the tuple, right = 2nd element of the tuple
        ors = self.ridge_orientation.split("-")
        
        piece = Piece(part=SlopeBrick452X1, 
                      rotation=self.piece_rotations[slope_side],
                      colour=self.colour)
        high_start_pieces, high_stop_pieces, wide_start_pieces, wide_stop_pieces = 0, 0, 0, 0

        match slope_side:
            case "left":
                high_start_pieces = 0
                high_stop_pieces = self.num_pieces_high
                wide_start_pieces = 0
                wide_stop_pieces = self.num_pieces_wide // 2
            case "right":
                high_start_pieces = self.num_pieces_high
                high_stop_pieces = 0
                wide_start_pieces = self.num_pieces_wide // 2
                wide_stop_pieces = self.num_pieces_wide
        
        self._fill_region(
            piece=piece,
            asc_desc=asc_desc,
            rows_along_axis=self.ridge_axis,
            high_start_pieces=high_start_pieces,
            high_stop_pieces=high_stop_pieces,
            wide_start_pieces=wide_start_pieces,
            wide_stop_pieces=wide_stop_pieces,
        )

        # gable rows will be parallel to the ridge, which means placing pieces at the same height
            
    def _fill_region(self,
                     piece: Piece,
                     asc_desc: Literal["asc", "desc"],
                     rows_along_axis: str,
                     high_start_pieces: int,
                     high_stop_pieces: int,
                     wide_start_pieces: int,
                     wide_stop_pieces: int,
    ) -> None:
        """Fill the specified area of the wall with bricks."""

        row_step = 1 if asc_desc == "asc" else -1

        # for row in range(high_start_pieces, high_stop_pieces, row_step):
        for row in range(1):
            for row_idx in range(wide_start_pieces, wide_stop_pieces):
                p = piece.copy()

                x, y, z = 0, 0, 0
                y = row * piece.ldu_y
                
                match rows_along_axis:
                    case "x":
                        x = 0
                        z = row_idx * piece.ldu_x
                    case "z":
                        x = row_idx * piece.ldu_x
                        z = 0

                pos = Vector(
                    x=x,
                    y=y,
                    z=z,
                )
                p.position = pos
                self.add_piece(p)


# class FlatRoof:
#     """A flat roof is a roof that is almost level, with a slight slope for drainage. 
#     Flat roofs are often used in commercial buildings and modern architecture."""

#     def __init__(self) -> None:
#         pass