"""Module for the Daily Arrivals tab of Step 3: Patient Length-of-Stay Modelling"""

from copy import deepcopy

import dash
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
from dash import Input, Output, Patch, State, callback, clientside_callback, dcc
from dash_compose import composition
from fitter import Fitter
from plotly import graph_objects as go
from scipy import stats
from scipy.stats import zscore

from cuh_resp_model.cache import bg_manager
from cuh_resp_model.components.ids import *

from ..components.back_next import back_next

DAY = pd.Timedelta(days=1)

GO_OPTS = {
    'spanmode': 'hard',
    'box_visible': True,
    'box_fillcolor': '#aa55aa',
    'box_line_color': '#aa00aa',
    'points': 'all',
    'meanline_visible': True,
    'meanline_color': 'red',
    'marker_size': 2,
    'marker_opacity': 0.5,
    'y0': 'LoS [days]',
    'orientation': 'h',
    'hoverinfo': 'skip'
}

PLACEHOLDER_TABLE_DATA = {
    "head": ["Placeholder"],
    "body": [[0]]
}


@composition
def stepper_step():
    """The contents for the Stepper Step 3 in the app."""
    go_layout = {
        'width': 1000,
        'height': 300,
        'title': 'Length of stay [days]',
        'legend_y': 0.5,
        'legend_font_size': 14,
        'title_font_size': 20,
        'xaxis': {'tickfont': {'size': 14}},
        'yaxis': {'tickfont': {'size': 14}},
        'title_font_weight': 900,
        'hovermode': 'x unified'
    }
    table_opts = {
        'striped': True,
        'highlightOnHover': True,
        'withTableBorder': True,
        'withColumnBorders': True
    }
    select_opts = {
        'label': 'Select distribution type',
        'description': 'The chosen distribution will be used for the final '
        'simulation step',
        'placeholder': 'Choose distribution type',
        'allowDeselect': False,
        'w': 400
    }
    with dmc.StepperStep(
        None,
        label="LoS Modelling",
        description=dmc.Text(
            "Fit patient length-of-stay distributions", size="xs")
    ) as ret:
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 3: Patient Length-of-Stay Modelling", ta="center", size="xl")
                yield dcc.Store(id=ID_STORE_PAEDS_FIT)
                yield dcc.Store(id=ID_STORE_ADULT_FIT)
                yield dcc.Store(id=ID_STORE_SENIOR_FIT)
                with dmc.Card(withBorder=True):
                    yield dmc.Text('0-15 Age group', size='xl', fw=700)
                    with dmc.Stack():
                        yield dcc.Graph(
                            id=ID_GRAPH_PAEDS,
                            figure=go.Figure(layout=go_layout)
                        )
                        yield dmc.Text('Distribution fitting results', fw=700)
                        with dmc.Stack(id='id-paeds-fit', pos="relative"):
                            yield dmc.LoadingOverlay(
                                id=ID_OVERLAY_PAEDS_FIT,
                                visible=True,
                                overlayProps={"radius": "sm", "blur": 2}
                            )
                            yield dmc.Table(
                                id=ID_TABLE_PAEDS_FIT,
                                **table_opts,
                                data=PLACEHOLDER_TABLE_DATA
                            )
                            yield dmc.Select(
                                id=ID_SELECT_PAEDS_FIT,
                                **select_opts,
                                data=['Placeholder'],
                            )
                with dmc.Card(withBorder=True):
                    yield dmc.Text('16-64 Age group', size='xl', fw=700)
                    with dmc.Stack():
                        yield dcc.Graph(
                            id=ID_GRAPH_ADULT,
                            figure=go.Figure(layout=go_layout)
                        )
                        yield dmc.Text('Distribution fitting results', fw=700)
                        with dmc.Stack(id='id-adult-fit', pos="relative"):
                            yield dmc.LoadingOverlay(
                                id=ID_OVERLAY_ADULT_FIT,
                                visible=True,
                                overlayProps={"radius": "sm", "blur": 2}
                            )
                            yield dmc.Table(
                                id=ID_TABLE_ADULT_FIT,
                                **table_opts,
                                data=PLACEHOLDER_TABLE_DATA
                            )
                            yield dmc.Select(
                                id=ID_SELECT_ADULT_FIT,
                                **select_opts,
                                data=['Placeholder'],
                            )
                with dmc.Card(withBorder=True):
                    yield dmc.Text('65+ Age group', size='xl', fw=700)
                    with dmc.Stack():
                        yield dcc.Graph(
                            id=ID_GRAPH_SENIOR,
                            figure=go.Figure(layout=go_layout)
                        )
                        yield dmc.Text('Distribution fitting results', fw=700)
                        with dmc.Stack(id='id-senior-fit', pos="relative"):
                            yield dmc.LoadingOverlay(
                                id=ID_OVERLAY_SENIOR_FIT,
                                visible=True,
                                overlayProps={"radius": "sm", "blur": 2}
                            )
                            yield dmc.Table(
                                id=ID_TABLE_SENIOR_FIT,
                                **table_opts,
                                data=PLACEHOLDER_TABLE_DATA
                            )
                            yield dmc.Select(
                                id=ID_SELECT_SENIOR_FIT,
                                **select_opts,
                                data=['Placeholder'],
                            )
                yield back_next(ID_STEPPER_BTN_3_TO_2, ID_STEPPER_BTN_3_TO_4)
    return ret


# region callbacks
#

# Go back to Step 2: Arrival modelling.
clientside_callback(
    """(step, state) => state - 1""",
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_3_TO_2, "n_clicks"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Output(ID_STORE_APPDATA, "data", allow_duplicate=True),
    Input(ID_STEPPER_BTN_3_TO_4, "n_clicks"),
    State(ID_STORE_APPDATA, "data"),
    State(ID_STEPPER, "active"),
    State(ID_SELECT_PAEDS_FIT, 'value'),
    State(ID_SELECT_ADULT_FIT, 'value'),
    State(ID_SELECT_SENIOR_FIT, 'value'),
    State(ID_STORE_PAEDS_FIT, 'data'),
    State(ID_STORE_ADULT_FIT, 'data'),
    State(ID_STORE_SENIOR_FIT, 'data'),
    prevent_initial_call=True
)
def stepper_next(_, data, curr_state,
                 seleted_dist_paeds, selected_dist_adult, selected_dist_senior,
                 dists_paeds, dists_adult, dists_senior):
    """Process app data for Step 2 and proceed to Step 3."""

    # Error handling -- this should not trigger, so just return no_update and
    # don't worry about showing error messages
    if not seleted_dist_paeds or not selected_dist_adult or not selected_dist_senior:
        return dash.no_update, dash.no_update

    new_data = deepcopy(data)
    new_data['completed'] = 3

    los_df = load_los(data['step_1']['los_data'])
    age_dist = {
        'paeds': np.mean(los_df.Age < 16),
        'adult': np.mean((los_df.Age >= 16) & (los_df.Age < 65)),
        'senior': np.mean(los_df.Age >= 65),
    }

    new_data['step_3'] = {
        'selected_dists': {
            'paeds': seleted_dist_paeds,
            'adult': selected_dist_adult,
            'senior': selected_dist_senior,
        },
        'dists': {
            'paeds': dists_paeds,
            'adult': dists_adult,
            'senior': dists_senior,
        },
        'age_dist': age_dist
    }

    return curr_state + 1, new_data


# Disable the "Next button if any inputs are missing."
clientside_callback(
    """(v1, v2, v3) => (!v1 || !v2 || !v3)""",
    Output(ID_STEPPER_BTN_3_TO_4, 'disabled'),
    Input(ID_SELECT_PAEDS_FIT, 'value'),
    Input(ID_SELECT_ADULT_FIT, 'value'),
    Input(ID_SELECT_SENIOR_FIT, 'value'),
)


@callback(
    Output(ID_GRAPH_PAEDS, 'figure', allow_duplicate=True),
    Output(ID_GRAPH_ADULT, 'figure', allow_duplicate=True),
    Output(ID_GRAPH_SENIOR, 'figure', allow_duplicate=True),
    Input(ID_STEPPER, 'active'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True
)
def render_patient_arr_graph(active_step, app_data: dict):
    """Render the LoS graphs for the three age groups."""

    if active_step != 2:  # Step 3
        return dash.no_update

    los_data = app_data['step_1']['los_data']
    los_df = load_los(los_data)

    # See: https://dash.plotly.com/partial-properties#using-patches-on-multiple-outputs
    paeds_figure = Patch()
    adults_figure = Patch()
    seniors_figure = Patch()

    paeds_figure['data'] = []
    adults_figure['data'] = []
    seniors_figure['data'] = []

    paeds_figure['data'].append(
        go.Violin(x=los_df.loc[los_df.Age < 16, 'LOS_Total'], **GO_OPTS)
    )

    adults_figure['data'].append(
        go.Violin(x=los_df.loc[(los_df.Age >= 16) & (los_df.Age < 65), 'LOS_Total'], **GO_OPTS)
    )

    seniors_figure['data'].append(
        go.Violin(x=los_df.loc[los_df.Age >= 65, 'LOS_Total'], **GO_OPTS)
    )

    return paeds_figure, adults_figure, seniors_figure


@callback(
    Output(ID_TABLE_PAEDS_FIT, 'data'),
    Output(ID_SELECT_PAEDS_FIT, 'data'),
    Output(ID_SELECT_PAEDS_FIT, 'value'),
    Output(ID_OVERLAY_PAEDS_FIT, 'visible'),
    Output(ID_STORE_PAEDS_FIT, 'data'),
    Input(ID_STEPPER, 'active'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True,
    background=True,
    manager=bg_manager
)
def fit_los_paeds(active_step, app_data: dict):
    """Fit LoS distributions to the paeds patient data."""
    if active_step != 2:  # Step 3
        return dash.no_update, dash.no_update, dash.no_update, True, dash.no_update

    los_data = app_data['step_1']['los_data']
    los_stats, dists = fit_los(los_data, 'paeds')
    return los_stats, [x[0] for x in los_stats['body']], None, False, dists


@callback(
    Output(ID_TABLE_ADULT_FIT, 'data'),
    Output(ID_SELECT_ADULT_FIT, 'data'),
    Output(ID_SELECT_ADULT_FIT, 'value'),
    Output(ID_OVERLAY_ADULT_FIT, 'visible'),
    Output(ID_STORE_ADULT_FIT, 'data'),
    Input(ID_STEPPER, 'active'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True,
    background=True,
    manager=bg_manager
)
def fit_los_adult(active_step, app_data: dict):
    """Fit LoS distributions to the adult (non-senior) patient data."""
    if active_step != 2:  # Step 3
        return dash.no_update, dash.no_update, dash.no_update, True, dash.no_update

    los_data = app_data['step_1']['los_data']
    los_stats, dists = fit_los(los_data, 'adult')
    return los_stats, [x[0] for x in los_stats['body']], None, False, dists


@callback(
    Output(ID_TABLE_SENIOR_FIT, 'data'),
    Output(ID_SELECT_SENIOR_FIT, 'data'),
    Output(ID_SELECT_SENIOR_FIT, 'value'),
    Output(ID_OVERLAY_SENIOR_FIT, 'visible'),
    Output(ID_STORE_SENIOR_FIT, 'data'),
    Input(ID_STEPPER, 'active'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True,
    background=True,
    manager=bg_manager
)
def fit_los_senior(active_step, app_data: dict):
    """Fit LoS distributions to the senior patient data."""
    if active_step != 2:  # Step 3
        return dash.no_update, dash.no_update, dash.no_update, True, dash.no_update

    los_data = app_data['step_1']['los_data']
    los_stats, dists = fit_los(los_data, 'senior')
    return los_stats, [x[0] for x in los_stats['body']], None, False, dists
#
# endregion


# region helpers
#
def load_los(los_data):
    """Load LoS data from the Dash store into a pandas DataFrame."""
    los_df = pd.DataFrame.from_dict(los_data, orient='tight')
    los_df = los_df.loc[:, ['Age', 'Admission', 'Discharge', 'ReAdmission', 'ReAdmissionDisch']]
    los_df = los_df.assign(
        Admission=pd.to_datetime(los_df.Admission, format='ISO8601'),
        Discharge=pd.to_datetime(los_df.Discharge, format='ISO8601'),
        ReAdmission=pd.to_datetime(los_df.ReAdmission, format='ISO8601'),
        ReAdmissionDisch=pd.to_datetime(los_df.ReAdmissionDisch, format='ISO8601'),
    )
    los_df = los_df\
        .assign(LOS=los_df.Discharge - los_df.Admission,
                LOS_ReAdmission=los_df.ReAdmissionDisch - los_df.ReAdmission)\
        .fillna({'LOS_ReAdmission': pd.Timedelta(0)})
    los_df = los_df.assign(LOS_Total=(los_df.LOS + los_df.LOS_ReAdmission) / DAY)
    return los_df


def get_params(dist_name):
    """Get the parameter names for a given distribution."""
    # Inspired by the code for Fitter.get_best()
    d = getattr(stats, dist_name)
    return (d.shapes + ", loc, scale").split(", ") if d.shapes else ["loc", "scale"]


def fit_los(los_data, group: str):
    """Fit an LoS distribution."""

    # Load data and select age group
    los_df = load_los(los_data)
    if group == 'paeds':
        los = los_df.loc[los_df.Age < 16, 'LOS_Total']
    elif group == 'adult':
        los = los_df.loc[(los_df.Age >= 16) & (los_df.Age < 65), 'LOS_Total']
    elif group == 'senior':
        los = los_df.loc[los_df.Age >= 65, 'LOS_Total']
    else:
        raise ValueError(f'Unexpected value for LoS group: {group}')

    # Remove outliers
    los = los[np.abs(zscore(los)) < 3]

    # Fit distributions
    f = Fitter(los, timeout=10)
    f.fit()

    # Distribution statistics sorted by sum of squared errors
    fit_df = f.df_errors.loc[
        np.isfinite(f.df_errors.sumsquare_error),
        ['sumsquare_error', 'aic', 'bic', 'ks_pvalue']
    ].sort_values(
        'sumsquare_error'
    ).assign(
        dist_mean=np.nan,
        dist_std=np.nan
    )

    # Filter results by standard deviation
    s = np.std(los)

    for dist_name in fit_df.index:
        dist = getattr(stats, dist_name)(*f.fitted_param[dist_name])
        fit_df.loc[dist_name, 'dist_mean'] = dist.mean()
        fit_df.loc[dist_name, 'dist_std'] = dist.std()
    fit_df = fit_df.loc[
        (fit_df.dist_mean > 0) & (fit_df.dist_std > 0.75 * s) & (fit_df.dist_std < 1.5 * s)
    ]

    # Keep top 5 only
    fit_df = fit_df[:5].reset_index(names='Distribution')

    fit_df.sumsquare_error = fit_df.sumsquare_error.round(6)
    fit_df.aic = fit_df.aic.round(3)
    fit_df.bic = fit_df.bic.round(3)
    fit_df.ks_pvalue = fit_df.ks_pvalue.round(5)
    fit_df.dist_mean = fit_df.dist_mean.round(4)
    fit_df.dist_std = fit_df.dist_std.round(4)

    # Rename columns
    fit_df.columns = [
        'Distribution',
        'Σ(error²)',
        'AIC',
        'BIC',
        'KS p-value',
        'Mean',
        'St. dev.'
    ]

    data = {
        'head': fit_df.columns.to_list(),
        'body': fit_df.to_numpy().tolist()
    }
    dists = {
        n: dict(zip(get_params(n), f.fitted_param[n]))
        for n in fit_df.Distribution
    }
    return data, dists
#
# endregion
