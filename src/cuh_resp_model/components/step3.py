"""Module for the Daily Arrivals tab of Step 3: Patient Length-of-Stay Modelling"""

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, callback
from dash_compose import composition

from cuh_resp_model.components.ids import *

from ..components.back_next import back_next


@composition
def stepper_step():
    """The contents for the Stepper Step 3 in the app."""
    with dmc.StepperStep(
        None,
        label="LoS Modelling",
        description=dmc.Text(
            "Fit patient length-of-stay distributions", size="xs")
    ) as ret:
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 3: Patient Length-of-Stay Modelling", ta="center", size="xl")
                with dmc.Card(withBorder=True):
                    yield dmc.Text('0-15 Age group', size='xl', fw=700)
                with dmc.Card(withBorder=True):
                    yield dmc.Text('16-64 Age group', size='xl', fw=700)
                with dmc.Card(withBorder=True):
                    yield dmc.Text('65+ Age group', size='xl', fw=700)
                yield back_next(ID_STEPPER_BTN_3_TO_2, ID_STEPPER_BTN_3_TO_4)
    return ret


# region callbacks
#
@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_3_TO_2, "n_clicks"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)
def stepper_back(_, curr_state):
    """Go back to Step 2: Patient Arrival Modelling.

    This will clear all progress in Step 3 (deferred until user clicks Next in Step 2)."""
    return curr_state - 1


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Output(ID_STORE_APPDATA, "data", allow_duplicate=True),
    Input(ID_STEPPER_BTN_3_TO_4, "n_clicks"),
    State(ID_STORE_APPDATA, "data"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)
def stepper_next(_, data, curr_state):
    """Process app data for Step 2 and proceed to Step 3."""
    return curr_state + 1, dash.no_update
#
# endregion
