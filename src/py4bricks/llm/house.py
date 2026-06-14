"""house.py — a one-call assembler for a complete, good-looking building.

All the primitives for a handsome building exist (Box, Wall enrichment,
composed Window/Door, Roof with eaves, Chimney …) but they're spread across
many classes. `House` wires them together with tasteful defaults so an LLM can
get a finished building in a couple of lines, then customise from there.

    from py4bricks.llm import House, Scene, COTTAGE

    scene = Scene("village")
    scene.place_at(House(width_studs=22, length_studs=16, palette=COTTAGE, chimney=True))
    scene.render_file("house.mpd")


STYLE COOKBOOK — how to make a building look good
-------------------------------------------------
`House` already applies these; reach for them by hand when composing your own:

1. PICK A PALETTE, don't pick colours. `from py4bricks.llm import SANDSTONE,
   COTTAGE, BRICK_RED, STONE_GREY, MODERN, TUDOR`. Read colours by role
   (`palette.wall`, `.trim`, `.accent`, `.roof`, `.base`, `.glass`).

2. ANCHOR THE BASE. Give every wall a darker foundation course:
   `wall.foundation(colour=palette.base)`. It grounds the building visually.

3. CAP THE WALLS. Never leave raw studs on top:
   `wall.coping(colour=palette.trim)`.

4. TRIM THE OPENINGS. Use composed `Window`/`Door` (frame + sill, optional
   shutters / flower box), not bare parts, and colour frames in `palette.trim`,
   door leaves in `palette.accent`.

5. GIVE OPENINGS RHYTHM. Space windows evenly with a corner margin; put one
   focal entrance (a `Door`, maybe a `Porch`/`Canopy`) on the front.

6. FINISH THE ROOF. A gabled `Roof(..., eaves_studs=1)` in `palette.roof`, and
   a `Chimney(..., skirt_bricks=3)` near the ridge.

7. ADD A LITTLE LIFE. A `Planter`, `Lamp`, or `Sign` by the door; a `Railing`
   on a balcony. A few details read as "designed".

8. TEXTURE, SPARINGLY. `wall.mottle(colour=palette.base, ratio=0.10)` for
   subtle masonry variation — keep the ratio low so it doesn't look noisy.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.palette import Palette
    from py4bricks.llm.types import Facing, Orientation

from py4bricks.llm.box import Box
from py4bricks.llm.group import Group
from py4bricks.llm.openings import Door, Window
from py4bricks.llm.ornaments import Chimney
from py4bricks.llm.roof import Roof


class House(Group):
    """A complete building: enriched walls, rhythmic openings, a roof, a chimney.

    width_studs / length_studs — footprint, in studs.
    height_bricks — wall height in brick rows (default 9; must fit the door).
    palette       — colour scheme (its roles drive every colour choice).
    door_facing   — which wall carries the entrance (default "south").
    windows       — auto-place evenly-spaced windows on every wall (default True).
    chimney       — add a chimney near the ridge (default False).
    texture       — subtle wall mottling (default False).
    ridge_running — roof ridge direction; defaults to along the longer side.
    """

    def __init__(
        self,
        *,
        width_studs: int,
        length_studs: int,
        palette: Palette,
        height_bricks: int = 9,
        door_facing: Facing = "south",
        windows: bool = True,
        chimney: bool = False,
        texture: bool = False,
        ridge_running: Orientation | None = None,
        name: str = "house",
    ) -> None:
        super().__init__(name=name)

        box = Box(
            width_studs=width_studs, length_studs=length_studs,
            height_bricks=height_bricks, colour=palette.wall, bonded=True,
            name=f"{name}_walls",
        )
        self._enrich_walls(box, palette, texture)
        self._add_door(box, palette, door_facing, width_studs, length_studs)
        if windows:
            self._add_windows(box, palette, door_facing, width_studs, length_studs, height_bricks)
        self.add(box)

        rr = ridge_running or ("east-west" if width_studs >= length_studs else "north-south")
        roof = Roof(
            name=f"{name}_roof", width_studs=width_studs, length_studs=length_studs,
            ridge_running=rr, colour=palette.roof, eaves_studs=1,
        )
        self.place_on_top_of(roof, box)

        if chimney:
            # Seat the chimney ON the ridge line, where the roof surface really
            # is at ridge height — off the ridge place_on_top_of would leave it
            # floating above the lower slope. The 2x2 base is centred on the
            # ridge (the -1 offsets), and a short skirt tucks it under the cap.
            if rr == "east-west":          # ridge runs along X, centred in Z
                c_right, c_back = max(0, width_studs // 3), max(0, length_studs // 2 - 1)
            else:                          # ridge runs along Z, centred in X
                c_right, c_back = max(0, width_studs // 2 - 1), max(0, length_studs // 3)
            self.place_on_top_of(
                Chimney(colour=palette.base, height_bricks=4, cap_colour=palette.trim, skirt_bricks=2),
                roof, right_studs=c_right, back_studs=c_back,
            )

    # ------------------------------------------------------------------
    # Assembly steps
    # ------------------------------------------------------------------

    def _enrich_walls(self, box: Box, palette: Palette, texture: bool) -> None:
        for side in ("south", "east", "north", "west"):
            wall = box[side]
            wall.foundation(colour=palette.base, brick_rows=1)
            wall.coping(colour=palette.trim)
            if texture:
                wall.mottle(colour=palette.base, ratio=0.10, seed=1)

    def _add_door(
        self, box: Box, palette: Palette, door_facing: Facing,
        width_studs: int, length_studs: int,
    ) -> None:
        door = Door(colour=palette.trim, leaf_colour=palette.accent)
        wall_width = self._wall_width(door_facing, width_studs, length_studs)
        door_x = max(0, (wall_width - door.opening_width_studs) // 2)
        self._door_span = (door_facing, door_x, door.opening_width_studs)
        box[door_facing].insert(piece=door, studs_x=door_x, brick_row=0)

    def _add_windows(
        self, box: Box, palette: Palette, door_facing: Facing,
        width_studs: int, length_studs: int, height_bricks: int,
    ) -> None:
        proto = Window(colour=palette.trim)
        win_w, win_h = proto.opening_width_studs, proto.opening_height_bricks
        row = max(1, (height_bricks - win_h) // 2)
        if row + win_h > height_bricks:        # too short to fit a window
            return

        for side in ("south", "east", "north", "west"):
            wall_width = self._wall_width(side, width_studs, length_studs)
            for x in self._even_positions(wall_width, win_w):
                if self._overlaps_door(side, x, win_w):
                    continue
                box[side].insert(
                    piece=Window(colour=palette.trim, sill_colour=palette.trim),
                    studs_x=x, brick_row=row,
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _wall_width(side: Facing, width_studs: int, length_studs: int) -> int:
        """Buildable width of a Box wall (corners drop one stud, per Box)."""
        return (width_studs - 1) if side in ("south", "north") else (length_studs - 1)

    @staticmethod
    def _even_positions(wall_width: int, win_width: int, margin: int = 2) -> list[int]:
        """Left-edge x of evenly-spaced windows across a wall, with corner margins."""
        usable = wall_width - 2 * margin
        if usable < win_width:
            return []
        count = max(1, min(4, (usable + 3) // (win_width + 3)))  # ~3-stud gaps
        if count == 1:
            return [margin + (usable - win_width) // 2]
        step = (usable - win_width) / (count - 1)
        return [int(round(margin + i * step)) for i in range(count)]

    def _overlaps_door(self, side: Facing, x: int, win_width: int) -> bool:
        """True if a window at (side, x) would clash with the entrance door."""
        door_side, door_x, door_w = self._door_span
        if side != door_side:
            return False
        return not (x + win_width <= door_x or x >= door_x + door_w)
