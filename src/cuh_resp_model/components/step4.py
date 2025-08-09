"""Main module for Step 4 of the stepper: Simulation."""

import json
import zipfile
from copy import deepcopy
from io import BytesIO, StringIO
from typing import Any, Callable

import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, callback, dcc
from dash_compose import composition
from plotly import graph_objects as go

from cuh_resp_model.cache import bg_manager
from cuh_resp_model.components.back_next import back_next
from cuh_resp_model.sim import (gen_plotly, get_quantiles, sim, sim_results_from_dict,
                                sim_results_to_dict)

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
                            "Use the 'Select all' button to include all age groups or the 'X' at "
                            "the right side of the dropdown to clear the selection.",
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
    set_progress: Callable[[int], Any],
    _,  # n_clicks: int,
    num_reps: int,
    jitter: int,
    app_data: dict[str, any]
):
    """Run the simulation and return the results.

    See `cuh_resp_model.sim.simulate_once()` for details on the simulation parameters.
    """

    # Get the scenario from the app data.
    scenario_df = pd.DataFrame.from_dict(app_data['step2']['scenario_df'], orient='tight')
    scenario_df = scenario_df.assign(
        date=pd.to_datetime(scenario_df['date'], format='ISO8601'),
    )

    # Get the age groups from the app data.
    age_df = pd.DataFrame.from_dict(app_data['step3']['age_groups'], orient='columns')

    # Use the 'query' column to get the age group names, e.g. "Age ≥ 0 and Age < 16".
    # This is used for the MultiSelect component.
    age_group_names = age_df['query'].tolist()

    sim_results = sim(
        scenario_df=scenario_df,
        age_df=age_df,
        n_runs=num_reps,
        jitter=jitter/100,  # Convert percentage to fraction.
        extra_days=25,  # TODO: Add control for this in the UI.
        set_progress=set_progress,
    )

    return (
        sim_results_to_dict(sim_results),
        age_group_names,
        age_group_names  # Default to all age groups selected
    )


@callback(
    Output(ID_GRAPH, 'figure', allow_duplicate=True),
    Input('step4-store', 'data'),
    Input('step4-multiselect-age-groups', 'value'),
    prevent_initial_call=True
)
def graph_results(
    app_data: dict[str, any],
    selected_age_groups: list[str]
):
    """Generate the graph for the simulation results."""

    def group_sum(dfs, selected_age_groups):
        """
        Combine the bed occupancy data for selected age groups into a single series.
        """
        return pd.concat(
            (dfs[g] for g in selected_age_groups),
            axis=1, join='outer'
        ).ffill().sum(axis=1)

    if not selected_age_groups or not app_data:
        # If no age groups are selected or no app data is available, return an empty figure.
        return go.Figure()

    # Convert the app data to a SimResults object.
    sim_results = sim_results_from_dict(app_data)
    q = get_quantiles(
        list(group_sum(dfs, selected_age_groups) for dfs in sim_results.beds_by_age_list)
    )
    fig = gen_plotly(q, title='Bed occupancy for selected age groups')
    return fig


@callback(
    Output('step4-multiselect-age-groups', 'value', allow_duplicate=True),
    Input('step4-button-all-age-groups', 'n_clicks'),
    State('step4-multiselect-age-groups', 'data'),
    prevent_initial_call=True
)
def select_all_age_groups(_, all_keys: list[str]):
    """Select all age groups in the MultiSelect component.  Triggered when the
    'Select all' button is clicked."""
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
