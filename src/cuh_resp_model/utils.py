"""Utility funtions."""

from os import PathLike


def read_file(path: PathLike, binary=False) -> str | bytes:
    """Read a file and return its contents as a str or bytes."""
    if binary:
        with open(path, "rb") as f:
            return f.read()
    else:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
