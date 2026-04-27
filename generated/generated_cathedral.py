"""
# ============================================================
# GOTHIC CATHEDRAL BUILD PLAN
# ============================================================
#
# "Cathedral of Light" — a cross-plan Gothic cathedral with
# stained glass, interior columns, transept arms, apse, and
# twin entrance spires.
#
# Plan (top view, south = entrance, north = altar):
#
#         ┌──────────────────────┐  z=62
#         │        APSE          │   (altar chapel)
#         └──────────┬───────────┘  z=52
#                    │
# ┌──────────────────┼──────────────────┐  z=44
# │   LEFT TRANSEPT  │  RIGHT TRANSEPT  │  (crossing arms)
# └──────────────────┼──────────────────┘  z=30
#                    │
#    ┌───────────────┴────────────────┐  z=0
# ┌──┘         NAVE (24x52)          └──┐
# │  L.TOWER   (stained glass aisles)   R.TOWER  │
# └─────────────────────────────────────────────────┘  z=-2
#
# Components:
#   Nave          : 24 x 52 studs, 18 bricks — pointed stained glass
#   Transept arms : 14 x 14 studs, 14 bricks — flanking the crossing
#   Apse          : 24 x 10 studs, 14 bricks — altar chapel
#   Towers        :  8 x 10 studs, 26 bricks — soaring spires
#   Columns       : 5 pairs inside nave, circular, 12 bricks
#
# Stained glass (Trans colours):
#   Nave east  : Trans_Light_Blue   (morning light)
#   Nave west  : Trans_Orange       (evening light)
#   Nave south : Trans_Yellow       (golden entrance)
#   Nave north : Trans_Red          (altar glow)
#   Transepts  : Trans_Green        (cross arms)
#   Towers     : Trans_Yellow       (beacon light)
#   Apse       : Trans_Red          (sanctuary)
#
# Roofs (all Red tile):
#   Nave        : ridge N-S  (slopes fold E-W)
#   Transepts   : ridge E-W  (perpendicular to nave — classic crossing)
#   Apse        : ridge N-S
#   Tower spires: ridge N-S  (rise above nave roof line)  [Dark_Grey slate]
#
# Build order:
#   1. Body group — all sections placed, then roofs placed on top
#   2. Terrain derived from body.studs_x x body.studs_z (auto-fits any building)
#   3. Scene: terrain placed at origin, body placed on top of terrain
# ============================================================
"""
from pathlib import Path

from py4bricks.library.colours import (
    Dark_Bluish_Grey,
    Dark_Grey,
    Light_Bluish_Grey,
    Red,
    Reddish_Brown,
    Tan,
    Trans_Green,
    Trans_Light_Blue,
    Trans_Orange,
    Trans_Red,
    Trans_Yellow,
)
from py4bricks.library.parts.doors import Door1X4X6Frame
from py4bricks.library.parts.windows import Window1X4X3WithoutShutterTabs
from py4bricks.llm import Box, Column, Group, Roof, Scene, Slab
from py4bricks.pieces import Piece

# ── Dimensions ────────────────────────────────────────────────────────────────

NAVE_WIDTH   = 24   # studs E-W
NAVE_LENGTH  = 52   # studs N-S
NAVE_HEIGHT  = 18   # bricks

WING_W       = 14   # studs E-W per transept arm
WING_D       = 14   # studs N-S
WING_H       = 14   # bricks
CROSSING_Z   = 30   # stud offset from south where transept crosses nave

APSE_D       = 10   # studs N-S (altar chapel depth)
APSE_H       = 14   # bricks

TOWER_W      = 8    # studs E-W
TOWER_D      = 10   # studs N-S
TOWER_H      = 26   # bricks — rises well above the nave

COL_HEIGHT   = 12   # bricks — interior nave columns

# ── Part factories ────────────────────────────────────────────────────────────

def win(colour) -> Piece:
    """Fresh stained-glass window piece in the given Trans colour."""
    return Piece(part=Window1X4X3WithoutShutterTabs, colour=colour)

def make_door() -> Piece:
    """Heavy oak front door."""
    return Piece(part=Door1X4X6Frame, colour=Reddish_Brown)

# ── Nave ──────────────────────────────────────────────────────────────────────

def make_nave() -> Box:
    """Central nave: tall Gothic walls with two levels of stained glass.

    South facade: entrance door flanked by golden windows and a rose window.
    East/West sides: 3 bays each, two windows per bay (triforium + clerestory).
    North (altar): red glow windows and a high central rose window.
    """
    nave = Box(
        name="nave",
        width_studs=NAVE_WIDTH,
        length_studs=NAVE_LENGTH,
        height_bricks=NAVE_HEIGHT,
        colour=Light_Bluish_Grey,
        bonded=True,
    )

    # South facade — entrance door + flanking windows + rose window high up
    nave["south"].insert(piece=make_door(),          studs_x=10, brick_row=0)
    nave["south"].insert(piece=win(Trans_Yellow),    studs_x=2,  brick_row=4)
    nave["south"].insert(piece=win(Trans_Yellow),    studs_x=17, brick_row=4)
    nave["south"].insert(piece=win(Trans_Yellow),    studs_x=10, brick_row=13)  # rose window

    # North wall — altar glow
    nave["north"].insert(piece=win(Trans_Red),       studs_x=3,  brick_row=4)
    nave["north"].insert(piece=win(Trans_Red),       studs_x=16, brick_row=4)
    nave["north"].insert(piece=win(Trans_Red),       studs_x=9,  brick_row=13)  # rose window

    # East aisle — morning light (3 bays, lower + upper clerestory)
    for bay_z in (7, 23, 39):
        nave["east"].insert(piece=win(Trans_Light_Blue), studs_x=bay_z, brick_row=4)
        nave["east"].insert(piece=win(Trans_Light_Blue), studs_x=bay_z, brick_row=12)

    # West aisle — evening light
    for bay_z in (7, 23, 39):
        nave["west"].insert(piece=win(Trans_Orange),     studs_x=bay_z, brick_row=4)
        nave["west"].insert(piece=win(Trans_Orange),     studs_x=bay_z, brick_row=12)

    return nave


def add_nave_columns(nave: Box) -> None:
    """5 pairs of circular columns forming the interior nave aisles.

    Added directly to the nave Box so they are elevated with it.
    Left colonnade (x=4) and right colonnade (x=19), one column per bay.
    """
    prototype = Column(
        height_bricks=COL_HEIGHT,
        colour=Light_Bluish_Grey,
        shape="circular",
    )
    for bay_z in (6, 16, 26, 36, 46):
        nave.place_at(prototype.copy(), studs_x=4,  plates_y=0, studs_z=bay_z)
        nave.place_at(prototype.copy(), studs_x=19, plates_y=0, studs_z=bay_z)

# ── Transept wing ─────────────────────────────────────────────────────────────

def make_transept_wing() -> Box:
    """One transept arm: lower than the nave, large end window in Trans_Green."""
    wing = Box(
        name="transept_wing",
        width_studs=WING_W,
        length_studs=WING_D,
        height_bricks=WING_H,
        colour=Light_Bluish_Grey,
        bonded=True,
    )
    # End windows on all four faces (the east/west walls face outward from the crossing)
    for wall in ("south", "north"):
        wing[wall].insert(piece=win(Trans_Green), studs_x=4, brick_row=4)
    wing["east"].insert(piece=win(Trans_Green),   studs_x=4, brick_row=4)
    wing["west"].insert(piece=win(Trans_Green),   studs_x=4, brick_row=4)
    return wing

# ── Apse ──────────────────────────────────────────────────────────────────────

def make_apse() -> Box:
    """Altar chapel: same width as nave, shallow, with red sanctuary windows."""
    apse = Box(
        name="apse",
        width_studs=NAVE_WIDTH,
        length_studs=APSE_D,
        height_bricks=APSE_H,
        colour=Light_Bluish_Grey,
        bonded=True,
    )
    apse["north"].insert(piece=win(Trans_Red), studs_x=4,  brick_row=4)
    apse["north"].insert(piece=win(Trans_Red), studs_x=15, brick_row=4)
    apse["east"].insert( piece=win(Trans_Red), studs_x=2,  brick_row=4)
    apse["west"].insert( piece=win(Trans_Red), studs_x=5,  brick_row=4)
    return apse

# ── Tower ─────────────────────────────────────────────────────────────────────

def make_tower() -> Box:
    """Entrance spire: tall Dark_Bluish_Grey tower, narrow windows on each face."""
    tower = Box(
        name="tower",
        width_studs=TOWER_W,
        length_studs=TOWER_D,
        height_bricks=TOWER_H,
        colour=Dark_Bluish_Grey,
        bonded=True,
    )
    # Narrow slit windows at two levels (slit = 4 wide, fits the part)
    for wall in ("south", "north"):
        tower[wall].insert(piece=win(Trans_Yellow), studs_x=2, brick_row=8)
        tower[wall].insert(piece=win(Trans_Yellow), studs_x=2, brick_row=18)
    for wall in ("east", "west"):
        tower[wall].insert(piece=win(Trans_Yellow), studs_x=2, brick_row=8)
        tower[wall].insert(piece=win(Trans_Yellow), studs_x=2, brick_row=18)
    return tower

# ── Terrain ───────────────────────────────────────────────────────────────────

def make_terrain(constructed: Group) -> Slab:
    """Stone-flag terrain that auto-fits the full footprint of any building.

    Dimensions are derived from the assembled group's bounding box, so the
    slab always covers exactly what was built — no hardcoded dimensions needed.
    """
    terrain_width  = constructed.studs_z if constructed.orientation in ("east", "west") else constructed.studs_x
    terrain_length = constructed.studs_x if constructed.orientation in ("east", "west") else constructed.studs_z
    return Slab(
        name="terrain",
        width_studs=terrain_width,
        length_studs=terrain_length,
        colour=Tan,
    )

# ── Scene assembly ────────────────────────────────────────────────────────────

scene = Scene("Cathedral of Light")

body = Group()

# ── Sections ──────────────────────────────────────────────────────────────────

nave = make_nave()
add_nave_columns(nave)
body.place_at(nave, studs_x=0, plates_y=0, studs_z=0)

# Transept arms flush with nave walls (±1 stud overlap is invisible)
left_wing = make_transept_wing()
body.place_at(left_wing, studs_x=-(WING_W - 1), plates_y=0, studs_z=CROSSING_Z)

right_wing = make_transept_wing()
body.place_at(right_wing, studs_x=NAVE_WIDTH - 1, plates_y=0, studs_z=CROSSING_Z)

# Apse directly north of nave
apse = make_apse()
body.place_at(apse, studs_x=0, plates_y=0, studs_z=NAVE_LENGTH)

# Twin towers flanking the south entrance
left_tower = make_tower()
body.place_at(left_tower, studs_x=-TOWER_W, plates_y=0, studs_z=-2)

right_tower = make_tower()
body.place_at(right_tower, studs_x=NAVE_WIDTH - 1, plates_y=0, studs_z=-2)

# ── Roofs ─────────────────────────────────────────────────────────────────────

# Nave roof — ridge N-S, overhangs east and west sides
body.place_on_top_of(
    Roof(name="nave_roof",
         width_studs=nave.width_studs, length_studs=nave.length_studs,
         ridge_running="north-south", colour=Red),
    nave,
)

# Transept roofs — ridge E-W (perpendicular to nave, classic Gothic crossing)
body.place_on_top_of(
    Roof(name="left_wing_roof",
         width_studs=left_wing.width_studs, length_studs=left_wing.length_studs,
         ridge_running="east-west", colour=Red),
    left_wing,
)
body.place_on_top_of(
    Roof(name="right_wing_roof",
         width_studs=right_wing.width_studs, length_studs=right_wing.length_studs,
         ridge_running="east-west", colour=Red),
    right_wing,
)

# Apse roof
body.place_on_top_of(
    Roof(name="apse_roof",
         width_studs=apse.width_studs, length_studs=apse.length_studs,
         ridge_running="north-south", colour=Red),
    apse,
)

# Tower spires — dark grey slate, soar above the nave roof line
body.place_on_top_of(
    Roof(name="left_spire",
         width_studs=TOWER_W, length_studs=TOWER_D,
         ridge_running="north-south", colour=Dark_Grey),
    left_tower,
)
body.place_on_top_of(
    Roof(name="right_spire",
         width_studs=TOWER_W, length_studs=TOWER_D,
         ridge_running="north-south", colour=Dark_Grey),
    right_tower,
)

# Terrain auto-fits the fully assembled body, then body is stacked on top
terrain = make_terrain(body)
scene.place_at(terrain, studs_x=0, plates_y=0, studs_z=0)

body_center = body.studs_x // 2, body.studs_z // 2
terrain_center = terrain.studs_x // 2, terrain.studs_z // 2
offset_x = terrain_center[0] - body_center[0]
offset_z = terrain_center[1] - body_center[1]

# FIXME terrain is not centered under the body and right/back studs values seem not to have any effect
scene.place_on_top_of(body, terrain, right_studs=offset_x, back_studs=offset_z)

# ── Render ────────────────────────────────────────────────────────────────────

output = Path("generated/generated_cathedral.mpd")
output.parent.mkdir(exist_ok=True)
scene.render_file(output)
print(f"Cathedral of Light rendered to {output}")
