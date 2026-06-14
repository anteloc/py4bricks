"""A two-storey House with a balcony, beside a single-storey neighbour."""

from pathlib import Path

from py4bricks.llm import COTTAGE, STONE_GREY, House, Scene

scene = Scene("House test")

# Two-storey house: balcony opens off a door on the upper floor.
scene.place_at(
    House(
        width_studs=24, length_studs=18, palette=COTTAGE,
        storeys=2, balcony="south", chimney=True,
    ),
    studs_x=0, studs_z=0,
)

# Single-storey neighbour.
scene.place_at(
    House(
        width_studs=18, length_studs=14, palette=STONE_GREY,
        storeys=1, chimney=True,
    ),
    studs_x=34, studs_z=0,
)

file_path = Path(__file__).with_suffix(".mpd")
scene.render_file(file_path)
print(f"House test rendered to {file_path.name}")
