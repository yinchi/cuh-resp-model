"""Main module for Step 4 of the stepper: Simulation."""

from time import sleep
import dash_mantine_components as dmc
from dash import Input, Output, State, callback, dcc
from dash_compose import composition

from cuh_resp_model.cache import bg_manager
from cuh_resp_model.components.back_next import back_next

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
        yield dcc.Store(id='step3-store', data={})
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 4: Simulate", ta="center", size="xl")
                yield stack()
                yield back_next('btn-stepper-4-to-3', None)
    return ret


@composition
def stack():
    """The DMC stack for Step 3."""

    with dmc.Stack(gap=36) as ret:
        with dmc.Stack(gap=10):
            yield dmc.Text('Configuration', fw=700, size='lg')
            with dmc.Group(m=0):
                yield dmc.Button(
                    'Download configuration (.json)',
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
        yield dmc.Box(id='step4-box-results', display='none')
    return ret
# endregion


# region callbacks
@callback(
    Output('step4-box-results', 'children'),
    Output('step4-box-results', 'display'),
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
    ],
    progress=[
        Output('step4-progress-simulation', 'value'),
        Output('step4-text-progress', 'children'),
    ],
    cancel=[Input('stepper', 'active_step')]  # Cancel if active step changes
)
@composition
def simulate(
    set_progress: callable,
    _,  # n_clicks: int,
    num_reps: int,
    jitter: int,
    app_data: dict[str, any]
):
    """Run the simulation and return the results."""
    for iter in range(1, num_reps+1):
        # Simulate some progress
        sleep(1)
        set_progress((iter / num_reps * 100, f'{iter}/{num_reps}'))

    # Return the results as a box with some text
    with dmc.Stack(gap=10) as ret:
        yield dmc.Text(
            'Simulation results',
            fw=700, size='lg'
        )
        yield dmc.Text(
            f'Placeholder; results to go here.'
        )
    return ret, None
# endregion
