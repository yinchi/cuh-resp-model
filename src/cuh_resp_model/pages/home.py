"""Main page for the dash app."""

import dash
import dash_mantine_components as dmc
from dash import dcc
from dash_compose import composition

from cuh_resp_model.components import step1, step2

dash.register_page(__name__, path="/")

# region layout


@composition
def layout():
    """App layout using Dash Compose."""
    with dmc.Stack(px="sm") as ret:
        with dmc.Stepper(
            None, id='stepper', active=0,
            allowNextStepsSelect=False
        ):
            yield step1.stepper_step()
            yield step2.stepper_step()
        yield dcc.Store(id='store-appdata', data={})
        with dmc.Modal(title='Error', id='modal-validation-error', opened=False,
                       styles={
                           'title': {
                               'font-size': '1.2rem',
                               'font-weight': 'bold',
                               'color': 'red'
                           }
                       }):
            yield dmc.Text('Error text to go here.', id='text-validation-error')
    return ret
# endregion
