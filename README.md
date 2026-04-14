# py4bricks
Produce LDraw/LEGO models via Agentic LLMs

> [!NOTE]
> This project began as a derivative of **pyldraw3** by **Harold Martin** ([hbmartin](https://github.com/hbmartin)), originally available at [https://github.com/hbmartin/pyldraw3](https://github.com/hbmartin/pyldraw3), a fork itself of [pyldraw](https://github.com/rienafairefr/python-ldraw), by **Matthieu Berthomé** ([rienafairefr](https://github.com/rienafairefr)) . It has since been substantially modified, including **TODO** brief summary of major changes.

## Setup

```
uv venv --python 3.14 # create venv
source .venv/bin/activate

uv sync # update dependencies

uv pip install... # install more packages if required

uv pip install -e . # make py4bricks available for importing while also editing

uv build # create dist bundles

uv run py4bricks --update # re-generate py4bricks.library from LDraw's complete.zip
# NOTE: for correct generation of part dimensions, it is required to rebuild/add the new parts to data/ldraw.db, table PART_BBOXES

```