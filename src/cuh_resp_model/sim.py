"""Simulation module for the CUH Respiratory Model."""

import random
from datetime import datetime
from typing import Any, Callable, NamedTuple

import pandas as pd
import plotly.graph_objects as go
import salabim as s
from scipy import stats


# Note that in the frontend, our age groups have names like 'Age >= 0 and Age < 16',
# but in the backend, we only use indices.
class PatientData(NamedTuple):
    """Data structure to hold patient information."""
    age_group_idx: int
    """Index of the age group for the patient.  Corresponds to the row index in the
    age distribution DataFrame."""
    los: float
    """Length of stay (LOS) for the patient in days."""


def rand_patient(age_df: pd.DataFrame) -> PatientData:
    """Generate random patient data based on age distribution, including the age group index
    and length of stay (LOS).

    Args:
        age_df (pd.DataFrame):
            DataFrame containing age distribution data.  The columns include:
            - 'ratio': Proportion of patients in each age group.
            - 'dist_type': Type of distribution (e.g., 'norm', 'gamma').
            - 'dist_params': Parameters for the distribution, as a dict.

    Returns:
        PatientData: A namedtuple containing:
            - 'los': Randomly selected length of stay (LOS) value.
            - 'age_group_idx': Index of the selected age group.
    """

    age_ratios = age_df['ratio'].to_list()
    age_dist_types = age_df['dist_type'].to_list()
    age_dist_params = age_df['dist_params'].to_list()

    dists = []
    for dist_name, dist_params in zip(age_dist_types, age_dist_params):
        dist = getattr(stats, dist_name)(**dist_params)
        dists.append(dist)

    idx = random.choices(range(len(age_ratios)), weights=age_ratios, k=1)[0]
    val = dists[idx].rvs()
    return PatientData(age_group_idx=idx, los=val)


class Patient(s.Component):
    """Represents a patient in the simulation."""

    def setup(  # pylint: disable=arguments-differ,pointless-string-statement
        self, data: PatientData
    ):
        """Initialize the patient with a random length of stay and age group index."""

        self.los = data.los
        """Length of stay (LOS) for the patient in days."""

        self.age_group_idx = data.age_group_idx
        """Index of the age group for the patient.  Corresponds to the row index in the
        age distribution DataFrame.  See also: `PatientGenerator.setup()`."""

    def process(self):
        """Process the patient by claiming a bed for the duration of their stay."""
        # Resources are used as counters of occupied beds, thus
        # we claim both a global bed resource and a specific age group bed resource.
        self.request(self.env.beds)
        self.request(self.env.beds_by_age[self.age_group_idx])

        self.hold(self.los)  # Hold for the length of stay
        self.release()  # Release all resources claimed by this patient


class PatientGenerator(s.Component):
    """Generates patients based on a scenario DataFrame and age distribution DataFrame."""

    def setup(    # pylint: disable=arguments-differ,pointless-string-statement
        self,
        scenario_df: pd.DataFrame,
        age_df: pd.DataFrame,
        jitter: float = 0.2
    ):
        """Initialize generator parameters."""

        self.scenario_df = scenario_df
        """Scenario DataFrame containing patient arrival data.  Columns include
        the date and number of patients to generate for that date."""

        self.age_df = age_df
        """Age distribution DataFrame containing age group ratios and distribution parameters."""

        self.jitter = jitter
        """Jitter factor to add randomness to patient generation."""

    def process(self):
        """Generate patients based on the scenario DataFrame."""
        for _, row in self.scenario_df.iterrows():

            y = row['y']  # Number of patients to generate for this date
            y *= random.uniform(1 - self.jitter, 1 + self.jitter)  # Apply jitter
            y = round(max(0, y))  # Ensure non-negative integer number of patients

            for _ in range(y):
                delay = self.env.days(random.uniform(0, 1))
                Patient(
                    # salabim parameters
                    env=self.env,
                    delay=delay,  # Delay before the patient is processed (enters the system)

                    # setup() parameter
                    data=rand_patient(self.age_df),
                )

            # Wait for one day before generating the next batch of patients
            self.hold(self.env.days(1))


def sim_once(
    scenario_df: pd.DataFrame,
    age_df: pd.DataFrame,
    jitter: float = 0.2,
    extra_days: int = 25
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Simulate bed occupancy based on the patient arrivals scenario and age distribution.

    Args:
        scenario_df (pd.DataFrame):
            DataFrame containing patient arrival data.  Columns include:
            - 'date': Date of patient arrivals. (datetime, not str)
            - 'y': Number of patients to generate for that date.
        age_df (pd.DataFrame):
            DataFrame containing age distribution data.  The columns include:
            - 'query': Age group query (e.g., 'Age >= 0 and Age < 16').
            - 'ratio': Proportion of patients in each age group.
            - 'dist_type': Type of distribution (e.g., 'norm', 'gamma').
            - 'dist_params': Parameters for the distribution, as a dict.
        jitter (float):
            Jitter factor to add randomness to patient generation.  Default is 0.2 (20%).
        extra_days (int):
            Number of extra days to run the simulation beyond the last date in the
            scenario DataFrame.

    Returns:
        tuple: A tuple containing:
            - beds_df (pd.DataFrame): DataFrame with timestamps and occupied beds.
            - beds_df_by_age (dict): Dictionary mapping age group queries to DataFrames
              with timestamps and occupied beds for each age group.
    """
    env = s.Environment(time_unit='days', datetime0=scenario_df['date'].min(), random_seed='*')

    # Use infinite-capacity resource as counter of occupied beds
    env.beds = s.Resource('Beds', env=env, capacity=s.inf)
    env.beds_by_age = [
        s.Resource(f'Beds for age group {i}', env=env, capacity=s.inf)
        for i in range(len(age_df))
    ]

    # Create the patient generator
    env.patients = PatientGenerator(
        env=env, scenario_df=scenario_df, age_df=age_df, jitter=jitter
    )

    # Run until the last date in the scenario DataFrame
    till = scenario_df['date'].max() + pd.Timedelta(days=extra_days)
    env.run(till=env.datetime_to_t(till))

    # Collect the results for overall bed occupancy
    beds_df: pd.DataFrame = env.beds.claimed_quantity.as_dataframe()
    beds_df.columns = ['t', 'occupied_beds']
    beds_df['timestamp'] = beds_df.t.map(env.t_to_datetime)  # float to datetime
    beds_df = beds_df[['timestamp', 'occupied_beds']]
    beds_df = beds_df.set_index('timestamp', drop=True).sort_index()\
        .resample('1D').max().ffill()  # Daily max occupancy, forward fill missing values

    beds_dfs_by_age = {}

    for i in range(age_df.shape[0]):
        # Collect the results for each age group
        df = env.beds_by_age[i].claimed_quantity.as_dataframe()
        df.columns = ['t', 'occupied_beds']
        df['timestamp'] = df.t.map(env.t_to_datetime)  # float to datetime
        df = df[['timestamp', 'occupied_beds']]
        df = df.set_index('timestamp', drop=True).sort_index()\
            .resample('1D').max().ffill()  # Daily max occupancy, forward fill missing values

        # Use the age group query as the key in the dictionary
        beds_dfs_by_age[age_df['query'][i]] = df

    return beds_df, beds_dfs_by_age


class SimResults(NamedTuple):
    """Results of a simulation with multiple runs."""

    overall_beds_list: list[pd.DataFrame]
    """List of DataFrames with timestamps and occupied beds for each run."""
    beds_by_age_list: list[dict[str, pd.DataFrame]]
    """List of dictionaries mapping age group queries to DataFrames with timestamps
    and occupied beds for each age group in each run."""


def sim_results_to_dict(sim_results):
    """
    Convert the overall beds list from sim_results to a dictionary format.
    The index is converted to ISO format for better readability.
    """

    def df_to_dict(df):
        df = df.copy()
        df.index = df.index.map(datetime.isoformat)  # Convert index to ISO format
        return df.to_dict(orient='dict')['occupied_beds']

    _overall_beds_list = [
        df_to_dict(df) for df in sim_results.overall_beds_list
    ]

    _beds_by_age_list = [
        {g: df_to_dict(d[g]) for g in d}
        for d in sim_results.beds_by_age_list
    ]

    return {
        'overall_beds_list': _overall_beds_list,
        'beds_by_age_list': _beds_by_age_list
    }


def sim_results_from_dict(sim_results_dict):
    """
    Convert a dictionary back to sim_results format.
    The index is converted from ISO format back to datetime.
    Inverse of `sim_results_to_dict`.
    """

    def dict_to_df(d):
        df = pd.DataFrame({'occupied_beds': d})
        df.index = pd.to_datetime(df.index, format='ISO8601')  # Convert index back to datetime
        return df

    overall_beds_list = [dict_to_df(d) for d in sim_results_dict['overall_beds_list']]
    beds_by_age_list = [
        {g: dict_to_df(d[g]) for g in d} for d in sim_results_dict['beds_by_age_list']
    ]

    return SimResults(overall_beds_list=overall_beds_list, beds_by_age_list=beds_by_age_list)


def sim(
    scenario_df: pd.DataFrame,
    age_df: pd.DataFrame,
    n_runs: int = 30,
    jitter: float = 0.2,
    extra_days: int = 25,
    set_progress: Callable[[int], Any] = None
) -> SimResults:
    """Run multiple simulations and collect results.

    Args:
        scenario_df (pd.DataFrame):
            DataFrame containing patient arrival data.
        age_df (pd.DataFrame):
            DataFrame containing age distribution data.
        n_runs (int):
            Number of simulation runs to perform.  Default is 30.
        jitter (float):
            Jitter factor to add randomness to patient generation.  Default is 0.2 (20%).
        extra_days (int):
            Number of extra days to run the simulation beyond the last date in the
            scenario DataFrame.

    Returns:
        SimResults: A named tuple containing:
            - 'beds_df': List of DataFrames with timestamps and occupied beds for each run.
            - 'beds_df_by_age': List of dictionaries mapping age group queries to DataFrames
              with timestamps and occupied beds for each age group in each run.
    """

    overall_beds_list = []
    beds_by_age_list = []

    for i in range(n_runs):
        beds_df, beds_by_age = sim_once(
            scenario_df=scenario_df,
            age_df=age_df,
            jitter=jitter,
            extra_days=extra_days
        )
        overall_beds_list.append(beds_df)
        beds_by_age_list.append(beds_by_age)
        set_progress((
            (i + 1) / n_runs * 100,  # Progress, convert to percentage
            f'{i + 1}/{n_runs}'  # Text display, e.g. '1/30'
        ))

    return SimResults(
        overall_beds_list=overall_beds_list,
        beds_by_age_list=beds_by_age_list
    )


QUANTILES = [0.1, 0.25, 0.5, 0.75, 0.9]


def get_quantiles(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Compute quantiles for a list of DataFrames.

    Args:
        dfs (list[pd.DataFrame]): List of DataFrames to compute quantiles for.

    Returns:
        pd.DataFrame: DataFrame containing the quantiles for each input DataFrame.
    """

    # Our dataframes have a timestamp index and a single column 'occupied_beds'.
    # Concatenate them along the columns axis.  Since we are considering bed occupancy
    # by date, use ffill to handle missing values.
    combined_df = pd.concat(dfs, axis=1, join='outer').ffill()
    combined_df.columns = [f'run_{i}' for i in range(len(dfs))]
    quantiles = combined_df.quantile(QUANTILES, axis=1).T
    return quantiles


def gen_plotly(quantiles: pd.DataFrame, title: str = 'Bed Occupancy Quantiles') -> dict:
    """Generate a Plotly figure from quantiles DataFrame.

    Args:
        quantiles (pd.DataFrame): DataFrame containing quantiles.
        title (str): Title of the plot.  Default is 'Bed Occupancy Quantiles'.

    Returns:
        dict: Plotly figure.
    """

    fig = go.Figure()

    # fill between lower and upper deciles
    fig.add_trace(go.Scatter(
        x=quantiles.index,
        y=quantiles[0.1],
        name='lower decile',
        line={'width': 0},
        legend=None
    ))
    fig.add_trace(go.Scatter(
        x=quantiles.index,
        y=quantiles[0.9],
        name='upper decile',
        fillcolor='rgba(127, 127, 255, 0.3)',  # Fill color with transparency
        fill='tonexty',
        line={'width': 0},
        legend=None
    ))

    # # fill between lower and upper quartiles
    fig.add_trace(go.Scatter(
        x=quantiles.index,
        y=quantiles[0.25],
        name='lower quartile',
        line={'width': 0},
        legend=None
    ))
    fig.add_trace(go.Scatter(
        x=quantiles.index,
        y=quantiles[0.75],
        name='upper quartile',
        fillcolor='rgba(0, 0, 255, 0.5)',  # Fill color with transparency
        fill='tonexty',
        line={'width': 0},
        legend=None
    ))

    # median line
    fig.add_trace(go.Scatter(
        x=quantiles.index,
        y=quantiles[0.5],
        mode='lines',
        name='median',
        line=dict(color='black', width=2),
        legend=None
    ))

    fig.update_layout(
        title=title,
        title_font_weight='bold',
        title_font_size=20,
        xaxis_title='Date',
        yaxis_title='Occupied Beds',
        legend_title='Quantiles',
        height=400,
        width=1000,
        legend_y=0.5,
        hovermode='x unified',
    )
    return fig
