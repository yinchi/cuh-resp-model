"""Main page for the dash app."""

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback, dcc
from dash_compose import composition

from cuh_resp_model.components.ids import (
    ID_STEPPER,
    ID_STEPPER_BTN_1_TO_2,
    ID_STEPPER_BTN_2_TO_1,
    ID_STEPPER_BTN_1_TO_0,

    ID_STORE_APPDATA
)
from cuh_resp_model.components import step1
from cuh_resp_model.components.back_next import back_next

dash.register_page(__name__, path="/")

NUM_STEPS = 3


# region layout
@composition
def layout():
    """App layout using Dash Compose."""
    with dmc.Stack(px="sm") as ret:
        with dmc.Stepper(
            None, id=ID_STEPPER, active=0,
            allowNextStepsSelect=False
        ):
            yield step1.step()
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
    Input(ID_STEPPER_BTN_1_TO_2, "n_clicks"),
    State(ID_STORE_APPDATA, "data"),
    prevent_initial_call=True
)
def stepper_next_2(_, data):
    """Process app data for Step 2 (1 internally) and proceed to Step 3 (2 internally)."""
    return 2, dash.no_update
# endregion
