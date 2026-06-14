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

9. FOR ANYTHING BEYOND A SINGLE BOX, use a Footprint + House.from_footprint —
   not several Houses placed side by side (that leaves walls/windows inside the
   join). Declare the massing as a union of rectangular blocks and the engine
   builds one continuous shell with exterior-only openings and a roof per block:

       from py4bricks.llm import Footprint, House, COTTAGE
       plan = (Footprint()
               .add_block(x=0,  z=0, width=20, length=16)   # main
               .add_block(x=20, z=4, width=12, length=12))  # wing -> L-plan
       house = House.from_footprint(plan, palette=COTTAGE, storeys=2,
                                    entrance="south", chimney=True)

   L / T / U / courtyard / wings / bays are all just blocks — a bay is simply a
   small block sharing an edge. House.l_plan is a two-block convenience wrapper.

10. FOR TALL BUILDINGS, switch the roof and skin and stack tiers:
    - roof_style="flat" gives a deck + parapet instead of a gable.
    - facade="curtain" gives a glazed skin (glass_segment_width/height tune the
      pane grid) instead of punched windows.
    - House.from_tiers([(footprint, storeys), ...]) stacks tiers; give higher
      tiers smaller (inset) footprints for setbacks — each lower tier's top
      becomes a terrace with a parapet.
    - House.tower(footprint, palette=..., storeys=...) is the one-call skyscraper:
      a tripartite base / shaft / crown with setbacks and a curtain wall.

        from py4bricks.llm import Footprint, House, MODERN
        tower = House.tower(Footprint().add_block(x=0, z=0, width=22, length=22),
                            palette=MODERN, storeys=28)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from py4bricks.colour import Colour
    from py4bricks.llm.palette import Palette
    from py4bricks.llm.types import Facing, Orientation

from py4bricks.geometry import PLATES_PER_BRICK_HEIGHT
from py4bricks.llm.box import Box
from py4bricks.llm.footprint import Footprint
from py4bricks.llm.group import Group
from py4bricks.llm.massing import BayWindow
from py4bricks.llm.openings import Door, Window
from py4bricks.llm.ornaments import Balcony, Chimney
from py4bricks.llm.roof import Roof
from py4bricks.llm.slab import Slab


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
    def from_footprint(
        cls,
        footprint: Footprint,
        *,
        palette: Palette,
        storeys: int = 1,
        storey_height_bricks: int = 9,
        entrance: Facing = "south",
        chimney: bool = False,
        texture: bool = False,
        facade: Literal["punched", "curtain"] = "punched",
        glass_segment_width: int = 2,
        glass_segment_height: int = 2,
        roof_style: Literal["gabled", "flat"] = "gabled",
        parapet_bricks: int = 1,
        floors: bool = True,
        floor_colour: Colour | None = None,
        name: str = "house",
    ) -> Group:
        """A complete multi-block building from a Footprint — the general path.

        Builds the enriched, opening-bearing shell (continuous interiors,
        exterior-only windows/door) from the footprint's exterior runs, then caps
        it: a per-block gabled roof (`roof_style="gabled"`, houses) or a flat deck
        with a parapet following the exterior boundary (`roof_style="flat"`, the
        tall-building top). A chimney applies to gabled roofs only.

        Any massing expressible as a union of rectangles works: L / T / U /
        courtyard / wings / bays are all just blocks — no special-casing.
        """
        height = storeys * storey_height_bricks
        building = Group(name=name)

        shell = footprint.build_shell(
            height_bricks=height, colour=palette.wall, bonded=True, storeys=storeys,
            foundation_colour=palette.base, coping_colour=palette.trim, band_colour=palette.trim,
            mottle_colour=palette.base if texture else None,
            facade=facade, windows=True, window_colour=palette.trim, glass_colour=palette.glass,
            glass_segment_width=glass_segment_width, glass_segment_height=glass_segment_height,
            entrance=entrance, door_colour=palette.trim, leaf_colour=palette.accent,
            name=f"{name}_shell",
        )
        building.add(shell)

        if floors:
            cls._add_floors(
                building, footprint, palette, storeys, storey_height_bricks,
                roof_style, floor_colour, name,
            )

        top = height * PLATES_PER_BRICK_HEIGHT
        if roof_style == "flat":
            cls._add_flat_roof(building, footprint, palette, top, parapet_bricks, name)
        else:
            cls._add_gabled_roofs(building, footprint, palette, top, chimney, name)
        return building

    @staticmethod
    def _add_floors(
        building: Group, footprint: Footprint, palette: Palette,
        storeys: int, storey_height_bricks: int, roof_style: Literal["gabled", "flat"],
        floor_colour: Colour | None, name: str,
    ) -> None:
        """A floor at each storey level, plus a top ceiling. The floor of storey
        s+1 is the ceiling of storey s; under a gabled roof the top storey gets
        its own ceiling (a flat roof's deck already closes it).

        The floor covers only INTERIOR cells (the footprint eroded one stud at the
        exterior walls, but kept across shared block junctions), so it meets the
        walls' inner faces without overlapping them — no z-fighting — and its top
        sits at the storey base (one plate down), level with the door threshold.
        """
        colour = floor_colour or palette.base
        top_level = storeys + 1 if roof_style == "gabled" else storeys
        for level in range(top_level):
            y = level * storey_height_bricks * PLATES_PER_BRICK_HEIGHT - 1  # top at storey base
            for i, (x, z, w, length) in enumerate(footprint.blocks):
                slab = Slab(
                    width_studs=w, length_studs=length, colour=colour,
                    name=f"{name}_floor{level}_{i}",
                )
                building.place_at(slab, studs_x=x, plates_y=y, studs_z=z)

    @classmethod
    def tower(
        cls,
        footprint: Footprint,
        *,
        palette: Palette,
        storeys: int = 20,
        storey_height_bricks: int = 6,
        base_storeys: int = 3,
        crown_storeys: int = 2,
        setback_studs: int = 2,
        entrance: Facing = "south",
        glass_segment_width: int = 2,
        glass_segment_height: int = 1,
        name: str = "tower",
    ) -> Group:
        """One-call skyscraper: a tripartite base / shaft / crown with setbacks.

        From a single ground footprint, builds three stacked tiers — a full-width
        base (podium, with the entrance), a slightly set-back shaft (the bulk of
        the floors), and a further set-back crown — all in a curtain-wall skin
        with a parapet at each setback and the top. It's `from_tiers` with
        tasteful proportions chosen for you; reach for `from_tiers` directly when
        you want explicit control of every tier.

            tower = House.tower(
                Footprint().add_block(x=0, z=0, width=22, length=22),
                palette=MODERN, storeys=28,
            )
        """
        base = max(1, min(base_storeys, storeys))
        crown = max(0, min(crown_storeys, storeys - base))
        shaft = max(0, storeys - base - crown)

        tiers: list[tuple[Footprint, int]] = [(footprint, base)]
        if shaft > 0:
            tiers.append((footprint.inset(setback_studs), shaft))
        if crown > 0:
            tiers.append((footprint.inset(setback_studs * (2 if shaft > 0 else 1)), crown))

        return cls.from_tiers(
            tiers, palette=palette, storey_height_bricks=storey_height_bricks,
            entrance=entrance, facade="curtain",
            glass_segment_width=glass_segment_width, glass_segment_height=glass_segment_height,
            name=name,
        )

    @classmethod
    def from_tiers(
        cls,
        tiers: list[tuple[Footprint, int]],
        *,
        palette: Palette,
        storey_height_bricks: int = 8,
        entrance: Facing = "south",
        facade: Literal["punched", "curtain"] = "curtain",
        glass_segment_width: int = 2,
        glass_segment_height: int = 2,
        texture: bool = False,
        parapet_bricks: int = 2,
        name: str = "tower",
    ) -> Group:
        """A tall building as a vertical stack of (Footprint, storeys) tiers.

        Each tier is a shell stacked on the one below; give higher tiers smaller
        (inset) footprints for setbacks — a podium-and-tower / wedding-cake
        massing. Every tier is capped with a flat deck + parapet: a terrace for
        the lower tiers (where the next tier steps back), the crown for the top.
        Only the ground tier gets a foundation and the entrance.

            tiers = [
                (Footprint().add_block(x=0, z=0, width=24, length=24), 4),  # podium
                (Footprint().add_block(x=2, z=2, width=20, length=20), 8),  # mid
                (Footprint().add_block(x=5, z=5, width=14, length=14), 6),  # tower
            ]
            tower = House.from_tiers(tiers, palette=MODERN)
        """
        building = Group(name=name)
        base_brick = 0  # cumulative height of tiers placed so far
        for i, (footprint, storeys) in enumerate(tiers):
            height = storeys * storey_height_bricks
            shell = footprint.build_shell(
                height_bricks=height, colour=palette.wall, bonded=True, storeys=storeys,
                foundation_colour=palette.base if i == 0 else None,
                coping_colour=palette.trim, band_colour=palette.trim,
                mottle_colour=palette.base if texture else None,
                facade=facade, windows=True, window_colour=palette.trim, glass_colour=palette.glass,
                glass_segment_width=glass_segment_width, glass_segment_height=glass_segment_height,
                entrance=entrance if i == 0 else None,
                door_colour=palette.trim, leaf_colour=palette.accent,
                name=f"{name}_tier{i}",
            )
            building.place_at(shell, studs_x=0, plates_y=base_brick * PLATES_PER_BRICK_HEIGHT, studs_z=0)
            base_brick += height
            # The next tier (if any) sits on this tier's deck; its footprint marks
            # where this parapet must not run (else it interpenetrates the wall above).
            above = tiers[i + 1][0].cells() if i + 1 < len(tiers) else None
            cls._add_flat_roof(
                building, footprint, palette,
                base_brick * PLATES_PER_BRICK_HEIGHT, parapet_bricks, f"{name}_tier{i}",
                exclude_under=above,
            )
        return building

    @staticmethod
    def _add_gabled_roofs(
        building: Group, footprint: Footprint, palette: Palette,
        top: int, chimney: bool, name: str,
    ) -> None:
        """One gabled roof per block, seated on the wall tops; optional chimney."""
        roofs: list[tuple[Group, int, int, int, int, Orientation]] = []
        for i, (x, z, w, length) in enumerate(footprint.blocks):
            rr: Orientation = "east-west" if w >= length else "north-south"
            # A footprint block spans the full w x length studs, but Roof is sized
            # like a Box (which covers width-1), so +1 each way to reach the far walls.
            roof = Roof(
                name=f"{name}_roof{i}", width_studs=w + 1, length_studs=length + 1,
                ridge_running=rr, colour=palette.roof, eaves_studs=1,
            )
            building.place_at(roof, studs_x=x, plates_y=top, studs_z=z)
            roofs.append((roof, x, z, w, length, rr))

        if chimney and roofs:
            roof, x, z, w, length, rr = roofs[0]
            if rr == "east-west":
                cr, cb = max(0, w // 3), max(0, length // 2 - 1)
            else:
                cr, cb = max(0, w // 2 - 1), max(0, length // 3)
            building.place_on_top_of(
                Chimney(colour=palette.base, height_bricks=4, cap_colour=palette.trim, skirt_bricks=2),
                roof, right_studs=cr, back_studs=cb,
            )

    @staticmethod
    def _add_flat_roof(
        building: Group, footprint: Footprint, palette: Palette,
        top: int, parapet_bricks: int, name: str,
        exclude_under: set[tuple[int, int]] | None = None,
    ) -> None:
        """A flat deck (a Slab per block) plus a parapet that follows the exterior
        boundary — reusing the boundary tracer, so it stays continuous around any
        massing and never raises an interior parapet.

        `exclude_under` (the footprint of the tier above) drops parapet segments
        the upper tier sits on, so the parapet rims only the exposed terrace."""
        for i, (x, z, w, length) in enumerate(footprint.blocks):
            deck = Slab(width_studs=w, length_studs=length, colour=palette.roof, name=f"{name}_deck{i}")
            building.place_at(deck, studs_x=x, plates_y=top, studs_z=z)

        parapet = footprint.build_shell(
            height_bricks=parapet_bricks, colour=palette.wall, bonded=True,
            coping_colour=palette.trim, exclude_under=exclude_under, name=f"{name}_parapet",
        )
        building.place_at(parapet, studs_x=0, plates_y=top, studs_z=0)

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
        """An L-shaped house: a main block plus a wing sharing one edge.

        Now expressed as a two-block Footprint, so the shared wall is open
        (continuous interior) and every opening is exterior — fixing the old
        closed-box version's interior walls/windows.
        """
        plan = (
            Footprint()
            .add_block(x=0, z=0, width=main_width, length=main_length)
            .add_block(x=main_width, z=main_length - wing_length, width=wing_width, length=wing_length)
        )
        return cls.from_footprint(
            plan, palette=palette, storeys=storeys, storey_height_bricks=storey_height_bricks,
            entrance=door_facing, chimney=chimney, name=name,
        )

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
