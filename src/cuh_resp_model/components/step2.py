"""Main module for Step 2 of the stepper: Scenario modelling."""

from typing import Any, Literal

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, Patch, State, callback, dcc
from dash_compose import composition
from plotly import graph_objects as go

from cuh_resp_model.components.back_next import back_next

ID_GRAPH = {'themed_graph': True, 'name': 'step2-graph-arrivals'}


# region layout
@composition
def stepper_step():
    """The contents for the Stepper Step 1 in the app."""

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
    """The DMC stack."""

    with dmc.Stack(gap=36) as ret:
        with dmc.Stack(gap=10):
            yield dmc.Text('Start date options:', fw=700, size='lg')
            yield dmc.Text(
                'For community-acquired infections, use the following timestamp as the starting '
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
                value='Admission',
                w=400
            )

        with dmc.Stack(gap=10):
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
            with dmc.Group(align='baseline'):
                # Parameters for a scaled and shifted beta distribution.
                # Note date values are in ISO format even though the display format is different.
                yield dmc.DateInput(id='step2-dateinput-scenario-start',
                                    label='Start date (DD-MM-YYYY)',
                                    valueFormat='DD-MM-YYYY',
                                    value='2025-01-01',
                                    w=200)
                yield dmc.DateInput(id='step2-dateinput-scenario-end',
                                    label='End date (DD-MM-YYYY)',
                                    valueFormat='DD-MM-YYYY',
                                    value='2025-05-01',
                                    w=200)
                yield dmc.DateInput(id='step2-dateinput-scenario-mode',
                                    label='Peak date (DD-MM-YYYY)',
                                    valueFormat='DD-MM-YYYY',
                                    value='2025-03-01',
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
                                      value=10.0, min=0, decimalScale=2,
                                      w=200)
    return ret
# endregion


# region callbacks
@callback(
    Output(ID_GRAPH, 'figure', allow_duplicate=True),
    Input('stepper', 'active'),  # current step
    Input('step2-select-starttime-option', 'value'),  # Admission or FirstPosCollected
    State('store-appdata', 'data'),
    prevent_initial_call=True
)
def render_scenario_graph(
    active_step: int,
    start_date_option: Literal['Admission', 'FirstPosCollected'],
    app_data: dict[str, Any]
):
    if active_step != 1:
        raise dash.exceptions.PreventUpdate

    disease_name: str = app_data['step1']['disease_name']
    stays_df = pd.DataFrame.from_dict(app_data['step1']['stays_df'], orient='tight')

    start_date = stays_df.Admission.copy()

    if start_date_option == 'FirstPosCollected':
        start_date[stays_df.Acquisition.str.startswith('Community')] = \
            stays_df.FirstPosCollected[stays_df.Acquisition.str.startswith('Community')]

    # Original type was pd.Timestamp before to_dict, thus stored in ISO format
    # After from_dict, we need to cast back to pd.Timestamp
    start_date = pd.to_datetime(start_date, format='ISO8601')

    start_date_df = pd.DataFrame(
        {'start': start_date, 'num_cases': 1}
    ).set_index('start').resample('D').count()

    # 7-day rolling average, using end date for x-value
    start_date_df['rolling_avg'] = start_date_df['num_cases'] \
        .rolling(window=7, min_periods=3, center=False).mean()

    patched_fig = Patch()
    patched_fig['layout']['title']['text'] = f'{disease_name} cases by start date'
    patched_fig['data'] = []  # reset plots

    patched_fig['data'].append(
        go.Scatter(
            x=start_date_df.index,
            y=start_date_df.num_cases,
            name='Count',
            line={'width': 0.5}
        )
    )
    patched_fig['data'].append(
        go.Scatter(
            x=start_date_df.index,
            y=start_date_df.rolling_avg,
            name='7-day rolling average',
            # Show a short name and only 4 decimal places for the rolling average
            hovertemplate='7-day avg.: %{y:.4f}<extra></extra>',
            line={'width': 2}
        )
    )

    return patched_fig
# endregion

# region helpers

# endregion
