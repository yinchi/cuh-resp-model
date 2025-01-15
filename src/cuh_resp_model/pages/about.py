"""Main page for the dash app."""

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash_compose import composition

dash.register_page(__name__, path='/about')

@composition
def layout():
    """App layout using Dash Compose."""
    with dmc.Stack(gap=0, px="sm") as ret:
        with dmc.Title(order=2):
            yield "About"
        with dcc.Markdown():
            yield """\
**Author**: Yin-Chi Chan, Institute for Manufacturing, University of Cambridge
- Email: <yinchi.chan@nhs.net>

This webapp is was developed for modelling bed requirements at Addenbrooke's Hospital, Cambridge
caused by respiratory viruses. It is best viewed on desktop with a horizontal resolution of at least
1200 pixels (mobile not supported).

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse
cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
culpa qui officia deserunt mollit anim id est laborum.
"""
    return ret
