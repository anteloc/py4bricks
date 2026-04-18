from __future__ import annotations
import math
from typing import Literal

from py4bricks import part
from py4bricks.colour import Colour
from py4bricks.library.colours import Red
from py4bricks.library.parts.slopes import SlopeBrick452X1, SlopeBrick452X1Double
from py4bricks.library.parts.tiles import Tile1X1WithGroove
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
                 colour: Colour = Red,
    ) -> None:
        """Create a pitched roof for the given box, with the given ridge orientation and colour.
        
        First piece of the roof will be placed on top of the box, 
        at the height of selected wall according to orientation, over the origin of that wall.
        
        """
        self.box_to_cover = box_to_cover
        self.ridge_orientation = ridge_orientation
        self.colour = colour

        self.slope_part = SlopeBrick452X1
        self.ridge_part_even = SlopeBrick452X1Double
        self.ridge_part_odd = Tile1X1WithGroove
        self.slope_angle = 45
        
        match ridge_orientation:
            case "north-south":
                self.ref_wall = box_to_cover["west_wall"]
                self.width_studs = box_to_cover.box_depth_studs
                self.pieces_rotation = {
                    "left": Identity().rotate(0, axis=YAxis),
                    "right": Identity().rotate(180, axis=YAxis),
                }
            case "east-west":
                self.ref_wall = box_to_cover["south_wall"]
                self.width_studs = box_to_cover.box_width_studs
                self.pieces_rotation = {
                    "left": Identity().rotate(90, axis=YAxis),
                    "right": Identity().rotate(-90, axis=YAxis),
                }
            case _:
                raise ValueError(f"Invalid ridge orientation: {ridge_orientation}")


        self.even_width = self.width_studs % 2 == 0
        self.finishing_part = self.ridge_part_even if self.even_width else self.ridge_part_odd

        def height_from_c1_and_slope(c1, slope):
            alpha_rad = math.radians(slope)
            t = math.tan(alpha_rad)
            height = c1 * t**2
            return height
        
        half_width_ldu = studs_to_ldu(self.width_studs) / 2
        self.height_ldu = height_from_c1_and_slope(half_width_ldu, self.slope_angle)

        slope_piece = Piece(part=self.slope_part, colour=self.colour)
        self.height_in_pieces = int(self.height_ldu / slope_piece.ldu_y)
        self.width_in_pieces = int(self.width_studs / slope_piece.studs_x)

        # roof will be positioned just on top of the box, i.e. at the height of a wall
        # self.roof_pos = self.ref_wall.position + Vector(0, brick_height_to_ldu(self.ref_wall.bricks_height), 0)
        self.roof_pos = self.ref_wall.position

        super().__init__(position=self.roof_pos, rotation=self.ref_wall.rotation)

        self._build_roof()


    def _build_roof(self):
        first_left_piece = Piece(part=self.slope_part, 
                                 position=Vector(0, self.ref_wall.ldu_y, 0), 
                                 rotation=self.pieces_rotation["left"],
                                 colour=self.colour)

        self.add_piece(first_left_piece)

        # create a row by attaching new pieces to the previous one
        prev_left_piece = first_left_piece
        print(f"Adding left slope pieces, total: {self.width_in_pieces}")
        for _ in range(1, self.width_in_pieces):
            p = prev_left_piece.copy()
            Piece.attach(piece=p, to=prev_left_piece, side="right")
            prev_left_piece = p
            self.add_piece(p)


