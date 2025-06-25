"""Main module for Step 3 of the stepper: Length-of-stay modelling."""

from time import sleep
from typing import Any
import dash_mantine_components as dmc
import fitter
from dash import Input, Output, State, callback, dcc
from dash_compose import composition
import pandas as pd

from cuh_resp_model.components.back_next import back_next

COMMON_DISTS = fitter.get_common_distributions()


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
            with dmc.Group(align='start'):
                yield dmc.TextInput(
                    id='step3-textinput-age-groups',
                    label='Age group breakpoints',
                    value="16,65",
                    w=200
                )
                yield dmc.Button(
                    'Fit LoS distributions',
                    id='step3-button-fit-los',
                    mt='1.6rem'
                )
                yield dmc.Checkbox(
                    id='step3-checkbox-fit-common-only',
                    label='Common distributions only',
                    checked=True,
                    size='md',
                    mt='1.9rem'
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
    Input('step2-select-starttime-option', 'value')
)
def start_mode_msg(mode: str):
    if mode == 'FirstPosCollected':
        return 'Using time of first postive test as start time for hospital-acquired infections, ' \
            'and admission time for all other infections.  Go back to Step 2 to change this.'
        
    else:
        return 'Using admission time as start time for all cases, including ' \
            'hospital-acquired infections.    Go back to Step 2 to change this.'


@callback(
    Output('step3-box-results', 'children'),
    Input('step3-button-fit-los', 'n_clicks'),
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
def fit_los(_, age_breakpoints: str, common_only: bool, app_data: dict[str, Any]):

    age_breakpoints = '' if not age_breakpoints else age_breakpoints  # Handle None
    age_breakpoints = age_breakpoints.split(',')
    age_breakpoints = [int(age) for age in age_breakpoints]

    stays_df = pd.DataFrame.from_dict(app_data['step1']['stays_df'], orient='tight')
    stays_df.to_feather('stays.feather')
    sleep(2)
    with dmc.Stack(gap=10) as ret:
        yield dmc.Text('LoS fitting results:', size='lg', fw=700)
        yield dcc.Markdown('''\
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam sed malesuada nisi. Nulla cursus
sem euismod tincidunt suscipit. Aliquam posuere eu orci placerat dapibus. Donec vehicula elit in
ipsum hendrerit commodo. Nullam placerat, nulla ut faucibus molestie, ligula nisl faucibus lorem, a
iaculis dui erat at felis. Pellentesque habitant morbi tristique senectus et netus et malesuada...
''')
    return ret
# endregion
