from typing import Literal
from py4bricks.library.colours import Blue as North_Blue
from py4bricks.library.colours import Orange as West_Orange
from py4bricks.library.colours import Red as South_Red
from py4bricks.library.colours import Yellow as East_Yellow
from py4bricks.library.colours import Dark_Azure as Debug_Dark_Azure
from py4bricks.llm.group import Group
from py4bricks.pieces import Piece
from py4bricks.colour import Colour
from py4bricks.library.parts.bricks import Brick1X1

def debug_colour_by_orientation(orientation: Literal["north", "south", "east", "west"]):

    match orientation:
        case "north":
            return North_Blue
        case "south":
            return South_Red
        case "east":
            return East_Yellow
        case "west":
            return West_Orange
        case _:
            raise ValueError(f"Invalid orientation: {orientation}")

def debug_add_origin_marker(parent_group: Group, piece_or_group: Piece | Group, colour: Colour = Debug_Dark_Azure) -> None:
    origin_marker = Piece(part=Brick1X1, colour=colour)
    origin_marker.position = piece_or_group.position
    parent_group.add(origin_marker)
