"""A Box with a Roof on top, made of sloped bricks."""

from pathlib import Path

from py4bricks.library.colours import Red, White
from py4bricks.llm import Box, Roof, Scene

scene = Scene("A Box with a Roof on top, made of sloped bricks test")

box = Box(
    name="Box",
    width_studs=11,
    length_studs=22,
    height_bricks=3,
    colour=White,
    bonded=True,
)

scene.add(box)

roof = Roof(
    name="Roof",
    width_studs=box.width_studs,
    length_studs=box.length_studs,
    # ridge_running="east-west",
    ridge_running="north-south",
    colour=Red,
)

scene.place_on_top_of(roof, box)

scene.render_file(Path(__file__).with_suffix(".mpd"))

print("A Box with a Roof on top, made of sloped bricks test rendered to roof_test.mpd")
