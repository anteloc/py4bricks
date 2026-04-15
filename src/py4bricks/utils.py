"""Some utils functions."""

import os
import re
from typing import Any


def clean(input_string: str) -> str:
    """Clean a description string.

    :param input_string:
    :return:
    """
    return re.sub(r"\W+", "_", input_string).replace("_x_", "x")


def camel(input_string: str) -> str:
    """Return a CamelCase string."""
    return "".join(x for x in input_string.title() if not x.isspace())

def class_name(part_description: str) -> str:
    """Return a class name for a part description."""
    return clean(camel(part_description))


def ensure_exists(path: str) -> str:
    """Make the directory if it does not exist."""
    os.makedirs(path, exist_ok=True)  # noqa: PTH103
    return path


# https://stackoverflow.com/a/6027615
def flatten(input_dict: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten a dictionary."""
    items = []
    for key, value in input_dict.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)

def single_value_or_error(values: tuple, non_value: Any, param_name: str) -> Any:
    """Filter a tuple of values returning one if only one or else throw error."""
    matching_values = [v for v in values if v != non_value]
    err_msg: str

    match len(matching_values):
        case 0:
            err_msg = f"No value found for: {param_name}"
        case 1:
            return matching_values[0]
        case _:
            err_msg = f"Multiple values found for: {param_name}: {matching_values}"
    raise ValueError(err_msg)
