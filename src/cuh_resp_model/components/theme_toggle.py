"""Dark theme toggle component for Dash Mantine."""

from pathlib import Path

import dash_mantine_components as dmc
import plotly.io as pio
from dash import ALL, Input, Output, Patch, State, callback, clientside_callback
from dash_iconify import DashIconify

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
        id='switch-theme-toggle',
        persistence=True,
        color="grey",
        size="lg"
    )
# endregion


# region callbacks

TOGGLE_COLOR_SCHEME: JSCode = read_file(Path(__file__).parent.resolve() / "js/theme_toggle.js")
"""Toggle light/dark mode for the web app."""

dmc.add_figure_templates()
REDUCED_GRAPH_MARGINS = {'l': 30, 'r': 30, 't': 90, 'b': 30}
pio.templates["plotly"].layout.margin = REDUCED_GRAPH_MARGINS
pio.templates["mantine_dark"].layout.margin = REDUCED_GRAPH_MARGINS

clientside_callback(
    TOGGLE_COLOR_SCHEME,
    Output('switch-theme-toggle', "id"),
    Input('switch-theme-toggle', "checked")
)


@callback(
    Output({'themed_graph': True, 'name': ALL}, "figure"),
    Input('switch-theme-toggle', "checked"),
    State({'themed_graph': True, 'name': ALL}, "id"),
)
def update_figure(is_dark_mode, ids):
    """Apply light/dark theme to dcc.Graph figures."""
    template = pio.templates["mantine_dark"] if is_dark_mode else pio.templates["plotly"]
    patched_figures = []
    for _ in ids:
        patched_fig = Patch()
        patched_fig["layout"]["template"] = template
        patched_figures.append(patched_fig)

    return patched_figures

# endregion
