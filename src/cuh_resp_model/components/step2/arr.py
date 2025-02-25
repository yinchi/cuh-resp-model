"""Module for the Daily Arrivals tab of Step 2: Analysis & Model Creation"""

import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, Patch, State, callback, dcc, no_update
from dash_compose import composition
from plotly import graph_objects as go

from cuh_resp_model.components.ids import ID_GRAPH_ARR, ID_STEPPER, ID_STORE_APPDATA


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
        yield poisson_fitter()

    return ret


# region callbacks
#
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
    patched_fig['layout']['title'] = f'{disease_name} cases by first positive test'
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
#
# endregion
