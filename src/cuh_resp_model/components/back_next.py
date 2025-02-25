"""Back/next button control."""

from html import unescape

import dash_mantine_components as dmc
from dash import html
from dash_compose import composition

from cuh_resp_model.utils import drop_none

LEFT = unescape("&larr;")
RIGHT = unescape("&rarr;")


@composition
def back_next(_back: str | None, _next: str | None):
    """Back and Next buttons, in a dmc.Stack."""
    with dmc.Stack(gap=0) as ret:
        yield html.Hr(style={"width": "100%",
                             "border-color": "var(--mantine-color-dimmed)"})
        with dmc.Group(
            justify="space-between",
            style={"flex": 1}
        ):
            with dmc.Button(
                **drop_none({
                    "style": {"visibility": "hidden"} if not _back else None,
                    "id": _back if _back else None
                })
            ):
                yield f"{LEFT} Back"
            with dmc.Button(
                **drop_none({
                    "style": {"visibility": "hidden"} if not _next else None,
                    "id": _next if _next else None
                })
            ):
                yield f"Next {RIGHT}"
    return ret
