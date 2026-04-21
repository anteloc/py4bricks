"""slab.py — LLM-friendly Slab: a flat horizontal surface of Plate pieces.

A Slab tiles a width_studs × length_studs rectangle with Plate1X2 (laid
along the X axis) and Plate1X1 fillers where the width is odd.  Multiple
plate layers can be stacked via height_plates for thicker floors or ceilings.

Coordinate conventions (slab-local, same as Scene):
    X — east (+) / west (-)    width direction
    Z — north (+) / south (-)  length direction
    Y — up (plates)            layer stacking direction

Tiling rule (per layer, per Z row):
    Greedy left-to-right along X: use Plate1X2 when x+1 is still in range,
    Plate1X1 otherwise.  This keeps the layout simple and deterministic.

Usage:
    floor   = Slab(width_studs=20, length_studs=15, colour=Tan)
    ceiling = Slab(width_studs=20, length_studs=15, colour=Dark_Tan, height_plates=3)
    scene.place_at(floor,   studs_x=0, plates_y=0,  studs_z=0)
    scene.place_at(ceiling, studs_x=0, plates_y=24, studs_z=0)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour

from py4bricks.geometry import Vector, plates_to_ldu, studs_to_ldu
from py4bricks.library.parts.plates import Plate1X1, Plate1X2
from py4bricks.llm.group import Group
from py4bricks.pieces import Piece


class Slab(Group):
    """A flat horizontal surface tiled with Plate1X2 / Plate1X1 pieces.

    Extends Group so the Scene can place and transform it like any other
    Group.  Children are built lazily on the first access after construction.

    Tiling is row-by-row in Z, left-to-right in X:
        use Plate1X2 while x + 1 < width_studs, else Plate1X1.
    Each layer sits one plate above the previous (plates_to_ldu step = 1).
    """

    def __init__(
        self,
        *,
        width_studs: int,
        length_studs: int,
        colour: Colour,
        height_plates: int = 1,
        name: str = "",
    ) -> None:
        super().__init__(name=name)

        self._width_studs  = width_studs
        self._length_studs = length_studs
        self._colour       = colour
        self._height_plates = height_plates
        self._dirty = True

    # ------------------------------------------------------------------
    # children property — overrides the dataclass field from Group
    # ------------------------------------------------------------------

    @property  # type: ignore[override]
    def children(self) -> list[Piece | Group]:
        """Lazily build the tile grid on first access."""
        if self._dirty:
            self._build()
            self._dirty = False
        return self._children

    @children.setter
    def children(self, value: list) -> None:
        # Intercepts Group dataclass setting self.children = [] at __init__ time.
        self._children: list[Piece | Group] = value

    # ------------------------------------------------------------------
    # Internal build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Fill _children with Plate1X2 / Plate1X1 tiles covering the rectangle."""
        self._children.clear()

        for plate_layer in range(self._height_plates):
            layer_y = plates_to_ldu(plate_layer)

            for z in range(self._length_studs):
                pos_z = studs_to_ldu(z)
                x = 0
                while x < self._width_studs:
                    use_1x2 = x + 1 < self._width_studs
                    part    = Plate1X2 if use_1x2 else Plate1X1
                    tile    = Piece(part=part, colour=self._colour)
                    tile.position = Vector(
                        x=studs_to_ldu(x),
                        y=layer_y,
                        z=pos_z,
                    )
                    self._children.append(tile)
                    x += 2 if use_1x2 else 1
