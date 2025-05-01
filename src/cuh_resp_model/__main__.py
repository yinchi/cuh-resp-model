"""Serves the Dash app for the cuh-resp-model module."""

from sys import argv
from .app import app

port = argv[1] if len(argv) >= 1 else 8050
app.run(port=argv[1])
