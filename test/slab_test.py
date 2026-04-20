"""
Slab test — a 20×15 floor slab placed inside a Box.

The slab sits at plates_y=0 (ground level), matching the box footprint.
A second slab at plates_y=24 (8 bricks up) acts as the ceiling.

Slab tiling (top view):
    X — width_studs=20, tiled with Plate1X2 along X, Plate1X1 for odd remainder
    Z — length_studs=15, one row of plates per stud

Box:
    width=20, length=15, height=8 bricks, bonded

                      z=15
    ┌──────────────────────────────┐
    │   Slab 20×15 (floor)         │
    └──────────────────────────────┘
    x=0                          x=20
                      z=0
"""

from pathlib import Path

from py4bricks.library.colours import Dark_Tan, Light_Grey, Tan
from py4bricks.llm import Scene
from py4bricks.llm.box import Box
from py4bricks.llm.slab import Slab

scene = Scene()

box = Box(
    width_studs=20,
    length_studs=15,
    height_bricks=8,
    colour=Light_Grey,
    bonded=True,
)
scene.place_at(box, studs_x=0, plates_y=1, studs_z=0)

# Floor slab — ground level, 1 plate thick
floor = Slab(width_studs=20, length_studs=15, colour=Tan)
scene.place_at(floor, studs_x=0, plates_y=0, studs_z=0)

# Ceiling slab — top of the 8-brick walls, 3 plates thick for solidity
ceiling = Slab(width_studs=20, length_studs=15, colour=Dark_Tan, height_plates=3)
scene.place_at(ceiling, studs_x=0, plates_y=25, studs_z=0)

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Slab test rendered to slab_test.mpd")
