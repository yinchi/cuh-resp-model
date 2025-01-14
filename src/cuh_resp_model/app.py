"""The dash app."""

import html
from datetime import date

import dash
import dash_mantine_components as dmc
from dash import Dash, _dash_renderer
from dash_compose import composition
from dash_iconify import DashIconify

from .components.theme_toggle import theme_toggle

_dash_renderer._set_react_version("18.2.0")  # pylint: disable=protected-access

app = Dash(external_stylesheets=dmc.styles.ALL)


COPY = html.unescape("&copy;")
NDASH = html.unescape("&ndash;")
NBSP = html.unescape("&nbsp;")


def copyright():  # pylint: disable=redefined-builtin
    """Generate the copyright string."""
    year = date.today().year
    return (
        f"{COPY} 2025{f"{NDASH}{year}" if year > 2025 else ""} "
        "Yin-Chi Chan, Institute for Manufacturing, "
        "University of Cambridge"
    )


@composition
def layout():
    """App layout using Dash Compose."""
    with dmc.MantineProvider() as ret:
        with dmc.AppShell(
            None,
            header={"height": "80"},
            padding="md",
        ):
            with dmc.AppShellHeader(None):
                with dmc.Group(
                    justify="space-between",
                    style={"flex": 1},
                    h="100%",
                    px="md",
                ):
                    with dmc.Group():
                        yield dmc.Image(src=dash.get_asset_url('logo-cuh.png'), h=80)
                        yield dmc.Title('CUH respiratory viruses modelling webapp')
                    yield theme_toggle()
            with dmc.AppShellMain(None):
                with dmc.Stack(px="sm"):
                    yield "Main"
            with dmc.AppShellFooter(None):
                with dmc.Group(
                    justify="space-between",
                    style={"flex": 1},
                    h="100%",
                    px="sm",
                    pt="10",
                    pb="5"
                ):
                    with dmc.Text():
                        yield copyright()
                    with dmc.Anchor(
                        href="http://github.com/yinchi/cuh-resp-model"
                    ):
                        yield DashIconify(icon="ion:logo-github", height=16)
                        yield f"{NBSP}Github"
    return ret


app.layout = layout()
