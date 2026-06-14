"""Tall buildings: one-call towers and an explicit setback stack.

House.tower(...) builds a tripartite base/shaft/crown skyscraper with setbacks
and a curtain-wall skin from a single footprint; House.from_tiers(...) gives
explicit control of each tier.
"""

from pathlib import Path

from py4bricks.llm import MODERN, SANDSTONE, STONE_GREY, Footprint, House, Scene

scene = Scene("Towers")

# Square 28-storey skyscraper — one call.
scene.place_at(
    House.tower(Footprint().add_block(x=0, z=0, width=22, length=22), palette=MODERN, storeys=28),
    studs_x=0, studs_z=0,
)

# Slim, taller tower with gentler setbacks.
scene.place_at(
    House.tower(
        Footprint().add_block(x=0, z=0, width=14, length=14),
        palette=STONE_GREY, storeys=34, setback_studs=1,
    ),
    studs_x=34, studs_z=0,
)

# L-footprint tower — setbacks work on any footprint.
scene.place_at(
    House.tower(
        Footprint().add_block(x=0, z=0, width=18, length=18).add_block(x=18, z=0, width=10, length=10),
        palette=SANDSTONE, storeys=22,
    ),
    studs_x=60, studs_z=0,
)

# Explicit setback stack via from_tiers (wedding-cake).
wedding_cake = [
    (Footprint().add_block(x=0, z=0, width=24, length=24), 4),
    (Footprint().add_block(x=2, z=2, width=20, length=20), 8),
    (Footprint().add_block(x=5, z=5, width=14, length=14), 6),
]
scene.place_at(House.from_tiers(wedding_cake, palette=MODERN), studs_x=92, studs_z=0)

file_path = Path(__file__).with_suffix(".mpd")
scene.render_file(file_path)
print(f"Tower demo rendered to {file_path.name}")
