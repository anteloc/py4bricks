from __future__ import annotations
from typing import Literal
from pathlib import Path

from py4bricks.pieces import Group, Piece
from py4bricks.geometry import Vector, Matrix

class Scene(Group):
    """Represents a scene, which is the world where all pieces and groups exist.
    
    Space is represented as a grid with:
    - Dimensions measured in studs for X and Z, and plates for Y. 
    - The origin (0, 0, 0) at the center of the bottom face of the first piece added to the scene. 
    - Positive X is to the right, positive Y is up, and positive Z is towards the back.
    """
    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.grid_space: dict[tuple[int, int, int], Piece | Group] = {}

    def add_piece(self, piece: Piece) -> None:
        """Add a piece to the scene, placing it in the grid space according to that piece's position and rotation."""
        super().add_piece(piece)
        # Update the grid space with the new piece's position
        grid_position = (int(piece.studs_x), int(piece.plates_y), int(piece.studs_z))
        self.grid_space[grid_position] = piece

    def place_at(self, 
                piece: Piece, 
                studs_x: int, 
                plates_y: int, 
                studs_z: int, 
                orientation: Literal["north", "south", "east", "west"] = "north"
    ) -> Piece:
        """Place the given piece at the given studs coordinates with the given rotation, and adds it to the scene."""
        piece = Piece.place_at(piece=piece, 
                            studs_x=studs_x, 
                            plates_y=plates_y, 
                            studs_z=studs_z, 
                            orientation=orientation)
        self.add_piece(piece)
        return piece

    def attach_to(self, piece: Piece, to: Piece, side: Literal["back", "front", "right", "left"]) -> Piece:
        """Attach the given piece to the given piece on the given side, and adds it to the scene."""
        piece = Piece.attach_to(piece=piece, to=to, side=side)
        self.add_piece(piece)
        return piece

    def render_str(self) -> str:
        """Render the scene as an LDraw .mpd file contents"""
        return repr(self)

    def render_file(self, file_path: Path | str) -> None:
        """Render the scene to an LDraw .mpd file."""
        p_file_path = Path(file_path)
        p_file_path.write_text(self.render_str())

