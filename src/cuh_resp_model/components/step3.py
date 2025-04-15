"""Module for the Daily Arrivals tab of Step 3: Patient Length-of-Stay Modelling"""

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, Patch, State, callback, clientside_callback, dcc
from dash_compose import composition
from plotly import graph_objects as go

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


@composition
def stepper_step():
    """The contents for the Stepper Step 3 in the app."""
    go_layout = {
        'width': 1000,
        'height': 300,
        'title': 'Length of stay [days]',
        'legend': {'y': 0.5, 'font_size': 12},
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
    placeholder_table_data = {
        "head": ["Placeholder"],
        "body": [[0]]
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
                with dmc.Card(withBorder=True):
                    yield dmc.Text('0-15 Age group', size='xl', fw=700)
                    with dmc.Stack():
                        yield dcc.Graph(
                            id=ID_GRAPH_PAEDS,
                            figure=go.Figure(layout=go_layout)
                        )
                        yield dmc.Text('Distribution fitting results', fw=700)
                        yield dmc.Table(
                            **table_opts,
                            data=placeholder_table_data
                        )
                        yield dmc.Select(
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
                        yield dmc.Table(
                            **table_opts,
                            data=placeholder_table_data
                        )
                        yield dmc.Select(
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
                        yield dmc.Table(
                            **table_opts,
                            data=placeholder_table_data
                        )
                        yield dmc.Select(
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
    prevent_initial_call=True
)
def stepper_next(_, data, curr_state):
    """Process app data for Step 2 and proceed to Step 3."""

    return curr_state + 1, dash.no_update


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
    print(los_df)

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
#
# endregion
