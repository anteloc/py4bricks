"""house.py — a one-call assembler for a complete, good-looking building.

All the primitives for a handsome building exist (Box, Wall enrichment,
composed Window/Door, Roof with eaves, Chimney …) but they're spread across
many classes. `House` wires them together with tasteful defaults so an LLM can
get a finished building in a couple of lines, then customise from there.

    from py4bricks.llm import House, Scene, COTTAGE

    scene = Scene("village")
    # a cosy single-storey cottage
    scene.place_at(House(width_studs=22, length_studs=16, palette=COTTAGE, chimney=True))
    # a two-storey house with a balcony off an upper-floor door
    scene.place_at(
        House(width_studs=24, length_studs=18, palette=COTTAGE,
              storeys=2, balcony="south", chimney=True),
        studs_x=30,
    )
    scene.render_file("houses.mpd")


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

7. ADD A LITTLE LIFE. A `Planter`, `Lamp`, or `Sign` by the door. A `Balcony`
   belongs on an UPPER storey, opening off a door — never floating over the
   ground entrance; `House(storeys=2, balcony="south")` wires that up for you.

8. TEXTURE, SPARINGLY. `wall.mottle(colour=palette.base, ratio=0.10)` for
   subtle masonry variation — keep the ratio low so it doesn't look noisy.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.palette import Palette
    from py4bricks.llm.types import Facing, Orientation

from py4bricks.geometry import PLATES_PER_BRICK_HEIGHT
from py4bricks.llm.box import Box
from py4bricks.llm.group import Group
from py4bricks.llm.massing import BayWindow
from py4bricks.llm.openings import Door, Window
from py4bricks.llm.ornaments import Balcony, Chimney
from py4bricks.llm.roof import Roof


class House(Group):
    """A complete multi-storey building: enriched walls, rhythmic openings per
    floor, a roof, an optional chimney and balcony.

    width_studs / length_studs — footprint, in studs.
    palette       — colour scheme (its roles drive every colour choice).
    storeys       — number of floors (default 1).
    storey_height_bricks — height of one floor in brick rows (default 9; must
                    fit a door).
    door_facing   — which wall carries the ground entrance (default "south").
    windows       — auto-place evenly-spaced windows on every floor (default True).
    chimney       — add a chimney on the ridge (default False).
    texture       — subtle wall mottling (default False).
    balcony       — wall to carry a balcony (default None). A balcony always
                    opens off a door on the TOP storey, so this requires
                    storeys >= 2.
    ridge_running — roof ridge direction; defaults to along the longer side.
    """

    def __init__(
        self,
        *,
        width_studs: int,
        length_studs: int,
        palette: Palette,
        storeys: int = 1,
        storey_height_bricks: int = 9,
        door_facing: Facing = "south",
        windows: bool = True,
        chimney: bool = False,
        texture: bool = False,
        balcony: Facing | None = None,
        bay: Facing | None = None,
        ridge_running: Orientation | None = None,
        name: str = "house",
    ) -> None:
        super().__init__(name=name)
        if balcony is not None and storeys < 2:
            raise ValueError(
                "balcony requires storeys >= 2 — it must open off a door on an "
                "upper floor, not over the ground entrance",
            )

        height_bricks = storeys * storey_height_bricks
        self._occupied: list[tuple[Facing, int, int, int, int]] = []  # side,x0,x1,r0,r1

        box = Box(
            width_studs=width_studs, length_studs=length_studs,
            height_bricks=height_bricks, colour=palette.wall, bonded=True,
            name=f"{name}_walls",
        )
        self._enrich_walls(box, palette, texture, storeys, storey_height_bricks)

        # Ground entrance.
        self._add_door(box, palette, door_facing, 0, width_studs, length_studs)
        # A balcony always opens off a door on the top storey.
        balcony_floor_row = (storeys - 1) * storey_height_bricks
        if balcony is not None:
            self._add_door(box, palette, balcony, balcony_floor_row, width_studs, length_studs)

        if windows:
            self._add_windows(box, palette, storeys, storey_height_bricks, width_studs, length_studs)
        self.add(box)

        if balcony is not None:
            self._add_balcony(palette, balcony, width_studs, length_studs, balcony_floor_row)
        if bay is not None:
            self._add_bay(palette, bay, width_studs, length_studs, height_bricks)

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

    def _enrich_walls(
        self, box: Box, palette: Palette, texture: bool,
        storeys: int, storey_height_bricks: int,
    ) -> None:
        for side in ("south", "east", "north", "west"):
            wall = box[side]
            wall.foundation(colour=palette.base, brick_rows=1)
            wall.coping(colour=palette.trim)
            if texture:
                wall.mottle(colour=palette.base, ratio=0.10, seed=1)
            # A string course at each floor line separates the storeys.
            for s in range(1, storeys):
                wall.band(brick_row=s * storey_height_bricks, colour=palette.trim)

    def _add_door(
        self, box: Box, palette: Palette, side: Facing, brick_row: int,
        width_studs: int, length_studs: int,
    ) -> None:
        door = Door(colour=palette.trim, leaf_colour=palette.accent)
        wall_width = self._wall_width(side, width_studs, length_studs)
        x = max(0, (wall_width - door.opening_width_studs) // 2)
        self._occupied.append(
            (side, x, x + door.opening_width_studs, brick_row, brick_row + door.opening_height_bricks),
        )
        box[side].insert(piece=door, studs_x=x, brick_row=brick_row)

    def _add_windows(
        self, box: Box, palette: Palette, storeys: int, storey_height_bricks: int,
        width_studs: int, length_studs: int,
    ) -> None:
        proto = Window(colour=palette.trim)
        win_w, win_h = proto.opening_width_studs, proto.opening_height_bricks
        total = storeys * storey_height_bricks

        for s in range(storeys):
            row = s * storey_height_bricks + max(1, (storey_height_bricks - win_h) // 2)
            if row + win_h > total:            # storey too short for a window
                continue
            for side in ("south", "east", "north", "west"):
                wall_width = self._wall_width(side, width_studs, length_studs)
                for x in self._even_positions(wall_width, win_w):
                    if self._is_occupied(side, x, x + win_w, row, row + win_h):
                        continue
                    box[side].insert(
                        piece=Window(colour=palette.trim, sill_colour=palette.trim),
                        studs_x=x, brick_row=row,
                    )

    def _add_balcony(
        self, palette: Palette, side: Facing,
        width_studs: int, length_studs: int, floor_row: int,
    ) -> None:
        """Hang a balcony on `side`, open back against the wall, floor level with
        the top-storey door it opens off, projecting outward.

        The balcony is sized to its door (door width + a margin each side) and
        wall-centred, so it lines up with the centred door rather than dwarfing
        it. Keeping the width even (door width is even) makes the centres match
        exactly for any wall width.
        """
        wall_width = self._wall_width(side, width_studs, length_studs)
        door_width = Door(colour=palette.trim).opening_width_studs
        margin = 2
        b_width = door_width + 2 * margin
        b_depth = 4
        plates_y = floor_row * PLATES_PER_BRICK_HEIGHT

        bal = Balcony(
            width_studs=b_width, depth_studs=b_depth,
            floor_colour=palette.base, railing_colour=palette.trim,
            name=f"{self.name}_balcony",
        )

        # Centre the balcony on its door. The door is inserted in wall-local
        # coords whose X flips to world on the north/west walls, so derive the
        # door's world centre per side and set `c` (the floor's low edge along
        # the wall) to align with it. facing=side then projects the floor out.
        door_x = max(0, (wall_width - door_width) // 2)
        half_door = door_width // 2
        half_bal = b_width // 2
        w, length = width_studs, length_studs
        if side == "south":     # door world x = door_x; floor projects -Z
            c = door_x + half_door - half_bal
            sx, sz = c + b_width, 0
        elif side == "north":   # door world x flips; floor projects +Z
            c = (w - 1 - door_x - half_door) - half_bal
            sx, sz = c, length - 1
        elif side == "east":    # door world z = door_x; floor projects +X
            c = door_x + half_door - half_bal
            sx, sz = w - 1, c + b_width
        else:                   # west: door world z flips; floor projects -X
            c = (length - 1 - door_x - half_door) - half_bal
            sx, sz = 0, c

        self.place_at(bal, studs_x=sx, plates_y=plates_y, studs_z=sz, facing=side)

    def _add_bay(
        self, palette: Palette, side: Facing,
        width_studs: int, length_studs: int, height_bricks: int,
    ) -> None:
        """Attach a full-height projecting bay window, wall-centred on `side`."""
        bay_width, bay_depth = 8, 4
        bay = BayWindow(
            width_studs=bay_width, depth_studs=bay_depth, height_bricks=height_bricks,
            colour=palette.wall, window_colour=palette.trim, cap_colour=palette.trim,
            name=f"{self.name}_bay",
        )
        self._project(bay, side, bay_width, floor_row=0,
                      width_studs=width_studs, length_studs=length_studs)

    def _project(
        self, item: Group, side: Facing, item_width: int, *,
        floor_row: int, width_studs: int, length_studs: int,
    ) -> None:
        """Place `item` (built projecting +Z, open back at z=0) flush against the
        exterior of `side`, wall-centred, projecting outward. Handles the
        north/west wall-local X flip so the centring lands in world coords."""
        wall_width = self._wall_width(side, width_studs, length_studs)
        c0 = max(0, (wall_width - item_width) // 2)   # wall-local low edge
        plates_y = floor_row * PLATES_PER_BRICK_HEIGHT
        w, length = width_studs, length_studs
        if side == "south":
            sx, sz = c0 + item_width, 0
        elif side == "north":
            sx, sz = (w - 1) - c0 - item_width, length - 1
        elif side == "east":
            sx, sz = w - 1, c0 + item_width
        else:                                          # west
            sx, sz = 0, (length - 1) - c0 - item_width
        self.place_at(item, studs_x=sx, plates_y=plates_y, studs_z=sz, facing=side)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def l_plan(
        cls,
        *,
        main_width: int,
        main_length: int,
        wing_width: int,
        wing_length: int,
        palette: Palette,
        storeys: int = 1,
        storey_height_bricks: int = 9,
        door_facing: Facing = "south",
        chimney: bool = False,
        name: str = "l_house",
    ) -> Group:
        """Compose two House blocks into an L-shaped footprint.

        The wing attaches to the east end of the main block, back-aligned
        (north edges flush), so the L opens to the south-east. Each block keeps
        its own enriched walls and roof; the gables meet at the inner corner.
        """
        g = Group(name=name)
        main = House(
            width_studs=main_width, length_studs=main_length, palette=palette,
            storeys=storeys, storey_height_bricks=storey_height_bricks,
            door_facing=door_facing, chimney=chimney, name=f"{name}_main",
        )
        g.place_at(main, studs_x=0, studs_z=0)
        wing = House(
            width_studs=wing_width, length_studs=wing_length, palette=palette,
            storeys=storeys, storey_height_bricks=storey_height_bricks,
            name=f"{name}_wing",
        )
        # Share the corner: overlap one stud in X, flush at the back (north).
        g.place_at(wing, studs_x=main_width - 1, studs_z=main_length - wing_length)
        return g

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

    def _is_occupied(self, side: Facing, x0: int, x1: int, r0: int, r1: int) -> bool:
        """True if (side, x0..x1, r0..r1) overlaps any door/opening already placed."""
        return any(
            s == side and x0 < ox1 and ox0 < x1 and r0 < or1 and or0 < r1
            for (s, ox0, ox1, or0, or1) in self._occupied
        )
