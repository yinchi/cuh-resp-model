"""Module for the Daily Arrivals tab of Step 3: Patient Length-of-Stay Modelling"""

import json
from copy import deepcopy

import dash_mantine_components as dmc
from dash import Input, Output, State, callback, clientside_callback, dcc
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
                with dmc.Stack():
                    with dmc.Group(gap='sm'):
                        yield dmc.Button(id=ID_CONFIG_DOWNLOAD_BTN, children="Download config")
                        yield dcc.Download(id=ID_CONFIG_DOWNLOAD)
                with dmc.Stack(gap='sm'):
                    yield dmc.Text("Simulation Results", size='xl')
                    with dmc.Stack(id=ID_SIM_RESULTS, pos="relative"):
                        yield dmc.LoadingOverlay(
                            id=ID_OVERLAY_SIM_RESULTS,
                            visible=True,
                            overlayProps={"radius": "sm", "blur": 2}
                        )
                        yield dmc.Stack(h=600)
                yield back_next(ID_STEPPER_BTN_4_TO_3, None)
    return ret


# region callbacks
#

# Go back to Step 3: LoS modelling.
clientside_callback(
    """(step, state) => state - 1""",
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_4_TO_3, "n_clicks"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)


@callback(
    Output(ID_CONFIG_DOWNLOAD, 'data'),
    Input(ID_CONFIG_DOWNLOAD_BTN, 'n_clicks'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True
)
def download_config(_, data):
    """Send the simulation config when the Download button is pressed."""
    ret = deepcopy(data)
    del ret['step_1']['los_data']  # not needed to run simulation or plot results
    return dcc.send_string(
        json.dumps(ret, sort_keys=False),
        filename='config.json'
    )
#
# endregion
