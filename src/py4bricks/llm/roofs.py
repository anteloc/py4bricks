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
                self.row_length_studs = box_to_cover.box_depth_studs
                self.span_studs = box_to_cover.box_width_studs
                self.pieces_rotation = {
                    "left": Identity().rotate(0, axis=YAxis),
                    "right": Identity().rotate(180, axis=YAxis),
                }
            case "east-west":
                self.ref_wall = box_to_cover["south_wall"]
                self.row_length_studs = box_to_cover.box_width_studs
                self.span_studs = box_to_cover.box_depth_studs
                self.pieces_rotation = {
                    "left": Identity().rotate(90, axis=YAxis),
                    "right": Identity().rotate(-90, axis=YAxis),
                }
            case _:
                raise ValueError(f"Invalid ridge orientation: {ridge_orientation}")


        self.even_width = self.span_studs % 2 == 0
        self.finishing_part = self.ridge_part_even if self.even_width else self.ridge_part_odd

        def height_from_c1_and_slope(c1, slope):
            alpha_rad = math.radians(slope)
            t = math.tan(alpha_rad)
            height = c1 * t**2
            return height
        
        half_width_ldu = studs_to_ldu(self.span_studs) / 2
        self.height_ldu = height_from_c1_and_slope(half_width_ldu, self.slope_angle)

        slope_piece = Piece(part=self.slope_part, colour=self.colour)
        self.height_in_pieces = int(self.height_ldu / slope_piece.ldu_y)
        self.row_length_in_pieces = int(self.row_length_studs / slope_piece.studs_x)

        # roof will be positioned just on top of the box, i.e. at the height of a wall
        # self.roof_pos = self.ref_wall.position + Vector(0, brick_height_to_ldu(self.ref_wall.bricks_height), 0)
        self.roof_pos = self.ref_wall.position

        super().__init__(position=self.roof_pos, rotation=self.ref_wall.rotation)

        self._build_roof()


    def _build_roof(self):
        self._build_first_row(side="left")
        self._build_first_row(side="right")

    def _build_first_row(self, side: Literal["left", "right"]) -> list[Piece]:
        """Build the first (bottom) row of slope pieces on one side of the roof.

        Left side starts at the ref_wall edge (Z=0 in group-local space).
        Right side starts at the opposite edge (Z=span_studs in group-local space).

        Because the right-side pieces are rotated 180° Y, attaching "right" would
        extend the row in the wrong direction. So right-side rows use side="left"
        to keep both rows extending along +X in group-local space.
        """
        pieces: list[Piece] = []

        # starting position: on top of the ref wall, at the corresponding edge
        start_z = 0 if side == "left" else studs_to_ldu(self.span_studs)

        first_piece = Piece(
            part=self.slope_part,
            position=Vector(0, self.ref_wall.ldu_y, start_z),
            rotation=self.pieces_rotation[side],
            colour=self.colour if side == "left" else Red,
        )
        pieces.append(first_piece)
        self.add_piece(first_piece)

        # attach direction flips for right side due to 180° Y rotation
        attach_side = "right" if side == "left" else "left"

        prev = first_piece
        for _ in range(1, self.row_length_in_pieces):
            p = prev.copy()
            Piece.attach(piece=p, to=prev, side=attach_side)
            prev = p
            pieces.append(p)
            self.add_piece(p)

        return pieces


