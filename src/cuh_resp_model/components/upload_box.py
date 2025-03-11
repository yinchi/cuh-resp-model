"""A file upload component."""

import dash_mantine_components as dmc
from dash import dcc
from dash_compose import composition


@composition
def upload_box(
    label: str,
    _id: str,
    prompt_id: str,
    initial_prompt: str
):
    """Create a DMC box with label for uploading a file."""
    with dmc.Stack(gap=0) as ret:
        yield label
        with dcc.Upload(
            id=_id,
            accept='.xlsx'
        ):
            with dmc.Box(
                style={
                    "width": "100%",
                    "border-width": "1px",
                    "border-style": "dashed",
                    "border-color": "var(--app-shell-border-color)",
                    "padding": "10px",
                    "border-radius": "5px"
                }
            ):
                with dmc.Center():
                    with dmc.Text(
                        id=prompt_id,
                    ):
                        yield initial_prompt
    return ret
