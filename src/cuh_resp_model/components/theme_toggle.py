"""Dark theme toggle component for Dash Mantine."""

import dash
import dash_mantine_components as dmc
from dash import Input, Output
from dash_iconify import DashIconify


# region layout
def theme_toggle():
    """Generate the theme toggle component."""
    return dmc.Switch(
        offLabel=DashIconify(
            icon="radix-icons:sun", width=15, color=dmc.DEFAULT_THEME["colors"]["yellow"][8]
        ),
        onLabel=DashIconify(
            icon="radix-icons:moon",
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
    """\
(switchOn) => {
    document.documentElement.setAttribute(
        'data-mantine-color-scheme', switchOn ? 'dark' : 'light');  
    return window.dash_clientside.no_update
}
""",
    Output("color-scheme-toggle", "id"),
    Input("color-scheme-toggle", "checked"),
)
# endregion
