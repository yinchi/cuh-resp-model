"""Module for the Daily Arrivals tab of Step 2: Patient Arrival Modelling"""

from datetime import date
from typing import Sequence

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, Patch, State, callback, dcc, no_update
from dash_compose import composition
from plotly import graph_objects as go

from cuh_resp_model.components.ids import *

from ..components.back_next import back_next


@composition
def stepper_step():
    """The contents for the Stepper Step 2 in the app."""
    with dmc.StepperStep(
        None,
        label="Arrival Modelling",
        description=dmc.Text(
            "Generate patient arrival scenario", size="xs")
    ) as ret:
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 2: Patient Arrival Modelling", ta="center", size="xl")
                yield arr()
                yield poisson_fitter()
                yield poisson_controls()
                yield back_next(ID_STEPPER_BTN_2_TO_1, ID_STEPPER_BTN_2_TO_3)
    return ret


@composition
def arr():
    """Contents of the dmc.Tab."""
    with dmc.Stack(px="sm", pt="xl", gap="xl") as ret:
        yield dcc.Graph(
            id=ID_GRAPH_ARR,
            figure=go.Figure(
                layout={
                    'width': 1000,
                    'height': 350,
                    'title': '{name} cases by first positive test',
                    'legend': {'y': 0.5, 'font_size': 12},
                    'legend_y': 0.5,
                    'legend_font_size': 14,
                    'title_font_size': 20,
                    'xaxis': {'tickfont': {'size': 14}},
                    'yaxis': {'tickfont': {'size': 14}},
                    'title_font_weight': 900,
                    'hovermode': 'x unified'
                }
            ),
            # config={'displayModeBar': False}
        )
    return ret


@composition
def poisson_fitter():
    """dmc.Group for fitting a Poisson curve to the arrival data."""
    with dmc.Stack() as ret:
        yield dmc.Text('Fit Poisson curve to time period', fw=700)
        with dmc.Group(gap='md', align='flex-end'):
            yield dmc.DatePickerInput(
                id=ID_POISSON_DATEPICKER,
                label='Date Range to Fit',
                type="range",
                value=[date(2023, 12, 1), date(2024, 2, 1)],
                numberOfColumns=2,
                valueFormat="YYYY-MM-DD",
                w=250
            )
            yield dmc.Button(
                'Fit Poisson curve',
                id=ID_POISSON_BUTTON_FIT
            )
    return ret


@composition
def poisson_controls():
    """dmc.Group for creating a patient arrival scenario from a Poisson curve."""
    with dmc.Stack() as ret:
        yield dmc.Text('Scenario parmeters', fw=700)
        with dmc.Group(gap='md', align='flex-end'):
            yield dmc.DatePickerInput(
                id=ID_POISSON_PEAK_DATE,
                label='Date of peak arrivals',
                numberOfColumns=1,
                valueFormat="YYYY-MM-DD",
                value=date(2024, 1, 1),
                w=200
            )
            yield dmc.NumberInput(
                id=ID_POISSON_PEAK,
                label='Peak daily arrivals',
                value=20,
                allowNegative=False,
                hideControls=True,
                w=200,
            )
            yield dmc.NumberInput(
                id=ID_POISSON_XSCALE,
                label='Horizontal scale parameter',
                value=3,
                allowNegative=False,
                hideControls=True,
                w=200,
            )
    return ret

# region callbacks
#


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_2_TO_1, "n_clicks"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)
def stepper_back(_, curr_state):
    """Go back to Step 1: Upload files.

    This will clear all progress in Step 2 (deferred until user clicks Next in Step 1)."""
    return curr_state-1


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Output(ID_STORE_APPDATA, "data", allow_duplicate=True),
    Input(ID_STEPPER_BTN_2_TO_3, "n_clicks"),
    State(ID_STORE_APPDATA, "data"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)
def stepper_next(_, data, curr_state):
    """Process app data for Step 2 and proceed to Step 3."""
    return curr_state+1, dash.no_update


@callback(
    Output(ID_GRAPH_ARR, 'figure', allow_duplicate=True),
    Input(ID_STEPPER, 'active'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True
)
def render_patient_arr_graph(active_step, app_data):
    """Render the patient arrivals graph when the current step is loaded."""
    if active_step != 1:  # Step 2
        return no_update

    disease_name = app_data['step_1']['disease_name']
    arr_df = pd.DataFrame.from_dict(app_data['step_1']['arr_data'], orient='tight')

    patched_fig = Patch()

    patched_fig['layout']['title']['text'] = f'{disease_name} cases by first positive test'
    patched_fig['data'] = []

    patched_fig['data'].append(go.Scatter(
        x=arr_df.index,
        y=arr_df['Count'],
        name='Count',
        line={'width': 0.5}
    ))
    patched_fig['data'].append(go.Scatter(
        x=arr_df.index,
        y=arr_df['7 day avg.'],
        name='7-day rolling avg.'
    ))

    return patched_fig


@callback(
    Output(ID_POISSON_BUTTON_FIT, 'disabled'),
    Input(ID_POISSON_DATEPICKER, 'value')
)
def update_fitter_btn_state(dates):
    '''Enable the button to fit a Poisson curve to arrivals, only if the date range picker
    has a valid value.'''
    valid_dates_range = (isinstance(dates, Sequence)) and (None not in dates)
    return not valid_dates_range
#
# endregion
