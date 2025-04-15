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

app = Dash(external_stylesheets=dmc.styles.ALL, use_pages=True)

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
            header={"height": "90"},
            padding="md",
            miw=1200
        ):
            with dmc.AppShellHeader(None, miw=1200):
                with dmc.Group(
                    justify="space-between",
                    style={"flex": 1},
                    h="100%",
                    px="md",
                ):
                    with dmc.Group():
                        yield dmc.Image(src=dash.get_asset_url("logo-cuh.png"), h=80)
                        yield dmc.Title("CUH respiratory viruses modelling webapp")
                    with dmc.Group(gap=0, align="flex-end"):
                        # HACK: align with title text on left-side header group
                        yield dmc.Title(".", opacity=0)
                        with dmc.Group(gap="xl"):
                            with dmc.Anchor(None, href="/", refresh=True, underline="never",
                                            style={"color": "var(--mantine-color-text)"}):
                                with dmc.Center():
                                    yield DashIconify(
                                        icon="material-symbols:home-rounded", height=20)
                                    yield dmc.Text(f"{NBSP}{NBSP}Home", fw=700)
                            with dmc.Anchor(None, href="/about", underline="never",
                                            style={"color": "var(--mantine-color-text)"}):
                                with dmc.Center():
                                    yield DashIconify(
                                        icon="material-symbols:help-outline", height=20)
                                    yield dmc.Text(f"{NBSP}{NBSP}About", fw=700)
                            yield theme_toggle()
            with dmc.AppShellMain(None, w=1200):
                yield dash.page_container
            with dmc.AppShellFooter(None, miw=1200):
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
                        href="http://github.com/yinchi/cuh-resp-model",
                        target="_blank"
                    ):
                        yield DashIconify(icon="ion:logo-github", height=16)
                        yield f"{NBSP}Github"
    return ret


app.layout = layout()
