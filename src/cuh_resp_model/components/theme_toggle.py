"""Dark theme toggle component for Dash Mantine."""

from pathlib import Path

import dash
import dash_mantine_components as dmc
from dash import Input, Output
from dash_iconify import DashIconify

from ..utils import read_file


# region layout
def theme_toggle():
    """Generate the theme toggle component."""
    return dmc.Switch(
        offLabel=DashIconify(
            icon="material-symbols:light-mode-rounded",
            width=15, color=dmc.DEFAULT_THEME["colors"]["yellow"][8]
        ),
        onLabel=DashIconify(
            icon="material-symbols:dark-mode-rounded",
            width=15,
            color=dmc.DEFAULT_THEME["colors"]["yellow"][6],
        ),
        id="color-scheme-toggle",
        persistence=True,
        color="grey",
        size="lg"
    )
# endregion


# region callbacks
dash.clientside_callback(
    read_file(Path(__file__).parent.resolve() / "theme_toggle.js"),
    Output("color-scheme-toggle", "id"),
    Input("color-scheme-toggle", "checked"),
)
# endregion
