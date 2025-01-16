"""Main page for the dash app."""

from html import unescape

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback, dcc, html
from dash_compose import composition

from cuh_resp_model.utils import drop_none

dash.register_page(__name__, path="/")

NUM_STEPS = 3

LEFT = unescape("&larr;")
RIGHT = unescape("&rarr;")


# region layout
ID_STEPPER = "stepper"
ID_STEPPER_BTN_0_TO_1 = "stepper-btn-0-to-1"
ID_STEPPER_BTN_1_TO_2 = "stepper-btn-1-to-2"
ID_STEPPER_BTN_2_TO_1 = "stepper-btn-2-to-1"
ID_STEPPER_BTN_1_TO_0 = "stepper-btn-1-to-0"

ID_STORE_APPDATA = "store-appdata"


@composition
def back_next(back: str | None, next: str | None):
    """Back and Next buttons for the Stepper, in a dmc.Stack."""
    with dmc.Stack(gap=0) as ret:
        yield html.Hr(style={"width": "100%",
                             "border-color": "var(--mantine-color-dimmed)"})
        with dmc.Group(
            justify="space-between",
            style={"flex": 1}
        ):
            with dmc.Button(
                **drop_none({
                    "style": {"visibility": "hidden"} if not back else None,
                    "id": back if back else None
                })
            ):
                yield f"{LEFT} Back"
            with dmc.Button(
                **drop_none({
                    "style": {"visibility": "hidden"} if not next else None,
                    "id": next if next else None
                })
            ):
                yield f"Next {RIGHT}"
    return ret


@composition
def layout():
    """App layout using Dash Compose."""
    with dmc.Stack(px="sm") as ret:
        with dmc.Stepper(
            None, id=ID_STEPPER, active=0,
            allowNextStepsSelect=False
        ):
            with dmc.StepperStep(
                None,
                label="Upload files",
                description=dmc.Text(
                    "Upload patient stay & occupancy records", size="xs")
            ):
                with dmc.Card():
                    with dmc.Stack(gap="xl"):
                        yield dmc.Text("Step 1: Upload Files", ta="center", size="xl")
                        yield back_next(None, ID_STEPPER_BTN_0_TO_1)
            with dmc.StepperStep(
                None,
                label="Analysis",
                description=dmc.Text(
                    "Generate patient arrival and length-of-stay models", size="xs")
            ):
                with dmc.Card():
                    with dmc.Stack(gap="xl"):
                        yield dmc.Text("Step 2: Analysis & Model Creation", ta="center", size="xl")
                        with dmc.Tabs(None, value="arrivals"):
                            with dmc.TabsList(None):
                                yield dmc.TabsTab("Daily arrivals", value="arrivals")
                                yield dmc.TabsTab("Length-of-stay", value="los")
                            with dmc.TabsPanel(None, value="arrivals"):
                                yield "Daily arrivals"
                            with dmc.TabsPanel(None, value="los"):
                                yield "Length-of-stay"
                        yield back_next(ID_STEPPER_BTN_1_TO_0, ID_STEPPER_BTN_1_TO_2)
            with dmc.StepperStep(
                None,
                label="Simulate!",
                description=dmc.Text(
                    "Generate bed occupancy forecast", size="xs")
            ):
                with dmc.Card():
                    with dmc.Stack(gap="xl"):
                        yield dmc.Text("Step 3: Simulation", ta="center", size="xl")
                        yield back_next(ID_STEPPER_BTN_2_TO_1, None)
        yield dcc.Store(
            id=ID_STORE_APPDATA
        )
    return ret
# endregion


# region callbacks
@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_1_TO_0, "n_clicks"),
    prevent_initial_call=True
)
def stepper_back_0(_):
    """Go back to Step 1: Upload files."""
    return 0


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_2_TO_1, "n_clicks"),
    prevent_initial_call=True,
)
def stepper_back_1(_):
    """Go back to Step 2: Analysis & Model Creation."""
    return 1


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Output(ID_STORE_APPDATA, "data", allow_duplicate=True),
    Input(ID_STEPPER_BTN_0_TO_1, "n_clicks"),
    State(ID_STORE_APPDATA, "data"),
    prevent_initial_call=True
)
def stepper_next_1(_, data):
    """Process app data for Step 1 (0 internally) and proceed to Step 2 (1 internally)."""
    return 1, dash.no_update


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Output(ID_STORE_APPDATA, "data", allow_duplicate=True),
    Input(ID_STEPPER_BTN_1_TO_2, "n_clicks"),
    State(ID_STORE_APPDATA, "data"),
    prevent_initial_call=True
)
def stepper_next_2(_, data):
    """Process app data for Step 2 (1 internally) and proceed to Step 3 (2 internally)."""
    return 2, dash.no_update
# endregion
