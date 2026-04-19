"""Box: a rectangular structure with four walls"""

from __future__ import annotations

from py4bricks.colour import Colour
from py4bricks.geometry import (
    Identity,
    Matrix,
    Vector,
    plates_to_brick_height,
    brick_height_to_plates
)
from py4bricks.library.colours import White
from py4bricks.llm.wall import Wall
from py4bricks.llm.wall_layout import WallLayout
from py4bricks.utils import single_value_or_error


class Box:
    """A Box is a rectangular structure defined by four walls: north, south, east and west.

    It can be used as a building block for more complex structures like houses or rooms.
    It's based on an underlying WallLayout of four walls, which defines the dimensions and positions of the walls, and can be accessed for more advanced use cases.

    """

    def __init__(self, 
                 box_width_studs: int, 
                 box_depth_studs: int, 
                 box_height_plates: int = 0, 
                 box_height_bricks: int = 0,
                 position: Vector = Vector(0, 0, 0),
                 colour: Colour = White,
    ) -> None:

        height_values = (
            box_height_bricks,
            plates_to_brick_height(box_height_plates),
        )

        _box_height_bricks = single_value_or_error(height_values, 0, "height (bricks or plates)")

        self.box_width_studs = box_width_studs
        self.box_depth_studs = box_depth_studs
        self.box_height_bricks = _box_height_bricks
        self.box_height_plates = brick_height_to_plates(_box_height_bricks)

        self.wall_layout = WallLayout(
            walls_height_bricks=_box_height_bricks,
            first_wall_position=position,
            colour=colour,
        )

        self.wall_layout.append_wall(name="south_wall", 
                                     wall_width_studs=box_width_studs, 
                                     facing="south")
        self.wall_layout.append_wall(name="west_wall", 
                                     wall_width_studs=box_depth_studs, 
                                     facing="west")
        self.wall_layout.append_wall(name="north_wall", 
                                     wall_width_studs=box_width_studs, 
                                     facing="north")
        self.wall_layout.append_wall(name="east_wall", 
                                     wall_width_studs=box_depth_studs, 
                                     facing="east")

    def __getitem__(self, wall_name: str) -> Wall:
        """Retrieve a wall by name, e.g. box["north_wall"]"""
        return self.wall_layout[wall_name]

    def __repr__(self) -> str:
        return repr(self.wall_layout)
