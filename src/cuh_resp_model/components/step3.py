import dash_mantine_components as dmc
import fitter
from dash import dcc
from dash_compose import composition

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
            yield dmc.Text('Define age groups:', fw=700, size='lg')
            yield dcc.Markdown('''\
Enter a list of age breakpoints, separated by commas.  For example, `16,65` creates three
age groups, 0-15, 16-64, and 65+.  Leaving the input below blank creates a single age group
for all patients.

Selecting "Common distributions only" will attempt only the common distribution types as defined
by the
[`fitter`](https://fitter.readthedocs.io/en/latest/faqs.html#what-are-the-distributions-available)
Python module.  To reduce computation time, it is recommended to leave this option checked.
''')
            with dmc.Group(align='start'):
                yield dmc.TextInput(
                    id='step3-textinput-age-groups',
                    label='Age group breakpoints',
                    value="16,65",
                    w=200
                )
                yield dmc.Button(
                    'Fit LoS distributions',
                    mt='1.6rem'
                )
                yield dmc.Checkbox(
                    label='Common distributions only',
                    checked=True,
                    size='md',
                    mt='1.9rem'
                )
    return ret
