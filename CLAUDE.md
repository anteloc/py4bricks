# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`py4bricks` is a Python package for LLM generation of python scripts that produce LDraw format files - a standard used by CAD applications that create LEGO models. The package provides facilities to create LDraw scene descriptions expressed as Python scripts that, when executed, will produce .mpd LDraw model files. 

## Development Commands

This project uses uv for dependency management and packaging.
Before running any commands be sure sure to active the venv `source .venv/bin/activate`


### Setup and Installation
```bash
uv sync                    # Install dependencies
uv run py4bricks --config # Get the current configuration for the CLI tool
uv run py4bricks --update # Download latest official LDraw complete.zip and generate py4bricks.library package
```

### Code Quality
```bash
uv run black .               # Format code (Black is configured)
```

### Building
```bash
uv build                     # Build package
```

## Architecture

### Core Components

1. **CLI Interface (`py4bricks/cli.py`)**: Main command-line interface with commands

2. **Dynamic Library Generation (`py4bricks/generation/`)**: 
   - Generates Python modules from LDraw parts libraries
   - Creates `py4bricks.library.*` namespace with parts organized by categories
   - Uses templates in `py4bricks/templates/` with Mustache templating

### Key Classes

- `Parts` (`py4bricks/parts.py`) - Manages parts catalog and loading
- `Piece` (`py4bricks/pieces.py`) - Represents individual LEGO pieces in models
- `Figure` (`py4bricks/figure.py`) - High-level minifigure construction
- Geometry classes (`py4bricks/geometry.py`) - Matrix operations and 3D math

### Configuration

- Uses OS-dependent cache directories for generated libraries
- Configuration stored in YAML format
- Parts libraries cached locally after download

## Development Notes

- The project supports Python 3.13+
- Uses uv for dependency management instead of traditional pip/setuptools
- Generated `py4bricks.library.*` modules should be regenerated when changing library versions
- Code style uses Black formatter and ruff linter

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