"""Dark theme toggle component for Dash Mantine."""

from pathlib import Path

import dash_mantine_components as dmc
from dash import clientside_callback, Input, Output
from dash_iconify import DashIconify

from cuh_resp_model.components.ids import ID_DARK_MODE_TOGGLE
from cuh_resp_model.utils import JSCode, read_file


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
        id=ID_DARK_MODE_TOGGLE,
        persistence=True,
        color="grey",
        size="lg"
    )
# endregion


# region callbacks
clientside_callback(
    read_file(Path(__file__).parent.resolve() / "js/theme_toggle.js"),
    Output("color-scheme-toggle", "id"),
    Input("color-scheme-toggle", "checked"),
)
# endregion
