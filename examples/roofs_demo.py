"""Two boxes, each capped with a gabled Roof running a different way."""

from pathlib import Path

from py4bricks.library.colours import Blue, Red, White
from py4bricks.llm import Box, Roof, Scene

scene = Scene("Roofs demo: east-west and north-south ridges")

# --- Box with an east-west ridge ---------------------------------------
box_ew = Box(name="Box_EW", width_studs=15, length_studs=12, height_bricks=4, colour=White, bonded=True)
scene.place_at(box_ew, studs_x=0, plates_y=0, studs_z=0)
scene.place_on_top_of(
    Roof(name="Roof_EW", width_studs=box_ew.width_studs, length_studs=box_ew.length_studs,
         ridge_running="east-west", colour=Red),
    box_ew,
)

# --- Box with a north-south ridge, placed to the east ------------------
box_ns = Box(name="Box_NS", width_studs=12, length_studs=22, height_bricks=4, colour=White, bonded=True)
scene.place_at(box_ns, studs_x=20, plates_y=0, studs_z=0)
scene.place_on_top_of(
    Roof(name="Roof_NS", width_studs=box_ns.width_studs, length_studs=box_ns.length_studs,
         ridge_running="north-south", colour=Blue),
    box_ns,
)

scene.render_file(Path(__file__).with_suffix(".mpd"))
print("Roofs demo rendered to roofs_demo.mpd")
