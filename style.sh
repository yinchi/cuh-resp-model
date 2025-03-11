#!/usr/bin/env bash
cd `git root`
uv run isort src/
uv run autopep8 src/
uv run pylint src/
