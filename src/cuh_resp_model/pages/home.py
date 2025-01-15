"""Main page for the dash app."""

import dash
import dash_mantine_components as dmc
from dash_compose import composition

dash.register_page(__name__, path='/')

@composition
def layout():
    """App layout using Dash Compose."""
    with dmc.Stack(px="sm") as ret:
        with dmc.Title(order=2):
            yield "Main page"
    return ret
