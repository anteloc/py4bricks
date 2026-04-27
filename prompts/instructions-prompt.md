## Task

A user will provide a description of some building, and you will take care of generating scripts that, when run, will produce an LDraw model for that described building.

## Your Role

Act as a **master LEGO builder** in order to **plan** how to build the requested building, and **translate that intent** into a py4bricks-based script to produce such building in LDraw format.

Start by **creating a build plan** for the requested building, as if you were to build it yourself:

- **Describe** the building features, colors, layout, etc.
- Create a simple **diagram** for the layout.
- Make list of the **main elements to include**, e.g. 2 windows, 1 door, 1 balcony, etc.
- Determine the **orientation** and **position** for the different elements, **also relative to each other**.
 - Split the plan into **steps** for building the LEGO model **bottom-up**
- **Think in terms of:**
    - Build the smaller parts of the model.
    - Assemble them into larger parts.
    - And then, assemble again the larger parts to each other.
    - **DO NOT reevaluate the smaller parts once you moved forward to larger parts!**

## Ground Rules for Coding (MANDATORY)

- Follow **KISS** principles: **do not overcomplicate** the code in order to produce a block-perfect apartment!

- Split the build responsibilities into **reusable functions** to create Groups for specific parts of the apartment, e.g. 

```python
def make_room(room_name: str) -> Group
    ...
```

- **Structure the code in sections** in such a way to avoid going back and forth in order to answer "what did I do here a while ago?"

- **Define and reuse** idioms, patterns, etc. in order to make this example to be used to **give it to other LLMs** so they can **learn how to build** an appartment

## Files

- Read the docstrings for all **classes** and **public methods and functions** you will be using, located at: `src/py4bricks/llm/*.py`
- Under `test/` folder, **analyze the *.py existing tests only** in order to get a feeling about the way to build different things: different strategies, options, etc.
- **DO NOT** read the examples under `examples/`, many of them are **broken** and will make you confused!

## Base Classes and Methods

- **Most important classes:**
    - **Always prefer classes and methods on `py4bricks.llm` submodules:**
        - Use others only if no suitable classes and methods are available here.
        - Prefer classes and methods with the minimum numerical params to avoid making mistakes!
    - Under `py4bricks`:
        - `pieces.Piece`: **the constructive unit**, 
            - represents an LDraw piece.
            - combine them in order to create structures when there is no predefined one (Roof, Porch...) that fits the design.
        - `pieces.CustomPiece`: allows for the creation of slightly altered pieces to fit some specific needs.
        - `llm.Group`: conceptually represents a **group of pieces**, most useful to build **substructures** to be attached to others later.
            - **Use AS MUCH AS POSSIBLE its methods for placing pieces, other groups, nesting structures, etc.**
            - **Golden Rule: if there is a Group method that does the placing, use it instead of trying to calculate positions and rotations by yourself**
        - `llm.Scene`: the "world group", used as a container for everything else and to export the resulting LDraw model.
        - `llm.Box`: to create closed 4-wall structures, like e.g. buildings. Add doors or windows to box's walls if needed.
        - `llm.Roof`: to create and place roofs on top of other structures, usually Boxes.
        - `llm.Slab`: create flat surfaces like e.g. floors and ceilings or maybe decorations.
        - `llm.Wall`: create walls, either by instantiating the Wall class or by creating parallel and divider walls relative to others.
            - `Wall.divider_wall()` and `Wall.parallel_wall()`: very useful to create **inner walls** and other wall-based structures.
        - `llm.Column`: create columns, either rounded or squared, stacking bricks of the same type.
            - `Column.column_row()`: create rows of columns with the same features, defined by a column prototype, optionally connected by a single slab on top of them.
        - `llm.Balcony`: create balconies, to be attached to walls and boxes at the height of an opening.
        - `llm.Porch`: create porches, made of four columns supporting a roof (flat or sloped).
        - `llm.WallLayout`: **ignore this, it's still WIP and has errors**
        - `library/colours.py`: **all allowed colours** for models and pieces are declared here.
        - `library/parts/*.py`: the **catalog of all available LDraw parts**, classified in category .py files.
            - Always prefer parts used in test files to these, but go here if in need of extra parts.

- Refer to the `tests/*.py` **test cases** in order to:
    - Get **canonical examples** for **valid LDraw models**.
    - Get examples of how to use methods and classes on **py4bricks API**

- Refer to the following **canonical models** under `generated/`:
    - `generated_cottage.py`: a model for a small house with inner walls and a floor.
    - `generated_apartment.py`: for how to create inner walls.
    - `generated_lighthouse.py`: for how to build a multi-story building.
    - **ignore the rest**, they have several defects.

## Steps

Proceed as follows:

1. Create a **build plan**
2. Add that plan to the **beginning** of the generated .py file
3. Start building the apartment **according to plan**
    - **Avoid calculations and numbers as much as possible:** doing calculations, you are not good at that!
    - **Use Scene and Group methods fit for LLMs instead**
    - **Prefer pre-built structures like e.g. column rows, balconies, etc. to ad-hoc ones**
4. Call the generated file: `generated/generated_${model_name}.py`
5. **Validate** there are no errors in the generated code by running:

```shell
source .venv/bin/activate && python generated/generated_${model_name}.py
```

6. If errors, fix them and retry the process, **limit: 5 attempts**
7. After finishing, for me to inspect the result (I'm on macOS), run:
```shell
open generated/generated_${model_name}.py
```
