"""Box: a rectangular structure with four walls"""

from __future__ import annotations

from typing import Literal

from py4bricks.colour import Colour
from py4bricks.errors import BuilderError
from py4bricks.geometry import (
    Vector,
    plates_to_brick_height,
    studs_to_ldu,
)
from py4bricks.library.colours import White
from py4bricks.utils import single_value_or_error

from .wall import Wall


class WallLayout:
    """A WallLayout is a set of walls interconnected by corners, one following the other.

    """

    def __init__(self,
                 walls_height_plates: int = 0,
                 walls_height_bricks: int = 0,
                 first_wall_position: Vector = Vector(0, 0, 0),
                 colour: Colour = White,
    ) -> None:
        self.first_wall_position = first_wall_position
        self.colour = colour
        self.walls: list[Wall] = []

        height_values = (
            walls_height_bricks,
            plates_to_brick_height(walls_height_plates),
        )

        self.walls_height_bricks = single_value_or_error(height_values, 0, "height (bricks or plates)")

    def append_wall(self,
                    name: str,
                    wall_width_studs: int,
                    facing: Literal["north", "south", "east", "west"],
    ) -> None:
        """Appends a new wall to the layout, connected to the previous wall by a corner.
        
        The first wall is placed at `first_wall_position`. Each subsequent wall is placed at the end of the previous wall, with a 90 degree clockwise rotation (e.g. if the first wall faces north, the second will face east, then south, then west...).

        """
        if not self.walls:
            self.walls.append(
                Wall(
                    name=name,
                    studs_width=wall_width_studs,
                    bricks_height=self.walls_height_bricks,
                    position=self.first_wall_position,
                    facing=facing,
                    colour=self.colour,
                ))
            return

        prev_wall = self.walls[-1]

        # TODO validate new wall's facing direction is not the same or opposite to the previous wall's facing direction


        prev_wall_end_pos = prev_wall.end_position


        # due to the fact that the end position is actually at a corner of the last brick,
        # manually creating this table by trial and error is easier than trying
        # to derive a formula based on the wall and piece geometry and offsets
        facing_offsets = {
            ("north", "east"): Vector(0, 0, studs_to_ldu(1)),   # ok
            ("north", "west"): Vector(-studs_to_ldu(1), 0, 0),  # ok
            ("south", "east"): Vector(studs_to_ldu(1), 0, 0),   # ok
            ("south", "west"): Vector(0, 0, -studs_to_ldu(1)),  # ok
            ("east", "north"): Vector(0, 0, -studs_to_ldu(1)),  # ok
            ("east", "south"): Vector(-studs_to_ldu(1), 0, 0), # ok
            ("west", "north"): Vector(studs_to_ldu(1), 0, 0), # ok
            ("west", "south"): Vector(0, 0, studs_to_ldu(1)), # ok
        }

        facings = (prev_wall.facing, facing)
        if facings not in facing_offsets:
            raise BuilderError(f"Invalid facing directions for new wall: {facings}. It cannot be the same or opposite as the previous wall's facing direction.")

        wall_pos = prev_wall_end_pos + facing_offsets[facings]

        wall = Wall.from_dimensions(
            name=name,
            studs_width=wall_width_studs - 1,  # corner brick belongs to previous wall
            bricks_height=self.walls_height_bricks,
            colour=self.colour,
        )
        wall.place(at=wall_pos, facing=facing)

        self.walls.append(wall)

    # retrieve walls by name on a dict-like way, e.g. wall_layout["north_wall"]
    def __getitem__(self, wall_name: str) -> Wall:
        for wall in self.walls:
            if wall.name == wall_name:
                return wall
        raise KeyError(f"Wall with name '{wall_name}' not found in the layout.")

    def __repr__(self) -> str:
        reprs = [repr(wall) for wall in self.walls]

        return "\n".join(reprs)
