"""Module for the Daily Arrivals tab of Step 3: Patient Length-of-Stay Modelling"""

import dash_mantine_components as dmc
from dash import Input, Output, State, callback
from dash_compose import composition

from cuh_resp_model.components.ids import *

from ..components.back_next import back_next


@composition
def stepper_step():
    """The contents for the Stepper Step 4 in the app."""
    with dmc.StepperStep(
        None,
        label="Simulate!"
    ) as ret:
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 4: Simulate disease scenario", ta="center", size="xl")
                yield back_next(ID_STEPPER_BTN_4_TO_3, None)
    return ret


# region callbacks
#
@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_4_TO_3, "n_clicks"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)
def stepper_back(_, curr_state):
    """Go back to Step 3: Patient Length-of-Stay Modelling.

    This will clear all progress in Step 4 (deferred until user clicks Next in Step 3)."""
    return curr_state - 1
#
# endregion
