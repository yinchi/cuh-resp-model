"""Main module for Step 4 of the stepper: Simulation."""

import json
import zipfile
from copy import deepcopy
from io import BytesIO, StringIO
from time import sleep

import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, callback, dcc
from dash_compose import composition
from plotly import graph_objects as go

from cuh_resp_model.cache import bg_manager
from cuh_resp_model.components.back_next import back_next

ID_GRAPH = {'themed_graph': True, 'name': 'step4-graph-results'}

# region layout


@composition
def stepper_step():
    """The contents for Step 4 in the app."""

    with dmc.StepperStep(
        None,
        label="Simulate",
        description=dmc.Text(
            "Run simulation", size="xs")
    ) as ret:
        yield dcc.Store(id='step4-store', data={})
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 4: Simulate", ta="center", size="xl")
                yield stack()
                yield back_next('btn-stepper-4-to-3', None)
    return ret


@composition
def stack():
    """The DMC stack for Step 4."""

    with dmc.Stack(gap=36) as ret:
        with dmc.Stack(gap=10):
            yield dmc.Text('Configuration', fw=700, size='lg')
            with dmc.Group(m=0):
                yield dmc.Button(
                    'Download configuration (.zip)',
                    id='step4-button-download-config'
                )
                yield dcc.Download(
                    id='step4-download-config'
                )
        with dmc.Stack(gap=10):
            yield dmc.Text('Simulate!', fw=700, size='lg')
            yield dmc.Text(
                'Adjust the settings below to run the simulation. '
                'The jitter setting controls the amount of random noise '
                'added to the number of daily admissions, as set up in Step 2.'
            )
            with dmc.Group(align='start'):
                yield dmc.Button(
                    'Run simulation',
                    id='step4-button-simulate',
                    mt='1.6rem'
                )
                yield dmc.NumberInput(
                    id='step4-numberinput-num-replications',
                    label='Number of replications (min: 10)',
                    value=30,
                    min=10
                )
                yield dmc.NumberInput(
                    id='step4-numberinput-jitter',
                    label='Jitter',
                    value=20,
                    min=0,
                    max=100,
                    step=1,
                    suffix='%'
                )
        with dmc.Stack(id='step4-stack-progress', gap=10, display='none'):
            yield dmc.Text('Progress', fw=700, size='lg')
            with dmc.Group(align='center', gap='md'):
                yield dmc.Progress(
                    id='step4-progress-simulation',
                    value=0,
                    size='xl',
                    w='70%',
                )
                yield dmc.Text(
                    '0/30',
                    id='step4-text-progress'
                )
        with dmc.Stack(id='step4-stack-results', gap=10, display='none'):
            yield dmc.Text(
                'Simulation results',
                fw=700, size='lg'
            )
            with dmc.Group(m=0):
                yield dmc.Button(
                    'Download results (.xlsx)',
                    id='step4-button-download-results'
                )
                yield dcc.Download(id='step4-download-results')
            all_keys = ['Age ≥ 0 and Age < 16', 'Age ≥ 16 and Age < 65', 'Age ≥ 65']
            yield dmc.MultiSelect(
                id='step4-multiselect-age-groups',
                label="Age groups to include in plot:",
                description="Plot will show daily total occupancy for the selected age groups. "
                            "Use the 'Select all' button to include all age groups or the 'X' at the right side of the dropdown to clear the selection.",
                clearable=True,
                value=all_keys,  # Default to all age groups
                data=all_keys,
                w=800,
                checkIconPosition="right",
            )
            with dmc.Group(m=0):
                yield dmc.Button(
                    "Select all",
                    id='step4-button-all-age-groups',
                )
            yield dcc.Graph(
                id=ID_GRAPH,
                figure=go.Figure(
                    # data = graph_data(summaries, all_keys),
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
                )
            )
    return ret
# endregion


# region callbacks
@callback(
    Output('step4-store', 'data'),
    Output('step4-multiselect-age-groups', 'data'),
    Output('step4-multiselect-age-groups', 'value', allow_duplicate=True),
    Input('step4-button-simulate', 'n_clicks'),
    State('step4-numberinput-num-replications', 'value'),
    State('step4-numberinput-jitter', 'value'),
    State('store-appdata', 'data'),
    prevent_initial_call=True,
    background=True,
    manager=bg_manager,
    running=[
        (Output('step4-button-simulate', 'disabled'), True, False),
        (Output('step4-stack-progress', 'display'), None, 'none'),
        (Output('step4-stack-results', 'display'), 'none', None),
    ],
    progress=[
        Output('step4-progress-simulation', 'value'),
        Output('step4-text-progress', 'children'),
    ],
    cancel=[Input('stepper', 'active_step')]  # Cancel if active step changes
)
def simulate(
    set_progress: callable,
    _,  # n_clicks: int,
    num_reps: int,
    jitter: int,
    app_data: dict[str, any]
):
    """Run the simulation and return the results."""

    # Read stays_df from app_data and fix the data types.
    # We will use this to compute historical occupancy by age group.
    stays_df = pd.DataFrame.from_dict(app_data['step1']['stays_df'], orient='tight')
    stays_df = stays_df.assign(
        Admission=pd.to_datetime(stays_df['Admission'], format='ISO8601'),
        Discharge=pd.to_datetime(stays_df['Discharge'], format='ISO8601'),
        ReAdmission=pd.to_datetime(stays_df['ReAdmission'], format='ISO8601'),
        ReAdmissionDischarge=pd.to_datetime(stays_df['ReAdmissionDischarge'], format='ISO8601'),
        FirstPosCollected=pd.to_datetime(stays_df['FirstPosCollected'], format='ISO8601'),
    )

    # Get the scenario from the app data.
    scenario_df = pd.DataFrame.from_dict(app_data['step2']['scenario_df'], orient='tight')
    scenario_df = scenario_df.assign(
        date=pd.to_datetime(scenario_df['date'], format='ISO8601'),
    )

    # Get the age groups from the app data.
    age_groups = app_data['step3']['age_groups']

    results = []
    for i in range(1, num_reps + 1):
        # Get a Pandas dataframe with the total daily occupancy for the ward, with
        # the index being the date and the columns being the age groups.
        results.append(
            simulate_once(
                scenario_df=scenario_df,
                jitter=jitter / 100,  # Convert percentage to a fraction
                age_groups=age_groups,
            )
        )

        # Update the progress bar and text.
        set_progress((
            i / num_reps * 100,  # Progress, convert to percentage
            f'{i}/{num_reps}'  # Text display, e.g. '1/30'
        ))

    # For each age group, concatenate the results from all simulation replications.
    # The simulation replications are laid out across the columns.
    results_df = {}
    keys2 = [group['query'] for group in age_groups]
    keys = keys2 + ['Total']
    for key in keys:
        # Concatenate the results for this age group across all iterations.
        results_df[key] = pd.concat(
            [results[i][key] for i in range(num_reps)],
            axis=1
        )
        # Set the column names to be the iteration numbers.
        results_df[key].columns = [f'Iteration {i + 1}' for i in range(num_reps)]

    # For each age group, compute summary statistics across all iterations.
    summaries = {}
    for key in keys:
        s = key.replace('>=', '≥').replace('<=', '≤')
        summaries[s] = pd.DataFrame({
            'median': results_df[key].median(axis=1),
            'lower_quartile': results_df[key].quantile(0.25, axis=1),
            'upper_quartile': results_df[key].quantile(0.75, axis=1),
            'lower_decile': results_df[key].quantile(0.1, axis=1),
            'upper_decile': results_df[key].quantile(0.9, axis=1)
        }).to_dict(orient='tight')

    # Return the results (dmc.Store data, dmc.MultiSelect options) and select all age groups by default.  This triggers a re-render of the graph in another callback.
    all_keys = [k for k in summaries.keys() if k != 'Total']
    return summaries, all_keys, all_keys


@callback(
    Output('step4-multiselect-age-groups', 'value', allow_duplicate=True),
    Input('step4-button-all-age-groups', 'n_clicks'),
    State('step4-multiselect-age-groups', 'data'),
    prevent_initial_call=True
)
def select_all_age_groups(_, all_keys: list[str]):
    """Select all age groups in the MultiSelect component.  Triggered when the 'Select all' button is clicked."""
    return all_keys


@callback(
    Output('step4-download-config', 'data'),
    Input('step4-button-download-config', 'n_clicks'),
    State('store-appdata', 'data'),
    prevent_initial_call=True
)
def download_config(_, app_data: dict[str, any]):
    """Download the configuration as a JSON file."""

    data = deepcopy(app_data)
    # Remove the uploaded patient stay and occupancy data from the generated configuration file.
    del data['step1']['stays_df']
    del data['step1']['occupancy_df']

    # Convert the app data to JSON and write it to a StringIO object.
    config_json = json.dumps(data, sort_keys=False)
    config_file = StringIO(config_json)

    # Convert stays_df to a Parquet file in memory.
    stays_df = pd.DataFrame.from_dict(app_data['step1']['stays_df'], orient='tight')
    stays_df = stays_df.assign(
        Age=pd.to_numeric(stays_df['Age']),
        Admission=pd.to_datetime(stays_df['Admission'], format='ISO8601'),
        Discharge=pd.to_datetime(stays_df['Discharge'], format='ISO8601'),
        ReAdmission=pd.to_datetime(stays_df['ReAdmission'], format='ISO8601'),
        ReAdmissionDischarge=pd.to_datetime(stays_df['ReAdmissionDischarge'], format='ISO8601'),
        FirstPosCollected=pd.to_datetime(stays_df['FirstPosCollected'], format='ISO8601'),
    )
    stays_file = BytesIO()
    stays_df.to_parquet(stays_file, index=False)

    # Convert occupancy_df to a Parquet file in memory.
    occupancy_df = pd.DataFrame.from_dict(app_data['step1']['occupancy_df'], orient='tight')
    occupancy_df = occupancy_df.assign(
        date=pd.to_datetime(occupancy_df['date'], format='ISO8601'),
        critical=pd.to_numeric(occupancy_df['critical']),
        noncritical=pd.to_numeric(occupancy_df['noncritical']),
    )
    occupancy_file = BytesIO()
    occupancy_df.to_parquet(occupancy_file, index=False)

    # Prepare the zip file in memory.
    # Pandas' to_parquet() method already uses 'snappy' compression by default,
    # so we use ZIP_STORED to avoid double compression.
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_STORED) as zip_file:
        zip_file.writestr('config.json', config_file.getvalue())
        zip_file.writestr('stays.parquet', stays_file.getvalue())
        zip_file.writestr('occupancy.parquet', occupancy_file.getvalue())

    zip_buffer.seek(0)
    return dcc.send_bytes(
        zip_buffer.read(),
        filename='simulation_config.zip',
        mime_type='application/zip'
    )


@callback(
    Output('stepper', 'active', allow_duplicate=True),
    Input('btn-stepper-4-to-3', 'n_clicks'),
    State('stepper', 'active'),
    prevent_initial_call=True
)
def stepper_back(_, current_step: int):
    """Go back to the previous step."""
    return current_step - 1  # 1-based to 0-based numbering
# endregion


# region helpers
def simulate_once(scenario_df: pd.DataFrame, jitter: float, age_groups: list[dict[str, any]]):
    """Run a single simulation iteration."""
    # Placeholder for the actual simulation logic. For now, we just return an empty dict.

    sleep(1)  # Simulate some processing time

    # Return a dummy result with the same structure as the expected output.
    # Use the query string from each age group as the column name for that group,
    # e.g. 'Age >= 0 and Age < 16'.
    return pd.DataFrame(
        [],
        index=pd.DatetimeIndex([], name='date'),
        dtype='int64',
        columns=[group['query'] for group in age_groups] + ['Total']
    )
# endregion
