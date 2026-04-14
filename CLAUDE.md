# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`py4bricks` is a Python package creating python scripts that produce LDraw format files - a standard used by CAD applications that create LEGO buildings models. 

The package provides a specialized API to make easy for LLMs to generate such scripts in a DSL-like way, adapted both to the strenghts of Agentic LLMs and their shortcomings. 

## Your Role

You will help in developing an **LLM-friendly API** in such a way that it's easy for LLMs to **generate valid scripts based on that API** that produce LDraw .mpd models for **buildings**

This API will act as an **adapter for the non-LLM friendly current implementation**, in such a way that an LLM can **take advantage of the current features**, but using this new API.

Your role is twofold:

a) **Help** in developing and implementing the new API
b) **Test it** by generating and running scripts to evaluate their quality and their produced LDraw models.


## LLM-friendly API Features

- Coded in a style grounded in nonvisual terms. 
- Expressive for describing the scene, distances, directions and practical functions. 
- Favor the following:
   - Relational and route-based expresiveness, such as north/south/east/west, left/right, near/far, behind/in front, step-by-step layout, and landmarks.
   - Helpful for short-term memory, i.e. it allows for incrementally building the script with very few need to go back and forth to double check what has been done.
- Concise, idiomatic and simple.
- Delegate the heavy work to the current underlying implementation for both geometry and parts.
- The more the new API looks like a DSL for a blind person to create LEGO buildings, the better.

## Development Commands

This project uses uv for dependency management and packaging.
Before running any commands be sure this is done:

```bash
source .venv/bin/activate
uv pip install -e . # make py4bricks available for importing while also editing
```

## Architecture

### Core Components

1. **Non-LLM friendly API for geometry and pieces (`src/py4bricks/geometry.py` and `src/py4bricks/pieces.py`)**: 
   - Contains the main classes and functions for creating LDraw models via scripting.
   - Coordinates are expressed via LDrawVectors, where Y axis is **negative** for "up".

2. **LLM-friendly API (located under `py4bricks/llm/`)**:
   - We will be creating API files, functions, constants etc. in this subpackage.
   - The LLMs will be generating scripts that import the modules under this subpackage.
   - These modules will be delegating the heavy work to the Non-LLM friendly API.
   - Coordinates will be expressed by Vectors, on a conventional coordinates system where Y axis is **positive** for "up".
   - As much as possible, **use as units studs (X and Z axis) and plates (Y axis)**, then to be **translated to LDUs when delegating** to the Non-LLM friendly API.

### Key Classes

- `Piece` and `Group` (`py4bricks/pieces.py`) - Represents individual LEGO pieces and groups of pieces in models
- Geometry classes (`py4bricks/geometry.py`) - Matrix operations and 3D math
- Unless instructed otherwise, **do not** go to:
   - `py4bricks/generation/`: this is for generating py4bricks/library dir.
   - `py4bricks/library/`: there are huge files here, just convenient variables and dicts for the massive collection of LDraw parts.
   - exception: `py4bricks/library/colours.py` contains colour definitions, this is allowed for you to read

## Python Practices
- Always use or add type hints
- Prefer @dataclasses where applicable
- Always use f-string over string formatting or concatentation (except in logging strings)
- Use async generators and comprehensions when they might provide benefits
- Use underscores in large numeric literals
- Use walrus assignment := where applicable
- Prefer to use named arguments when calling a method with more than one argument
- Use "list" instead of "List" and "dict" instead of "Dict" and "|" instead of "Union" for types
- Use "Self" for applicable types
- Use Structural Pattern Matching (match...case) where applicable
- Always use pathlib.Path for file operations, never use os.path
- Define constants with meaningful names, instead of using "just numbers"
- Create constants for typical operations like e.g. `ROTATE_NORTH: Matrix = ...`
- Indicated mathematical operations instead of calculations, such as `middle_distance = WALL_LENGTH / 2` instead of `middle_distance = 0.75`
- Get a piece's dimensions from its properties: piece.studs_x, piece.plates_y, etc.
- Do NOT try to infer a piece's dimensions from the variable for the part that it represents, like e.g. Window1X4X3
- Do NOT try and fix linter errors in the code
