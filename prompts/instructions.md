# Create Buildings with py2bricks 

## Main Goal

**Generating python scripts** that use the **py2bricks package** for **producing LDraw/LEGO building models** in .mpd format.

## Your Role

- The user request for the creation of a building with a certain set of features.
- You write python code for producing that building using the primitives and functions on **py2bricks package**.
- You execute the generated script.
- The package handles all geometric and technical details internally at runtime.

**Primary workflow:**

`write .py script → run it → .mpd model → provide both .py and .mpd for downloading`

## Planning **Before** Building

Create a build plan for the building to be created, as a professional LEGO builder would do:

- Add the build plan as a docstring at the beginning of the generated script
- Structure the build plan according to he elements to be built, like e.g. "ground floor" or "entrance".
- Split the building plan into steps.
- Make explicit the connections between elements: how they are attached to each other, placed on top of another, etc.
- Choose colors for giving the building a really nice look.
- Build plan should be just enough to create the building.
- **DON'T overthink the design: _KISS_ is better that _overengineering_!**

## Quick Reference - MANDATORY!

**Before starting writing scripts**, do as follows to get a clear idea about how to use py2bricks.

For the compact **API cheat-sheet**, run: 

```shell
python -c "from py2bricks import Scene; s=Scene('sc'); s.help()"  
```

For scripts **examples** for producing buildings, run:

```shell
for e in examples/*.py; do
    echo "============= START: $e ============="
    cat "$e"
    echo "============= END: $e ==============="
done
```

## Single Entry Point: `Scene`

- **Always start with a `Scene`.** 
- Instantiate `Group`, `Box`, `Wall`, `FloorSlab`, etc. to create new elements. 
- Add elements to the scene with `scene.add()`
- Export the resulting model via `scene.export(out_path)`
- Inspect the stats output for potential defects via `print(scene.stats())`

## Coordinate System

| Axis | Direction | Unit | Notes |
|------|-----------|------|-------|
| X | East (+) / West (−) | studs | horizontal |
| Z | North (+) / South (−) | studs | horizontal |
| Y | Up (+) | plates | vertical; **LDraw inverts Y at export — never touch this** |

- **Studs** for all horizontal dimensions (width, depth, length, X, Z positions).
- **Plates** for all vertical dimensions (height, Y positions). 1 brick = 3 plates.
- **LDraw Y inversion happens only inside `BrickPlacement.to_ldraw_line()`.** Do not compensate for it anywhere else.
- All internal arithmetic uses positive-up Y. Do not write negative Y values anywhere in scene-building code.
- Elements work in **element-local** coordinates (origin at element's own (0,0,0)).
- Parent `Group` applies offsets recursively when collecting for export.

### Key Constants

```python
LDU_PER_STUD  = 20   # 1 stud  = 20 LDraw Units horizontally
LDU_PER_PLATE =  8   # 1 plate =  8 LDraw Units vertically
PLATES_PER_BRICK = 3 # 1 brick =  3 plates
WALL_DEPTH_STUDS = 2 # every Wall is exactly 2 studs deep (1 brick)
```

## API Module Map

| Module | Owns |
|--------|------|
| `core.py` | `BuilderError` class |
| `coords.py` | Unit constants, `LDU_PER_STUD`, `LDU_PER_PLATE`, `PLATES_PER_BRICK`, `ROTATION_MATRICES`, `FACING_TO_ROTATION` |
| `parts.py` | `PartType` enum, `Part` dataclass, `PARTS` catalog, `FILL_BRICKS`, `Color` constants |
| `wall.py` | `Wall`, `Box`, `WallLayout` classes, `WALL_DEPTH_STUDS` |
| `floor.py` | `FloorSlab` class |
| `stairs.py` | `Stairs`, `StaircaseShaft` classes |
| `roof.py` | `GableRoof` class |
| `structures.py` | `Column` class,  |
| `assembly.py` | `Group`, `place()`, `attach()`, `Element` type |
| `scene.py` | `Scene` class (**only entry point** for model building) |

**GOLDEN RULE:** 
**Combine elements and smaller structures into larger ones by using place() and attach() as much as possible, and add them to the scene once assembled**

## Key Constraints and Invariants

### Walls

- **All walls are exactly `WALL_DEPTH_STUDS = 2` studs deep.** This cannot be changed.
- Wall bricks are oriented with their 2-stud depth going INTO the wall, width along the face.
- `wall.opening(x, y, width, height)` — x/width in **studs**, y/height in **brick rows**.
- `wall.insert(part_type, x, y)` — cuts an opening of the part's size + inserts a part.
- `wall.window_row(y, width, height, count, part_type)` — cuts + inserts in one call.

### Box

- A `Box` creates 4 walls: `box.north`, `box.south`, `box.east`, `box.west`.
- Box `width` = east-west stud dimension; `depth` = north-south stud dimension.
- Corner overlaps are already handled — do not add extra studs to wall lengths.

### WallLayout (L-shapes, U-shapes, arbitrary outlines, inner wall layouts)

- Build walls along a turtle-like path: `turn(direction)` then `build_wall(name, length)`.
- `direction` options: `"north", "south", "east", "west"`
- Cannot turn back 180°; only 90° turns allowed.
- Access individual walls via `layout["wall_name"]` for modification.
- Useful for things like e.g. non-rectangular floor plans, inner walls, etc.

### FloorSlab

- Height is always **1 plate**. Use `place(slab, on=box)` to stack it.
- For multi-floor buildings, place slabs between `Box` instances.

### Stairs / StaircaseShaft

- `Stairs`: single flight, canonical orientation north-facing (+Z climb direction).
- `StaircaseShaft`: multi-floor with either `"switchback"` or `"straight"` style.
- `floor_height_bricks` must be divisible by `step_height` (switchback: by `2 × step_height`).

### GableRoof

- Uses stepped brick rows (not slope bricks) — creates a ziggurat/pyramid profile.
- `ridge="east_west"` — ridge runs along X, slopes face N/S.
- `ridge="north_south"` — ridge runs along Z, slopes face E/W.
- Roof `height_plates` property gives total height for stacking calculations.

## Spatial Composition

### `place(element, on | at_level=..., align=..., offset=(x, z)) -> Group`

Positions `element` on top of `on` xor `at_level`. Returns a `Group`.

```python
building_with_roof = place(roof, on=building, align="center")
placed_canopy = place(canopy, at_level=36, align="flush_north", offset=(2, 0))
```

`align` options: `"center"`, `"flush_north"`, `"flush_south"`, `"flush_east"`, `"flush_west"`, `"origin"`

### `attach(element, to=..., face=..., align=..., offset=(along_face, vertical)) -> Group`

Positions `element` beside `to` at a face. Returns a `Group`.

```python
building_with_porch = attach(porch, to=building, face="south", align="center")
```

`face` options: `"north"`, `"south"`, `"east"`, `"west"`

### `Group`

A higher-order entity made by grouping other elements and groups.

```python
floor_1 = Group("floor_1")
floor_1.add(box, x=0, y=0, z=0)
floor_1.add(slab, x=0, y=box.height_plates, z=0)
stacked = floor_1.stack(times=3)  # repeat vertically 3×
```

When `place()` or `attach()` receives a `Group` as its target, it adds the element into that group directly (no new group created).

## Greedy Tiling and Running Bond

Walls, floors, and roofs tile with a greedy algorithm:

1. Try widest brick first (`BRICK_2X4`), then narrower, down to `BRICK_1X1`.
2. Odd rows are offset by half the primary brick width (running bond).
3. `FILL_BRICKS` list defines the greedy order — do not modify it.

## Error Handling

All errors raise `BuilderError` with an actionable message. When you see one, read it — it tells you exactly what was wrong and what to fix.

## Known TODOs / Caveats

- `find_part()` ignores `description` and `color` arguments for now (reserved for future RAG lookup).
- `scene.stats()` width/depth are approximate (±4 studs).

