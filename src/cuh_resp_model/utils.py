"""Utility funtions."""

from os import PathLike

JSCode = str
"""String containing JavaScript code"""


def read_file(path: PathLike, binary=False) -> str | bytes:
    """Read a file and return its contents as a str or bytes."""
    if binary:
        with open(path, "rb") as f:
            return f.read()
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def drop_none(d: dict) -> dict:
    """Drop None values from a dict. Useful for supplying keyword arguments to a function
    only if certain conditions are met, using the ** operator."""
    return {k: v for k, v in d.items() if v is not None}
