"""Main module for Step 2 of the stepper: Scenario modelling."""

import json
from typing import Any, Literal

import dash
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
from dash import Input, Output, Patch, State, callback, dcc
from dash_compose import composition
from plotly import graph_objects as go
from scipy.optimize import curve_fit
from scipy.stats import beta

from cuh_resp_model.components.back_next import back_next

ID_GRAPH = {'themed_graph': True, 'name': 'step2-graph-arrivals'}


# region layout
@composition
def stepper_step():
    """The contents for Step 2 in the app."""

    with dmc.StepperStep(
        None,
        label="Scenario modelling",
        description=dmc.Text(
            "Fit distribution for daily arrivals", size="xs")
    ) as ret:
        yield dcc.Store(id='step2-store', data={})
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 2: Scenario modelling", ta="center", size="xl")
                yield stack()
                yield back_next('btn-stepper-2-to-1', 'btn-stepper-2-to-3')
    return ret


@composition
def stack():
    """The DMC stack for Step 2."""

    with dmc.Stack(gap=36) as ret:
        with dmc.Stack(gap=10):
            yield dmc.Text('Start time options:', fw=700, size='lg')
            yield dmc.Text(
                'For hospital-acquired infections, use the following timestamp as the starting '
                'time:'
            )
            yield dmc.Select(
                id='step2-select-starttime-option',
                data=[
                    {'label': 'Admission',
                     'value': 'Admission'},
                    {'label': 'First positive test collected (FirstPosCollected)',
                     'value': 'FirstPosCollected'}
                ],
                value='FirstPosCollected',
                w=400
            )

        with dmc.Stack(gap=0):
            yield dmc.Text('Daily patient arrivals:', fw=700, size='lg')
            yield dcc.Graph(
                id=ID_GRAPH,
                figure=go.Figure(
                    layout={
                        'width': 1000,
                        'height': 350,
                        'legend': {'yanchor': 'bottom', 'y': 1,
                                   'xanchor': 'left', 'x': 0,
                                   'font_size': 14, 'orientation': 'h'},
                        'title_font_size': 20,
                        'xaxis': {'tickfont': {'size': 14}},
                        'yaxis': {'tickfont': {'size': 14}},
                        'title_font_weight': 900,
                        'hovermode': 'x unified'
                    }
                ),
                # config={'displayModeBar': False}
            )

        with dmc.Stack(gap=10):
            yield dmc.Text('Scenario parameters:', fw=700, size='lg')
            with dmc.Group(align='start'):
                with dmc.Stack():
                    with dmc.Group(align='start'):
                        # Parameters for a scaled and shifted beta distribution.
                        # Note date values are in ISO format even though the display format is
                        # different.
                        yield dmc.DateInput(id='step2-dateinput-scenario-start',
                                            label='Start date (DD-MM-YYYY)',
                                            valueFormat='DD-MM-YYYY',
                                            value='2024-07-01',
                                            w=200)
                        yield dmc.DateInput(id='step2-dateinput-scenario-end',
                                            label='End date (DD-MM-YYYY)',
                                            valueFormat='DD-MM-YYYY',
                                            value='2025-01-01',
                                            w=200)
                        yield dmc.DateInput(id='step2-dateinput-scenario-mode',
                                            label='Peak date (DD-MM-YYYY)',
                                            valueFormat='DD-MM-YYYY',
                                            value='2024-09-01',
                                            w=200)
                    with dmc.Group(align='baseline'):
                        yield dmc.NumberInput(id='step2-numinput-scenario-shape',
                                              label='Shape parameter (min: 0.1)',
                                              value=10.0, min=0.1, decimalScale=1, step=0.1,
                                              w=200)
                        yield dmc.NumberInput(id='step2-numinput-scenario-ymin',
                                              label='Minimum value (min: 0)',
                                              value=0.0, min=0, decimalScale=2,
                                              w=200)
                        yield dmc.NumberInput(id='step2-numinput-scenario-ymax',
                                              label='Maximum value',
                                              value=15.0, min=0, decimalScale=2,
                                              w=200)
                yield dmc.Text('⚠️ Error message goes here.',
                               id='step2-text-params-error',
                               display=None, mt='1.9rem', w=400, c='red')

        with dmc.Stack(gap=0):
            yield dmc.Text('Fit parameters:', fw=700, size='lg')
            yield dcc.Markdown('''\
Clicking the "Fit parameters" button below will replace all the parameters above
except for the scenario start date:

- The end date will be adjusted so that the fitted curve and the scenario curve have the same
  length (in days).
- The peak date will be set based to have the same distance from the start and end dates in both the
  fitted and scenario curves.
- The shape parameter and min/max values will be set to those of the fitted curve.
''')
            yield dmc.Alert(
                'Errors go here.',
                id='step2-alert-fitter',
                color='red',
                hide=True,
                withCloseButton=True,
                title=dmc.Text('Error!', size='lg'),
                mb=10
            )
            with dmc.Group(align='start'):
                # Parameters for a scaled and shifted beta distribution.
                # Note date values are in ISO format even though the display format is
                # different.
                yield dmc.DateInput(id='step2-dateinput-fitter-start',
                                    label='Start date (DD-MM-YYYY)',
                                    valueFormat='DD-MM-YYYY',
                                    value='2022-05-18',
                                    w=200)
                yield dmc.DateInput(id='step2-dateinput-fitter-end',
                                    label='End date (DD-MM-YYYY)',
                                    valueFormat='DD-MM-YYYY',
                                    value='2022-09-03',
                                    w=200)
                yield dmc.Button('Fit parameters',
                                 id='step2-button-fitter',
                                 mt='1.6rem')
                yield dcc.Store(id='step2-store-fitter-results',
                                data=None)
    return ret
# endregion


# region callbacks
@callback(
    Output(ID_GRAPH, 'figure', allow_duplicate=True),
    Output('step2-text-params-error', 'children'),
    Output('step2-text-params-error', 'display'),
    Input('stepper', 'active'),  # current step
    Input('step2-select-starttime-option', 'value'),  # Admission or FirstPosCollected
    Input('step2-dateinput-scenario-start', 'value'),
    Input('step2-dateinput-scenario-end', 'value'),
    Input('step2-dateinput-scenario-mode', 'value'),
    Input('step2-numinput-scenario-shape', 'value'),
    Input('step2-numinput-scenario-ymin', 'value'),
    Input('step2-numinput-scenario-ymax', 'value'),
    Input('step2-store-fitter-results', 'data'),
    State('store-appdata', 'data'),
    prevent_initial_call=True
)
def render_scenario_graph(
    active_step: int,
    start_date_option: Literal['Admission', 'FirstPosCollected'],
    scenario_start: pd.Timestamp,
    scenario_end: pd.Timestamp,
    scenario_mode: pd.Timestamp,
    scenario_shape: float,
    scenario_ymin: float,
    scenario_ymax: float,
    fitter_results: dict[str, Any] | None,
    app_data: dict[str, Any]
):
    """Re-plot the daily arrivals graph.  Triggered when:

    - Stepper enters Step 2
    - Start date option (admission / first positive collected) changed
    - Scenario controls changed
    - A new fitter result is pushed to the Store.
    """
    if active_step != 1:
        raise dash.exceptions.PreventUpdate

    disease_name: str = app_data['step1']['disease_name']

    patched_fig = Patch()
    patched_fig['layout']['title']['text'] = f'{disease_name} cases by start date'
    patched_fig['data'] = []  # reset plots

    # Extract start dates of patients
    stays_df = pd.DataFrame.from_dict(app_data['step1']['stays_df'], orient='tight')
    start_date_df = start_dates(stays_df, option=start_date_option)

    # Daily arrivals
    patched_fig['data'].append(
        go.Scatter(
            x=start_date_df.index,
            y=start_date_df.num_cases,
            name='Count',
            line={'width': 0.5}
        )
    )

    # 7-day rolling average
    patched_fig['data'].append(
        go.Scatter(
            x=start_date_df.index,
            y=start_date_df.rolling_avg,
            name='7-day rolling average',
            # Show a short name and only 4 decimal places for the rolling average
            hovertemplate='7-day avg.: %{y:.4f}<extra></extra>',
            line={'width': 1}
        )
    )

    # If we have fitter results, plot the fitted curve
    if fitter_results is not None:
        fit_df = beta_dist_df(
            x_min=fitter_results['start_date'],
            x_max=fitter_results['end_date'],
            x_mode=fitter_results['mode_date'],
            conc=fitter_results['shape'],
            y_min=fitter_results['y_min'],
            y_max=fitter_results['y_max']
        )
        patched_fig['data'].append(
            go.Scatter(
                x=fit_df.date,
                y=fit_df.y,
                name='Fitted curve',
                # Show a short name and only 4 decimal places for the rolling average
                hovertemplate='Fitted: %{y:.4f}<extra></extra>',
                line={'width': 2}
            )
        )

    # Skip plotting scenario curve if any input is of unexpected type, such as empty string
    # (i.e. user cleared the input box).  Note the conditions checked here are for input boxes in
    # invalid states; a second logic check in `beta_dist` is used for bad user input.
    try:
        scenario_start_ts = pd.to_datetime(scenario_start)
        scenario_end_ts = pd.to_datetime(scenario_end)
        scenario_mode_ts = pd.to_datetime(scenario_mode)
        scenario_shape = float(scenario_shape)
        scenario_ymin = float(scenario_ymin)
        scenario_ymax = float(scenario_ymax)
        assert (
            pd.notna(scenario_start_ts)
            and pd.notna(scenario_end_ts)
            and pd.notna(scenario_mode_ts)
            and scenario_shape > 0
            and scenario_ymin >= 0
            and scenario_ymax >= 0
        )
    except Exception as e:
        raise dash.exceptions.PreventUpdate from e

    # Create and plot scenario curve
    try:
        scenario_df = beta_dist_df(
            x_min=scenario_start, x_max=scenario_end, x_mode=scenario_mode,
            conc=scenario_shape, y_min=scenario_ymin, y_max=scenario_ymax
        )
        patched_fig['data'].append(
            go.Scatter(
                x=scenario_df.date,
                y=scenario_df.y,
                name='Scenario',
                # Show a short name and only 4 decimal places for the rolling average
                hovertemplate='Scenario: %{y:.4f}<extra></extra>',
                line={'width': 2}
            )
        )
        error_message = ''
    except AssertionError as e:
        patched_fig = dash.no_update  # Don't update the plots
        error_message = f"⚠️ {str(e)}"

    error_display = 'none' if error_message == '' else None
    return patched_fig, error_message, error_display


@callback(
    Output('step2-store-fitter-results', 'data'),
    Output('step2-alert-fitter', 'title'),
    Output('step2-alert-fitter', 'children'),
    Output('step2-alert-fitter', 'color'),
    Output('step2-alert-fitter', 'hide'),
    Output('step2-dateinput-scenario-end', 'value'),
    Output('step2-dateinput-scenario-mode', 'value'),
    Output('step2-numinput-scenario-shape', 'value'),
    Output('step2-numinput-scenario-ymin', 'value'),
    Output('step2-numinput-scenario-ymax', 'value'),
    Input('step2-button-fitter', 'n_clicks'),
    State('step2-dateinput-fitter-start', 'value'),
    State('step2-dateinput-fitter-end', 'value'),
    State('step2-select-starttime-option', 'value'),  # Admission or FirstPosCollected
    State('step2-dateinput-scenario-start', 'value'),  # Used to compute new scenario end
    State('store-appdata', 'data'),
    prevent_initial_call=True
)
def fit_arrivals(
    _,
    start: pd.Timestamp,
    end: pd.Timestamp,
    start_date_option: Literal['Admission', 'FirstPosCollected'],
    scenario_start: pd.Timestamp,
    app_data: dict[str, Any]
):
    """Fit a shifted and scaled beta curve to the patient arrival data.
    Also overwrites some of the scenario inputs to match that of the fitted curve.

    Triggered on button press ("Fit parameters" button).  Shows an alert (sets hide=False)
    with a success or error message.
    """

    # Check invalid input field states
    try:
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)
        scenario_start = pd.Timestamp(scenario_start)
        assert pd.notna(start) and pd.notna(end) and pd.notna(scenario_start)
    except Exception as e:
        raise dash.exceptions.PreventUpdate from e

    new_scenario_end = scenario_start + (end - start)

    try:
        # Check input value logic
        assert start < end, "Start date must be before end date."

        # Extract start dates of patients
        stays_df = pd.DataFrame.from_dict(app_data['step1']['stays_df'], orient='tight')
        start_date_df = start_dates(stays_df, option=start_date_option)
        start_date_df = start_date_df.loc[
            (start_date_df.index >= start) & (start_date_df.index <= end), ['num_cases']]

        assert not start_date_df.empty, "No patient stay data in selected period."
        assert len(start_date_df) >= 5, "Too little patient stay data in selected period."

        p_opt: tuple[float] = fit_beta(start_date_df)
        x_mode, shape, y_min, y_max = p_opt

        assert 0 < x_mode < 1, "Bad fit result: peak should be between the start and end dates."
        assert shape > 0, "Bad fit result: shape should be positive."
        assert y_max > y_min, "Bad fit result: maximum value should be larger than minimum value."

        mode_days = (end - start) / pd.Timedelta(days=1) * x_mode
        mode_timestamp = start + pd.Timedelta(days=mode_days)
        mode_date = mode_timestamp.round('d')
        ret = {
            'start_date': start,
            'end_date': end,
            'mode': x_mode,
            'mode_days': mode_days,
            'mode_date': mode_date,
            'shape': round(shape, 1),
            'y_min': round(y_min, 2),
            'y_max': round(y_max, 2)
        }
        scenario_mode_date = (scenario_start + pd.Timedelta(days=mode_days)).round('d')

        return ret, 'Success!', \
            [
                'New fit parameters computed. To dismiss this alert, lick the X in the top right '
                'corner.',
                dmc.Space(h=10),
                f'Peak: {ret["mode_date"].date()}, shape: {ret["shape"]}, '
                f'min: {ret["y_min"]}, max: {ret["y_max"]}',
            ], 'green', False, \
            new_scenario_end, scenario_mode_date, ret['shape'], ret['y_min'], ret['y_max']

    except AssertionError as e:
        return dash.no_update, 'Error!', str(e), 'red', False, \
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@callback(
    Output('stepper', 'active', allow_duplicate=True),
    Input('btn-stepper-2-to-1', 'n_clicks'),
    State('stepper', 'active'),
    prevent_initial_call=True
)
def stepper_back(_, current_step: int):
    """Go back to the previous step."""
    return current_step - 1  # 1-based to 0-based numbering


@callback(
    Output('stepper', 'active', allow_duplicate=True),
    Output('store-appdata', 'data', allow_duplicate=True),
    Output('modal-validation-error', 'opened', allow_duplicate=True),
    Output('text-validation-error', 'children', allow_duplicate=True),
    Input('btn-stepper-2-to-3', 'n_clicks'),
    State('stepper', 'active'),
    State('step2-dateinput-scenario-start', 'value'),
    State('step2-dateinput-scenario-end', 'value'),
    State('step2-dateinput-scenario-mode', 'value'),
    State('step2-numinput-scenario-shape', 'value'),
    State('step2-numinput-scenario-ymin', 'value'),
    State('step2-numinput-scenario-ymax', 'value'),
    State('step2-select-starttime-option', 'value'),  # Admission or FirstPosCollected
    State('store-appdata', 'data'),
    prevent_initial_call=True
)
def stepper_next(_, current_step: int,
                 scenario_start: str, scenario_end: str, scenario_mode: str, scenario_shape: float,
                 scenario_ymin: float, scenario_ymax: float,
                 starttime_option: Literal['Admission', 'FirstPosCollected'],
                 app_data: dict[str, Any]):
    """Validate inputs and go to the next step."""

    try:
        sc_params = {
            'start': scenario_start,
            'end': scenario_end,
            'mode': scenario_mode,
            'shape': scenario_shape,
            'y_min': scenario_ymin,
            'y_max': scenario_ymax,
        }
        scenario_df = beta_dist_df(
            x_min=scenario_start, x_max=scenario_end, x_mode=scenario_mode,
            conc=scenario_shape, y_min=scenario_ymin, y_max=scenario_ymax
        )
        # Convert all pd.Timestamp columns in scenario_df to ISO format (str)
        # so that Dataframe can be JSON-serialised
        for col in scenario_df.select_dtypes('datetime').columns:
            scenario_df[col] = scenario_df[col].astype('str')

        # Update the main data store for the web app
        # and compare old and new data (using sort_keys=True to ensure keys are in same order.)
        # If data changed, discard all steps after the current step
        old_data_json = json.dumps(app_data, sort_keys=True)
        app_data['step2'] = {
            'starttime_option': starttime_option,
            'scenario_parameters': sc_params,
            'scenario_df': scenario_df.to_dict(orient='tight')
        }
        data_json = json.dumps(app_data, sort_keys=True)
        if data_json != old_data_json:
            app_data = {f'step{n}': app_data[f'step{n}'] for n in (1, 2)}

        return current_step + 1, app_data, False, 'No errors detected.'

    except AssertionError as e:
        return dash.no_update, dash.no_update, True, str(e)
# endregion


# region helpers
def start_dates(stays_df: pd.DataFrame, option: Literal['Admission', 'FirstPosCollected']):
    """Generate a dataframe containing patient counts by start date, with a column
    containing the 7-day rolling average."""

    start_date_series = stays_df.Admission.copy()

    if option == 'FirstPosCollected':
        start_date_series[stays_df.Acquisition.str.startswith('Hospital')] = \
            stays_df.FirstPosCollected[stays_df.Acquisition.str.startswith('Hospital')]

    # Original type was pd.Timestamp before to_dict, thus stored in ISO format
    # After from_dict, we need to cast back to pd.Timestamp
    start_date_series = pd.to_datetime(start_date_series, format='ISO8601')

    start_date_df = pd.DataFrame(
        {'start': start_date_series, 'num_cases': 1}
    ).set_index('start').resample('D').count()

    # 7-day rolling average, using end date for x-value
    start_date_df['rolling_avg'] = start_date_df['num_cases'] \
        .rolling(window=7, min_periods=3, center=False).mean()

    return start_date_df


def beta_dist_df(x_min: pd.Timestamp, x_max: pd.Timestamp,
                 x_mode: pd.Timestamp, conc: float,
                 y_min: float, y_max: float):
    """Scaled and shifted beta distribution, with time-based x-axis.

    Parameters:
        x_min (pandas.Timestamp): The start date of the beta curve.
        x_max (pandas.Timestamp): The end date of the beta curve.
        x_mode (pandas.Timestamp): The peak date of the beta curve (where y is maximum).
        conc (pandas.Timestamp): How concentrated the curve is about its mode (maximum).
        y_min (pandas.Timestamp): The minimum value of the beta curve.
        y_max (pandas.Timestamp): The maximum value of the beta curve.

    Raises:
        AssertionError: If not (`x_min < x_max < x_mode` and `conc > 0` and `y_max > y_min`).
    """

    assert x_min < x_mode < x_max, "Dates must comply with start < peak < end."
    assert conc > 0, "Shape parameter of beta distribution must be positive."
    assert y_max > y_min, "Maximum value must be greater than minimum value."

    dates = np.arange(x_min, x_max, dtype='datetime64[D]')
    date_mapping = np.linspace(0, 1, len(dates))
    df = pd.DataFrame({'x': date_mapping, 'date': dates})
    mode = df.loc[df.date == x_mode, 'x'].item()

    a = mode * conc + 1
    b = (1 - mode) * conc + 1
    dist = beta(a, b)
    dist_max = dist.pdf(mode)

    df['y'] = dist.pdf(df.x) / dist_max * (y_max - y_min) + y_min
    return df


def fit_beta(data: pd.DataFrame):
    """Fits a beta curve to data.  The data should be a DataFrame with consecutive date indices
    and an integer column `num_cases`."""

    data['x'] = np.linspace(0, 1, len(data))

    def my_beta(x: float, mode: float, shape: float, y_min: float, y_max: float):
        a = mode * shape + 1
        b = (1 - mode) * shape + 1
        dist = beta(a, b)
        dist_max = dist.pdf(mode)
        y = dist.pdf(x) / dist_max * (y_max - y_min) + y_min
        return y

    p_opt, _ = curve_fit(
        f=my_beta,
        xdata=data['x'],
        ydata=data['num_cases'],
        p0=(0.5, 5, data['num_cases'].min(), data['num_cases'].max())
    )
    return p_opt

# endregion
