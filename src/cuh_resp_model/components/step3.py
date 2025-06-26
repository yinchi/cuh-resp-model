"""Main module for Step 3 of the stepper: Length-of-stay modelling."""

import os
import re
from base64 import b64encode
from io import BytesIO
from itertools import pairwise
from typing import Any

import dash
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import shutup
from dash import Input, Output, Patch, State, callback, dcc
from dash_compose import composition
from matplotlib import pyplot as plt
from plotly import graph_objects as go
from scipy import stats
from scipy.stats import zscore

from cuh_resp_model.components.back_next import back_next
from cuh_resp_model.components.step2 import start_dates

# fmt: off
# isort: off
os.environ['LOGURU_AUTOINIT'] = '0'
import fitter  # pylint: disable=C0411,C0413
COMMON_DISTS = fitter.get_common_distributions()
# isort: on
# fmt: on


ID_GRAPH = {'themed_graph': True, 'name': 'step3-graph-arrivals'}


# region layout
@composition
def stepper_step():
    """The contents for Step 3 in the app."""

    with dmc.StepperStep(
        None,
        label="LoS modelling",
        description=dmc.Text(
            "Fit distribution for patient LoS", size="xs")
    ) as ret:
        yield dcc.Store(id='step3-store', data={})
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 3: Length-of-stay modelling", ta="center", size="xl")
                yield stack()
                yield back_next('btn-stepper-3-to-2', 'btn-stepper-3-to-4')
    return ret


@composition
def stack():
    """The DMC stack for Step 3."""

    with dmc.Stack(gap=36) as ret:
        with dmc.Stack(gap=10):
            yield dmc.Text('Start date option:', fw=700, size='lg')
            yield dmc.Text('', id='step3-text-starttime-mode', size='sm')
        with dmc.Stack(gap=10):
            yield dmc.Text('Define age groups:', fw=700, size='lg')
            yield dcc.Markdown('''\
Enter a list of age breakpoints, separated by commas.  For example, `16,65` creates three
age groups, 0-15, 16-64, and 65+.  Leaving the input below blank creates a single age group
for all patients.

Selecting "Common distributions only" will attempt only the common distribution types as defined
by the
[`fitter`](https://fitter.readthedocs.io/en/latest/faqs.html#what-are-the-distributions-available)
Python module.  To reduce computation time, it is recommended to leave this option checked.
''', style={'font-size': 'small'})
            yield dmc.TextInput(
                id='step3-textinput-age-groups',
                label='Age group breakpoints',
                value="16,65",
                w=200
            )
        with dmc.Stack(gap=10):
            yield dmc.Text('Select date range for LoS fitting:', fw=700, size='lg')
            with dmc.Group(align='start'):
                yield dmc.DateInput(id='step3-dateinput-los-start',
                                    label='Start date (DD-MM-YYYY)',
                                    valueFormat='DD-MM-YYYY',
                                    value='2022-05-18',
                                    w=200)
                yield dmc.DateInput(id='step3-dateinput-los-end',
                                    label='End date (DD-MM-YYYY)',
                                    valueFormat='DD-MM-YYYY',
                                    value='2022-09-03',
                                    w=200)
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
            )
        with dmc.Stack(gap=10):
            yield dmc.Text('Fit length-of-stay distributions:', fw=700, size='lg')
            with dmc.Group(align='start'):
                yield dmc.Button(
                    'Fit LoS distributions',
                    id='step3-button-fit-los'
                )
                yield dmc.Checkbox(
                    id='step3-checkbox-fit-common-only',
                    label='Common distributions only',
                    checked=True,
                    size='md',
                    mt='0.3rem'
                )
        with dmc.Box(id='step3-loading', pos='relative'):
            yield dmc.LoadingOverlay(
                id='step3-loading',
                loaderProps={"color": "red", "size": "md"},
                overlayProps={"radius": "sm", "blur": 2},
                visible=False
            )
            yield dmc.Box(id='step3-box-results-placeholder', h=200, w=100, display='none')
            yield dmc.Box(id='step3-box-results', display='none')
    return ret
# endregion


# region callbacks
@callback(
    Output('step3-text-starttime-mode', 'children'),
    Input('store-appdata', 'data'),
)
def start_mode_msg(app_data: dict[str, Any]):
    """Show which mode is used for the start time of hospital-acquired infections."""

    try:
        starttime_option = app_data['step2']['starttime_option']
    except KeyError as e:
        raise dash.exceptions.PreventUpdate from e

    if starttime_option == 'FirstPosCollected':
        return 'Using time of first postive test as start time for hospital-acquired infections, ' \
            'and admission time for all other infections.  Go back to Step 2 to change this.'

    return 'Using admission time as start time for all cases, including ' \
        'hospital-acquired infections.    Go back to Step 2 to change this.'


@callback(
    Output(ID_GRAPH, 'figure', allow_duplicate=True),
    Input('stepper', 'active'),  # current step
    State('store-appdata', 'data'),
    prevent_initial_call=True
)
def render_arrivals_graph(
    active_step: int,
    app_data: dict[str, Any]
):
    """Plot daily arrivals."""

    if active_step != 2:
        raise dash.exceptions.PreventUpdate

    disease_name: str = app_data['step1']['disease_name']
    starttime_option = app_data['step2']['starttime_option']

    # TODO: extract duplicate code for plotting arrivals & 7-day average
    # (Steps 2 and 3)

    patched_fig = Patch()
    patched_fig['layout']['title']['text'] = f'{disease_name} cases by start date'
    patched_fig['data'] = []  # reset plots

    # Extract start dates of patients
    stays_df = pd.DataFrame.from_dict(app_data['step1']['stays_df'], orient='tight')
    start_date_df = start_dates(stays_df, option=starttime_option)

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

    return patched_fig


@callback(
    Output('step3-box-results', 'children'),
    Output('step3-store', 'data'),
    Input('step3-button-fit-los', 'n_clicks'),
    State('step3-dateinput-los-start', 'value'),
    State('step3-dateinput-los-end', 'value'),
    State('step3-textinput-age-groups', 'value'),
    State('step3-checkbox-fit-common-only', 'checked'),
    State('store-appdata', 'data'),
    running=[
        (Output('step3-loading', 'visible'), True, False),
        (Output('step3-box-results-placeholder', 'display'), None, 'none'),
        (Output('step3-box-results', 'display'), 'none', None)
    ],
    prevent_initial_call=True
)
@composition
def fit_los(_,
            start_date: str, end_date: str,
            age_breakpoints: str, common_only: bool,
            app_data: dict[str, Any]):
    """Fit LoS distributions to the defined age groups.  Returns either a `dmc.Stack` component
    for displaying the results or a `dmc.Alert` with an error message.

    `age_breakpoints` should be a comma-delimited list of integers, e.g. "16,65" defines
    the age groups 0-15, 16-64, 65+.

    If `common_only` is True, only the most common distribution types as defined in the `fitter`
    module are checked.
    """

    try:
        starttime_option = app_data['step2']['starttime_option']
        start = pd.to_datetime(start_date, format='ISO8601')
        end = pd.to_datetime(end_date, format='ISO8601')
        assert start < end, 'Start date must be before end date.'

        age_groups = get_age_groups(age_breakpoints)

        stays_df = pd.DataFrame.from_dict(app_data['step1']['stays_df'], orient='tight')
        stays_df = stays_df.assign(
            Admission=pd.to_datetime(stays_df.Admission, format='ISO8601'),
            Discharge=pd.to_datetime(stays_df.Discharge, format='ISO8601'),
            ReAdmission=pd.to_datetime(stays_df.ReAdmission, format='ISO8601'),
            ReAdmissionDischarge=pd.to_datetime(stays_df.ReAdmissionDischarge, format='ISO8601'),
            FirstPosCollected=pd.to_datetime(stays_df.FirstPosCollected, format='ISO8601'),
        )

        # Adjust start dates for hospital-acquired infections based on `starttime_option`
        df = stays_df.copy()
        df = df.assign(Start=df.Admission)
        if starttime_option == 'FirstPosCollected':
            df.loc[df.Acquisition.str.startswith('Hospital'), 'Start'] = \
                df.loc[df.Acquisition.str.startswith('Hospital'), 'FirstPosCollected']

        # Filter df by date range
        df = df.query('Start >= @start and Start <= @end')
        df = df.loc[df.Discharge.notna()]

        # For each age group, generate fit parameters and Plotly graph object
        for group in age_groups:
            query = group['query']
            group_df = df.query(query)
            assert not group_df.empty, \
                f'No patients found for age group ({query}).'
            assert len(group_df) >= 10, \
                f'Fewer than 10 patients found for age group ({query}); ' \
                f'fitting not attempted.'
            dist_type, dist_params, fitted_plot = fit_los_helper(group_df, common_only)

            # Append results to the group's dict object
            group.update({
                'dist_type': dist_type,
                'dist_params': dist_params,
                'fit_plot': fitted_plot
            })

        # Create a DMC Stack to display the results
        with dmc.Stack(gap=5) as ret:
            yield dmc.Text('LoS fitting results:', size='lg', fw=700)
            for group in age_groups:
                age_group = group['query'].replace('>=', '≥').replace('<=', '≤')
                yield dmc.Text(
                    f"Age group: {age_group}",
                    size='md', fw=700
                )
                yield dmc.Text(
                    f"Fitted distribution: {group['dist_type']}"
                )
                params = {k: round(v, 4) for k, v in group['dist_params'].items()}
                yield dmc.Text(
                    f"Parameters: {params}"
                )
                yield img_from_bytes(
                    group['fit_plot'],
                    style={'max-width': '70%', 'height': 'auto'}
                )
                yield dmc.Space(h=10)

        # Create the data to store in the step 3 store
        step3_data = {
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
            # Remove the 'fit_plot' key from each result to avoid storing large images
            'results': [{k: v for k, v in group.items() if k != 'fit_plot'}
                        for group in age_groups]
        }

        return ret, step3_data

    except AssertionError as e:
        alert = dmc.Alert(
            f'Error fitting LoS distributions: {e}',
            color='red',
            title=dmc.Text(
                'Error!',
                fw=700, size='lg'
            ),
            id='step3-alert-fit-los-error'
        )

        # Clear the Step 3 store as the fitting failed, this prevents stale data from being used
        # in subsequent steps.
        return alert, None


@callback(
    Output('stepper', 'active', allow_duplicate=True),
    Input('btn-stepper-3-to-2', 'n_clicks'),
    State('stepper', 'active'),
    prevent_initial_call=True
)
def stepper_back(_, current_step: int):
    """Go back to the previous step."""
    return current_step - 1  # 1-based to 0-based numbering
# endregion


# region helpers
def get_age_groups(age_breakpoints: str):
    """Generate age group infomation, i.e. bounds and query strings, from a comma-delimited string,
    e.g. '16,65' generates the [0,16), [16,65), and [65, inf) age groups."""

    # Validate str input
    age_breakpoints = '' if not age_breakpoints else age_breakpoints  # Handle None

    regex = r'^\d+(,\d+)*$'
    assert re.fullmatch(regex, age_breakpoints) is not None, \
        'Invalid input.  Expected a string of integers delimited by commas.'

    # Empty string case: single age group
    if age_breakpoints == '':
        return [{
            'lower': 0,
            'upper': None,
            'query': "Age >= 0"
        }]

    # Split str by comma and generate a dict for each age group
    age_breakpoints = age_breakpoints.split(',')
    age_breakpoints = [int(age) for age in age_breakpoints]

    assert all(x < y for x, y in pairwise(age_breakpoints)), \
        'Age breakpoints must be in strictly ascending order with no duplicates.'

    pairs = list(pairwise([0] + age_breakpoints + [None]))
    return [
        {
            'lower': pair[0],
            'upper': pair[1],
            'query': f"Age >= {pair[0]}{f' and Age < {pair[1]}' if pair[1] is not None else ''}"
        }
        for pair in pairs
    ]


def img_from_bytes(img_bytes: bytes, **kwargs):
    """Return a dash.html.Img component from a bytes object."""
    encoded = b64encode(img_bytes).decode('utf-8')
    src = f"data:image/png;base64,{encoded}"
    return dmc.Image(src=src, **kwargs)


def fit_los_helper(df: pd.DataFrame, common_only: bool):
    """Fit LoS distributions to the given DataFrame.

    Returns the distribution type, parameters, and a base64-encoded image of the fitted
    distribution plot (as a str).
    """

    # Compute total length of stay (LoS)
    df = df.assign(LoS=(df.Discharge - df.Admission) / pd.Timedelta(days=1))
    df = df.assign(ReLoS=(df.ReAdmissionDischarge - df.ReAdmission) / pd.Timedelta(days=1))
    df.ReLoS = df.ReLoS.fillna(0)
    df = df.assign(TotalLoS=df.LoS + df.ReLoS)
    los = df.TotalLoS.to_numpy()

    # Remove outliers
    filtered_los = los[abs(zscore(los)) <= 3]

    # Fit distributions using fitter
    f = fitter.Fitter(
        filtered_los,
        distributions=COMMON_DISTS if common_only else None  # None = default (all distributions)
    )
    # Since the fitter module is very verbose, we mute its warnings.
    with shutup.mute_warnings:
        f.fit(max_workers=1)

    # Sort results by sum squared error (SSE) and compute the distibution/empirical means and
    # standard deviations
    fit_df = f.df_errors.loc[
        np.isfinite(f.df_errors.sumsquare_error),
        ['sumsquare_error', 'aic', 'bic', 'ks_pvalue']
    ].sort_values(
        'sumsquare_error'
    ).assign(
        dist_mean=np.nan,
        dist_std=np.nan,
        data_mean=filtered_los.mean(),
        data_std=filtered_los.std()
    )

    # Get the distribution means and standard deviations for each fitted distribution.
    with shutup.mute_warnings:
        for dist_name in fit_df.index:
            dist = getattr(stats, dist_name)(*f.fitted_param[dist_name])
            fit_df.loc[dist_name, 'dist_mean'] = dist.mean()
            fit_df.loc[dist_name, 'dist_std'] = dist.std()

    # Get the ratios of the distribution means and stds to the empirical means and stds
    fit_df = fit_df.assign(
        mean_ratio=fit_df.dist_mean / fit_df.data_mean,
        std_ratio=fit_df.dist_std / fit_df.data_std,
    )

    # Filter out distributions with NaN statistics
    fit_df = fit_df.dropna(axis=0, how='any')

    # Filter out distributions where the mean or std ratio is not close to 1
    fit_df = fit_df.query('0.95 < mean_ratio < 1.05 and 0.9 < std_ratio < 1.1')\
        .sort_values(by='sumsquare_error')

    assert not fit_df.empty, \
        'Could not get a good fit to the LoS data.'

    # Get the best distribution type and parameters
    best_fit_type = str(fit_df.index[0])

    # Create a new Fitter object with just the best distribution type
    f2 = fitter.Fitter(filtered_los, distributions=[best_fit_type])
    f2.fit(max_workers=1)

    # Get the fitted parameters for the best distribution type
    best_fit_params = dict(zip(get_params(best_fit_type), f2.fitted_param[best_fit_type]))

    # Create a figure with the fitted and empirical distributions
    png_encoded = fit_plot(f2)

    return (
        best_fit_type,
        best_fit_params,
        png_encoded
    )


def get_params(dist_name):
    """Get the parameters for the given distribution name.  The distribution name should be
    a string matching the name of a distribution in `scipy.stats`.

    Inspired by the code for `Fitter.get_best()`.
    """
    d: stats.rv_continuous = getattr(stats, dist_name)
    # d.shapes is a string of parameter names, e.g. 'a, b'.
    # Add 'loc' and 'scale' to the list of parameters.
    return (d.shapes + ", loc, scale").split(", ") if d.shapes else ["loc", "scale"]


def fit_plot(f: fitter.Fitter):
    """Create a figure with the fitted and empirical distributions.  Returns a bytes object
    containing the figure image.
    """
    # Create and decorate the figure
    plt.rcParams.update({'font.size': 12})  # Set font size for matplotlib
    plt.figure(figsize=(10, 5))
    f.hist()
    f.plot_pdf()
    plt.legend(fontsize='11', loc='upper right')
    plt.title('Fitted distribution')
    plt.xlabel('Length of stay, days')
    plt.ylabel('Distribution density')

    # Save the figure to a bytes object
    io = BytesIO()
    plt.tight_layout(pad=1)
    plt.savefig(io, format='png')
    io.seek(0)
    png_bytes = io.read()
    plt.close()  # Close the figure to free memory

    # Return the image bytes
    return png_bytes
# endregion
