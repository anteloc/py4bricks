"""Footprint wall-shells: L-plan, main+bay, and U-plan (courtyard).

Demonstrates the boundary tracer — walls only on exterior edges, shared edges
left open so interiors stay continuous, corners placed exactly like Box.
"""

from pathlib import Path

from py4bricks.library.colours import Light_Bluish_Grey, Sand_Green, Tan
from py4bricks.llm import Scene
from py4bricks.llm.footprint import Footprint

scene = Scene("Footprint shells: L, bay, U")

# L-plan: a main block with a wing sharing one edge.
l_plan = (
    Footprint()
    .add_block(x=0, z=0, width=20, length=16)
    .add_block(x=20, z=4, width=12, length=12)
)
scene.place_at(l_plan.build_shell(height_bricks=8, colour=Light_Bluish_Grey), studs_x=0, studs_z=0)

# Main block with a projecting bay (a small block sharing an edge).
with_bay = (
    Footprint()
    .add_block(x=0, z=0, width=18, length=14)
    .add_block(x=5, z=-4, width=8, length=4)
)
scene.place_at(with_bay.build_shell(height_bricks=8, colour=Tan), studs_x=44, studs_z=0)

# U-plan (courtyard): three blocks forming a U.
u_plan = (
    Footprint()
    .add_block(x=0, z=0, width=20, length=6)
    .add_block(x=0, z=0, width=6, length=18)
    .add_block(x=14, z=0, width=6, length=18)
)
scene.place_at(u_plan.build_shell(height_bricks=8, colour=Sand_Green), studs_x=70, studs_z=0)

file_path = Path(__file__).with_suffix(".mpd")
scene.render_file(file_path)
print(f"Footprint shell demo rendered to {file_path.name}")
