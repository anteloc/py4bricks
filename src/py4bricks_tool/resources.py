"""Resource file access utilities."""

import codecs
from importlib import resources


def _get_resource(filename: str) -> str:
    return str(resources.files("py4bricks") / filename)


def _get_resource_content(filename: str) -> str:
    return codecs.open(_get_resource(filename), "r", encoding="utf-8").read()
