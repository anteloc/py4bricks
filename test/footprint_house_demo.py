"""Complete buildings from footprints: L-plan, U-plan courtyard, and a bay.

Each is one House.from_footprint(...) (or House.l_plan) call: an enriched shell
with continuous interiors and exterior-only openings, plus a roof per block.
"""

from pathlib import Path

from py4bricks.llm import COTTAGE, SANDSTONE, STONE_GREY, Footprint, House, Scene

scene = Scene("Footprint houses: L, U, bay")

# L-plan (2 storeys) — l_plan is a two-block footprint under the hood.
scene.place_at(
    House.l_plan(
        main_width=20, main_length=16, wing_width=12, wing_length=12,
        palette=COTTAGE, storeys=2, chimney=True,
    ),
    studs_x=0, studs_z=0,
)

# U-plan courtyard — three blocks.
u_plan = (
    Footprint()
    .add_block(x=0, z=0, width=20, length=6)
    .add_block(x=0, z=0, width=6, length=18)
    .add_block(x=14, z=0, width=6, length=18)
)
scene.place_at(
    House.from_footprint(u_plan, palette=SANDSTONE, storeys=1, entrance="south", chimney=True),
    studs_x=40, studs_z=0,
)

# Main block + a projecting bay — the bay is just another block.
with_bay = (
    Footprint()
    .add_block(x=0, z=0, width=18, length=14)
    .add_block(x=5, z=-4, width=8, length=4)
)
scene.place_at(
    House.from_footprint(with_bay, palette=STONE_GREY, storeys=1, entrance="north", chimney=True),
    studs_x=70, studs_z=0,
)

file_path = Path(__file__).with_suffix(".mpd")
scene.render_file(file_path)
print(f"Footprint house demo rendered to {file_path.name}")
