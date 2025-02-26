"""Main page for the dash app."""

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash_compose import composition

from cuh_resp_model.components import step1, step2, step3, step4
from cuh_resp_model.components.ids import *

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
            yield step1.stepper_step()
            yield step2.stepper_step()
            yield step3.stepper_step()
            yield step4.stepper_step()
        yield dcc.Store(
            id=ID_STORE_APPDATA
        )
    return ret
# endregion
