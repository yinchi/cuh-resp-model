"""Module for the Daily Arrivals tab of Step 3: Patient Length-of-Stay Modelling"""

import json
from copy import deepcopy
from math import isnan

import dash
import dash_mantine_components as dmc
import pandas as pd
import salabim as sim
from dash import Input, Output, State, callback, clientside_callback, dcc
from dash_compose import composition
from numpy.random import normal
from plotly import graph_objects as go
from scipy import stats

from cuh_resp_model.components.ids import *

from ..cache import bg_manager
from ..components.back_next import back_next


@composition
def stepper_step():
    """The contents for the Stepper Step 4 in the app."""
    with dmc.StepperStep(
        None,
        label="Simulate!"
    ) as ret:
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 4: Simulate disease scenario", ta="center", size="xl")
                with dmc.Stack():
                    with dmc.Group(gap='sm'):
                        yield dmc.Button(id=ID_CONFIG_DOWNLOAD_BTN, children="Download config")
                        yield dcc.Download(id=ID_CONFIG_DOWNLOAD)
                with dmc.Stack(gap='sm'):
                    yield dmc.Text("Simulation Results", size='xl')
                    with dmc.Stack(id=ID_SIM_RESULTS, pos="relative"):
                        yield dmc.LoadingOverlay(
                            id=ID_OVERLAY_SIM_RESULTS,
                            visible=True,
                            overlayProps={"radius": "sm", "blur": 2}
                        )
                        yield dmc.Stack(h=600)
                yield back_next(ID_STEPPER_BTN_4_TO_3, None)
    return ret


# region callbacks
#

# Go back to Step 3: LoS modelling.
clientside_callback(
    """(step, state) => state - 1""",
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Input(ID_STEPPER_BTN_4_TO_3, "n_clicks"),
    State(ID_STEPPER, "active"),
    prevent_initial_call=True
)


@callback(
    Output(ID_CONFIG_DOWNLOAD, 'data'),
    Input(ID_CONFIG_DOWNLOAD_BTN, 'n_clicks'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True
)
def download_config(_, data):
    """Send the simulation config when the Download button is pressed."""
    ret = deepcopy(data)
    del ret['step_1']['los_data']  # not needed to run simulation or plot results
    return dcc.send_string(
        json.dumps(ret, sort_keys=False),
        filename='config.json'
    )


@callback(
    Output(ID_SIM_RESULTS, 'children', allow_duplicate=True),
    Input(ID_STEPPER, 'active'),
    State(ID_STORE_APPDATA, 'data'),
    prevent_initial_call=True,
    background=True,
    manager=bg_manager
)
def gen_bed_forecasts(active_step, app_data: dict):
    """Render the LoS graphs for the three age groups."""

    if active_step != 3:  # Step 4
        return dash.no_update

    df_arr = pd.DataFrame({
        'date': app_data['step_2']['xs'],
        'n_arr': app_data['step_2']['ys']
    })
    df_arr

    # Get the simulation end, i.e. midnight one day after the last day in `df_arr`
    sim_end = pd.Timestamp(list(df_arr.date)[-1]) + pd.Timedelta(days=1)

    def get_dist(group: str):
        n = app_data['step_3']['selected_dists']['paeds']
        params = app_data['step_3']['dists']['paeds'][n]
        return getattr(stats, n)(**params)
    
    dist_paeds = get_dist('paeds')
    dist_adult = get_dist('adult')
    dist_senior = get_dist('senior')
    age_dist = app_data['step_3']['age_dist']

    patient_params = {
        'dist_paeds': dist_paeds,
        'dist_adult': dist_adult,
        'dist_senior': dist_senior,
        'age_dist': age_dist 
    }

    df_total, df_adult, df_paeds = simulate(
        df_arr,
        until=sim_end,
        patient_params=patient_params
    )

    fig_total = gen_figure(df_total, title='Total beds')
    fig_adult = gen_figure(df_adult, title='Adult beds')
    fig_paeds = gen_figure(df_paeds, title='Paeds beds')

    return [
        dcc.Graph(figure=fig_total),
        dcc.Graph(figure=fig_adult),
        dcc.Graph(figure=fig_paeds),
    ]
#
# endregion


# region helper functions
#
def simulate(
        df_arr: pd.DataFrame,
        until: pd.Timedelta,
        patient_params: dict
):
    """Run the simulation multiple times and concatenate the results."""
    dfs = []
    dfs_adult = []
    dfs_paeds = []

    for _ in range(30):
        result = simulate_once(
            df_arr,
            until=until,
            patient_params=patient_params
        )
        dfs.append(result['total'])
        dfs_paeds.append(result['paeds'])
        dfs_adult.append(result['adult'])

        df = pd.concat(dfs, axis=1)
        df_adult = pd.concat(dfs_adult, axis=1)
        df_paeds = pd.concat(dfs_paeds, axis=1)

    return df, df_adult, df_paeds


def simulate_once(
    df_arr: pd.DataFrame,
    until: pd.Timestamp,
    patient_params: dict
):
    """The respirator disease model simulation."""
    env = Environment(time_unit='days', datetime0=df_arr.date[0], random_seed='*')
    DailyArrivals(env=env, n_arr = df_arr.n_arr, patient_params=patient_params)

    env.run(env.datetime_to_t(until))

    beds_df = env.beds.claimed_quantity.as_dataframe().set_index('t')
    beds_paeds_df = env.beds_paeds.claimed_quantity.as_dataframe().set_index('t')
    beds_adult_df = env.beds_adult.claimed_quantity.as_dataframe().set_index('t')

    beds_df.index = beds_df.index.map(env.t_to_datetime)
    beds_paeds_df.index = beds_paeds_df.index.map(env.t_to_datetime)
    beds_adult_df.index = beds_adult_df.index.map(env.t_to_datetime)

    beds_df = beds_df.resample('1D').max().ffill()
    beds_paeds_df = beds_paeds_df.resample('1D').max().ffill()
    beds_adult_df = beds_adult_df.resample('1D').max().ffill()

    return {
        'total': beds_df, 'paeds': beds_paeds_df, 'adult': beds_adult_df
    }


class Environment(sim.Environment):
    """The simulation environment"""
    beds: sim.Resource

    # Use virtual resources as counters for different types of bed occupancies
    beds_adult: sim.Resource
    beds_paeds: sim.Resource

    def setup(self):
        self.beds = sim.Resource('beds', capacity=sim.inf, env=self)
        self.beds_adult = sim.Resource('beds', capacity=sim.inf, env=self)
        self.beds_paeds = sim.Resource('beds', capacity=sim.inf, env=self)


class DailyArrivals(sim.Component):
    """Daily Arrival generator."""

    n_arr: list[float]
    patient_params: dict

    def setup(self, n_arr, patient_params):
        self.n_arr = n_arr
        self.patient_params = patient_params

    def process(self):
        """Generate patients. Patients are batch-generated each day; each Patient instance
        is responsible for entering the system at the correct time-of-day using
        `Patient.hold()`."""
        JITTER = 0.05 # Add 5% jitter to simulation arrivals

        for n_cases in self.n_arr:
            n = round(n_cases * normal(1.0, JITTER))
            for _ in range(n):
                Patient(**self.patient_params)
            self.hold(self.env.days(1.0))


class Patient(sim.Component):
    """A patient in the respiratory disease model."""

    def process(self, dist_paeds, dist_adult, dist_senior, age_dist):
        """Model a patient journey through the ward."""
        self.env: Environment
        u01 = sim.Uniform(0, 1)

        # Arrivals are generated at midnight but released to the system at a random time of day
        self.hold(self.env.days(u01))

        is_paeds = False
        if (r := u01()) < age_dist['paeds']:
            is_paeds = True
            los = dist_paeds.rvs()
        elif r < age_dist['paeds'] + age_dist['adult']:
            los = dist_adult.rvs()
        else:
            los = dist_senior.rvs()
        
        assert not isnan(los), 'LOS is nan'
        los = max(0, los)  # Clip to bounds

        self.request(self.env.beds)  # 1 hold
        self.request(self.env.beds_paeds if is_paeds else self.env.beds_adult)  # 2 holds
        self.hold(los)
        self.release(self.env.beds_paeds if is_paeds else self.env.beds_adult)  # 1 holds
        self.release(self.env.beds)  # 0 holds


def gen_figure(df: pd.DataFrame, title: str):
    """Plot simulation results."""
    go_layout = {
        'width': 1000,
        'height': 300,
        'title': title,
        'legend_y': 0.5,
        'legend_font_size': 14,
        'title_font_size': 20,
        'xaxis': {'tickfont': {'size': 14}},
        'yaxis': {'tickfont': {'size': 14}},
        'title_font_weight': 900
    }

    x = list(df.index)

    y_lo = list(df.quantile(0.1, axis=1))
    y_hi = list(df.quantile(0.9, axis=1))
    fig = go.Figure(layout=go_layout)
    fig.add_trace(go.Scatter(
        x=x+x[::-1],
        y=y_hi+y_lo[::-1],
        fill='toself',
        fillcolor='rgba(231,107,243,0.3)',
        line_color='rgba(255,255,255,0)',
        name='lower/upper deciles',
    ))


    y_lo = list(df.quantile(0.25, axis=1))
    y_hi = list(df.quantile(0.75, axis=1))
    fig.add_trace(go.Scatter(
        x=x+x[::-1],
        y=y_hi+y_lo[::-1],
        fill='toself',
        fillcolor='rgba(231,107,243,0.5)',
        line_color='rgba(255,255,255,0)',
        name='lower/upper quartiles',
    ))

    fig.add_trace(go.Scatter(
        x=x, y=list(df.quantile(0.5, axis=1)),
        line_color='rgb(80,0,80)',
        name='Median'
    ))

    return fig
#
# endregion