"""
Slab on-top-of test — floor, box, and ceiling stacked via scene.place_on_top_of().

Build order:
    1. floor   — placed at ground level with place_at()
    2. box     — stacked on top of floor via place_on_top_of()
    3. ceiling — stacked on top of box  via place_on_top_of()

No manual plate/brick arithmetic: place_on_top_of() derives the correct
Y position from the bounding box of the reference item.

                      z=15
    ┌──────────────────────────────┐
    │   ceiling (Dark_Tan, 3pl)    │  ← place_on_top_of(ceiling, box)
    │   box walls (Light_Grey, 8br)│  ← place_on_top_of(box, floor)
    │   floor  (Tan, 1pl)          │  ← place_at(..., plates_y=0)
    └──────────────────────────────┘
    x=0                          x=20
"""

from pathlib import Path

from py4bricks.library.colours import Dark_Tan, Light_Grey, Tan
from py4bricks.llm import Scene
from py4bricks.llm.box import Box
from py4bricks.llm.slab import Slab

scene = Scene()

# 1. Floor — 1 plate thick, at ground level
floor = Slab(width_studs=20, length_studs=15, colour=Tan)
scene.place_at(floor, studs_x=0, plates_y=0, studs_z=0)

# 2. Box — walls sit flush on top of the floor slab
box = Box(
    width_studs=20,
    length_studs=15,
    height_bricks=8,
    colour=Light_Grey,
    bonded=True,
)
scene.place_on_top_of(box, floor)

# 3. Ceiling — 3 plates thick, sits flush on top of the box walls
ceiling = Slab(width_studs=20, length_studs=15, colour=Dark_Tan, height_plates=3)
scene.place_on_top_of(ceiling, box)

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Slab on-top-of test rendered to slab_on_top_of_test.mpd")
