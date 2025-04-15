"""Module for the Daily Arrivals tab of Step 2: Patient Arrival Modelling"""

from copy import deepcopy
from datetime import date, timedelta

import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, Patch, State, callback, clientside_callback, dcc, no_update
from dash_compose import composition
from dash_iconify import DashIconify
from plotly import graph_objects as go
from scipy.optimize import curve_fit
from scipy.stats import norm

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
                value=[date(2022, 12, 1), date(2023, 2, 1)],
                numberOfColumns=2,
                valueFormat="YYYY-MM-DD",
                w=250
            )
            yield dmc.Button(
                'Fit Poisson curve',
                id=ID_POISSON_BUTTON_FIT
            )
            with dmc.Group(gap=0):
                yield DashIconify(icon="material-symbols:warning-rounded", width=24,
                                  color=dmc.DEFAULT_THEME["colors"]["yellow"][5])
                yield dmc.Text(' Note: This will replace the horizontal scale and minimum '
                               'value parameters below.')
    return ret


@composition
def poisson_controls():
    """dmc.Group for creating a patient arrival scenario from a Poisson curve."""
    with dmc.Stack() as ret:
        yield dmc.Text('Scenario parameters', size='xl', fw=700)
        with dmc.Group(gap='md', align='flex-end'):
            yield dmc.DatePickerInput(
                id=ID_POISSON_PEAK_DATE,
                label='Date of peak arrivals',
                numberOfColumns=1,
                valueFormat="YYYY-MM-DD",
                value=date(2025, 1, 1),
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
            yield dmc.NumberInput(
                id=ID_POISSON_MIN,
                label='Minimum value',
                value=0,
                allowNegative=False,
                hideControls=True,
                w=200,
            )
        with dmc.Group(gap='md', align='flex-end'):
            yield dmc.DatePickerInput(
                id=ID_SCENARIO_DATES,
                label='Scenario date range',
                type="range",
                value=[date(2024, 10, 1), date(2025, 2, 28)],
                numberOfColumns=2,
                valueFormat="YYYY-MM-DD",
                w=250
            )
    return ret


# region callbacks
#

# Go back to Step 1: Upload files when stepper button clicked.
clientside_callback(
    """(step, state) => state - 1""",
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_2_TO_1, "n_clicks"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Output(ID_STORE_APPDATA, "data", allow_duplicate=True),
    Input(ID_STEPPER_BTN_2_TO_3, "n_clicks"),
    State(ID_STORE_APPDATA, "data"),
    State(ID_STEPPER, "active"),
    State(ID_SCENARIO_DATES, 'value'),
    State(ID_POISSON_PEAK_DATE, 'value'),
    State(ID_POISSON_XSCALE, 'value'),
    State(ID_POISSON_PEAK, 'value'),
    State(ID_POISSON_MIN, 'value'),
    prevent_initial_call=True
)
def stepper_next(_, data, curr_state, scenario_dates, loc, x_scale, y_max, y_min):
    """Process app data for Step 2 and proceed to Step 3."""

    # Error handling -- this should not trigger, so just return no_update and
    # don't worry about showing error messages
    if not scenario_dates or not loc:
        return no_update, no_update

    try:
        x_scale = float(x_scale)
        y_max = float(y_max)
        y_min = float(y_min)
        if x_scale <= 0:
            return no_update, no_update
    except BaseException:
        return no_update, no_update

    xs = [x.date() for x in pd.date_range(*scenario_dates)]
    ys = [norm_curve2(days(x, date.fromisoformat(loc)), x_scale, y_max, y_min) for x in xs]

    step2_data = {
        'scenario_start': pd.Timestamp(scenario_dates[0]).isoformat(),
        'scenario_end': pd.Timestamp(scenario_dates[1]).isoformat(),
        'peak_date': pd.Timestamp(loc).isoformat(),
        'peak_value': y_max,
        'min_value': y_min,
        'x_scale': x_scale,
        'xs': [x.isoformat() for x in xs],
        'ys': [float(y) for y in ys]
    }

    new_data = deepcopy(data)
    new_data['completed'] = 2
    new_data['step_2'] = step2_data

    return curr_state + 1, new_data


@callback(
    Output(ID_GRAPH_ARR, 'figure', allow_duplicate=True),
    Input(ID_STEPPER, 'active'),
    Input(ID_SCENARIO_DATES, 'value'),
    Input(ID_POISSON_PEAK_DATE, 'value'),
    Input(ID_POISSON_XSCALE, 'value'),
    Input(ID_POISSON_PEAK, 'value'),
    Input(ID_POISSON_MIN, 'value'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True
)
def render_patient_arr_graph(active_step, scenario_dates, loc, x_scale, y_max, y_min,
                             app_data: dict):
    """Render the patient arrivals graph when the current step is loaded,
    or when the Poisson fitting controls have changed input."""
    if active_step != 1:  # Step 2
        return no_update

    if not scenario_dates or not loc:
        return no_update

    try:
        x_scale = float(x_scale)
        y_max = float(y_max)
        y_min = float(y_min)
        if x_scale <= 0:
            return no_update
    except BaseException:
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

    # Scenario curve
    # get date range from start and end dates
    xs = [x.date() for x in pd.date_range(*scenario_dates)]
    ys = [norm_curve2(days(x, date.fromisoformat(loc)), x_scale, y_max, y_min) for x in xs]
    patched_fig['data'].append(go.Scatter(
        x=xs,
        y=ys,
        name='Scenario'
    ))

    return patched_fig


@callback(
    Output(ID_POISSON_XSCALE, 'value'),
    Output(ID_POISSON_MIN, 'value'),
    Input(ID_POISSON_BUTTON_FIT, 'n_clicks'),
    State(ID_POISSON_DATEPICKER, 'value'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True
)
def fit_curve(_, fit_range, app_data):
    """Fit a Poisson curve to the historical patient arrival data, and
    update the horizontal scale and minimum value of the scenario."""

    fit_start = pd.Timestamp(fit_range[0])
    fit_end = pd.Timestamp(fit_range[1])
    arr_df = pd.DataFrame.from_dict(app_data['step_1']['arr_data'], orient='tight')
    arr_df.index = pd.to_datetime(arr_df.index)
    arr_df = arr_df.loc[
        (arr_df.index >= fit_start) & (arr_df.index <= fit_end)
    ]
    if len(arr_df) == 0:
        return no_update, no_update

    xs = (arr_df.index - arr_df.index[0]) / pd.Timedelta(days=1)
    arr_df['xs'] = xs
    arr_df = arr_df.reset_index(drop=False).set_index('xs', drop=True)

    x_max = arr_df['7 day avg.'].idxmax()
    y_max = arr_df['7 day avg.'].max()
    y_min = arr_df['7 day avg.'].min()

    x_scale0 = 10  # Initial guess

    p_opt, _ = curve_fit(norm_curve3, arr_df.index, arr_df.Count, p0=[x_max, x_scale0, y_max])
    p_opt, _ = curve_fit(norm_curve4, arr_df.index, arr_df.Count, p0=[*p_opt, y_min])

    _, x_scale, y_max, y_min = p_opt

    return round(x_scale, 3), round(y_min, 3)


@callback(
    Output(ID_POISSON_DATEPICKER, 'error'),
    Output(ID_POISSON_BUTTON_FIT, 'disabled'),
    Input(ID_POISSON_DATEPICKER, 'value'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True
)
def validate_fit_range(fit_range, app_data):
    """Validate the date range selection for the Poisson fitter, and update the error message
    and button state."""
    fit_start = pd.Timestamp(fit_range[0])
    fit_end = pd.Timestamp(fit_range[1])

    # Fields may be none if user is in the middle of changing the dates
    if pd.isnull(fit_start) or pd.isnull(fit_end):
        return None, True

    arr_df = pd.DataFrame.from_dict(app_data['step_1']['arr_data'], orient='tight')
    arr_df.index = pd.to_datetime(arr_df.index)
    arr_df = arr_df.loc[
        (arr_df.index >= fit_start) & (arr_df.index <= fit_end)
    ]
    if len(arr_df) == 0:
        return 'No data in selected range.', True

    return None, False


@callback(
    Output(ID_POISSON_XSCALE, 'error'),
    Output(ID_STEPPER_BTN_2_TO_3, 'disabled'),
    Input(ID_POISSON_PEAK, 'value'),
    Input(ID_POISSON_XSCALE, 'value'),
    Input(ID_POISSON_MIN, 'value'),
    Input(ID_SCENARIO_DATES, 'value')
)
def validate_inputs(y_max, x_scale, y_min, sc_range):
    """Validate scenario inputs and update error message and 'Next' button status."""
    if y_max is None or y_max == '':
        return None, True

    if x_scale is None or x_scale == '':
        return None, True
    x_scale = float(x_scale)
    if x_scale <= 0:
        return 'Value must be positive', True

    if y_min is None or y_min == '':
        return None, True

    sc_start = pd.Timestamp(sc_range[0])
    sc_end = pd.Timestamp(sc_range[1])
    if pd.isnull(sc_start) or pd.isnull(sc_end):
        return None, True

    return None, False
#
# endregion


# region helper functions
#
def norm_curve(x, x_scale, y_max):
    """Compute a normal curve with horizontal scale `x_scale` and maximum `y_max`."""
    y_scale = y_max / norm.pdf(0, loc=0, scale=x_scale)
    return norm.pdf(x, loc=0, scale=x_scale) * y_scale


def norm_curve2(x, x_scale, y_max, y_min):
    """Same as `norm_curve` but with a y-offset."""
    return norm_curve(x, x_scale, y_max - y_min) + y_min


def norm_curve3(x, loc, x_scale, y_max):
    """Compute a normal curve with mean `loc`, horizontal scale `x_scale`, and maximum `y_max`."""
    y_scale = y_max / norm.pdf(loc, loc=loc, scale=x_scale)
    return norm.pdf(x, loc=loc, scale=x_scale) * y_scale


def norm_curve4(x, loc, x_scale, y_max, y_min):
    """Same as `norm_curve3` but with a y-offset."""
    return norm_curve3(x, loc, x_scale, y_max - y_min) + y_min


def days(x: date, loc: date) -> float:
    """Returns the number of days from `loc`."""
    return (x - loc) / timedelta(days=1)
#
# endregion
