"""Main module for Step 1 of the stepper: Upload files."""

import json
from base64 import b64decode
from io import BytesIO
from pathlib import Path
from typing import Any

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, callback, clientside_callback, dcc
from dash_compose import composition
from dash_iconify import DashIconify

from cuh_resp_model.components.back_next import back_next
from cuh_resp_model.utils import JSCode, read_file

MODULE_ROOT = Path(__file__).parent.parent
DISEASE_OPTIONS = ['COVID-19', 'Influenza', 'RSV']


TEXT_STAYS_HOVERCARD = '''\
Please upload an .xlsx or .csv file.

**Expected columns**: Refer to the example .xlsx file (green button) for minimum set of columns.
Extra columns are ignored.

**Acquisition column**: if the value in this column starts with 'Hospital', the admission time is
replaced by the time of the first positive test (FirstPosCollected column) for the purpose of
computing the stay length.
'''


TEXT_OCCUPANCY_HOVERCARD = '''\
Please upload an .xlsx or .csv file.

**Expected columns**:

- Date: DD-MM-YYYY format preferred
- Critical care: integer
- Non critical care: integer

For a minimal example, refer to the example .xlsx file (green button).
'''


# region layout
@composition
def stepper_step():
    """The contents for the Stepper Step 1 in the app."""

    with dmc.StepperStep(
        None,
        label="Upload files",
        description=dmc.Text(
            "Upload patient stay & occupancy records", size="xs")
    ) as ret:
        yield dcc.Store(id='step1-store', data={})
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 1: Upload Files", ta="center", size="xl")
                yield stack()
                yield back_next(None, 'btn-stepper-1-to-2')
    return ret


@composition
def stack():
    """The DMC stack."""

    with dmc.Stack(gap=36) as ret:
        with dmc.Stack(gap=10):
            yield dmc.Text('Name of respiratory illness:', fw=700, size='lg')
            yield dmc.Select(
                id='step1-select-disease-name',
                label='Select from dropdown or select "Other" to enter a custom name:',
                data=DISEASE_OPTIONS + ['Other'],
                value='COVID-19',
                w=400
            )
            yield dmc.TextInput(
                id='step1-textInput-disease-name-other',
                placeholder='Enter disease name',
                w=400
            )
        with dmc.Stack(gap=10):
            with dmc.Group(gap=5, align='baseline'):
                yield dmc.Text('Upload patient stay data', fw=700, size='lg')
                with dmc.HoverCard(
                    position='top-start',
                    withArrow=True,
                    width=400,
                    shadow='md',
                ):
                    with dmc.HoverCardTarget([]):
                        yield DashIconify(
                            icon='material-symbols:info-outline',
                            width=20,
                        )
                    with dmc.HoverCardDropdown([], bg='#ffffaa', c='black'):
                        yield dcc.Markdown(TEXT_STAYS_HOVERCARD)
            with dmc.Group(align='baseline'):
                yield dmc.Button(
                    'Download example .xlsx file',
                    id='step1-button-download-stays-example',
                    color='teal'
                )
                yield dcc.Download(id='step1-download-stays-example')
                with dash.dcc.Upload(
                    id='step1-upload-stays',
                    accept='.xlsx'
                ):
                    with dmc.Button([], id='step1-button-upload-stays'):
                        yield 'Upload'
                        yield dmc.Loader(id='step1-loader-upload-stays',
                                         size='sm', ms='sm', color='white', display='none')
                yield dmc.Text(
                    'No file uploaded.',
                    id='step1-text-upload-stays-info',
                    c='red'
                )
        with dmc.Stack(gap=10):
            with dmc.Group(gap=5, align='baseline'):
                yield dmc.Text('Upload occupancy data', fw=700, size='lg')
                with dmc.HoverCard(
                    position='top-start',
                    withArrow=True,
                    width=400,
                    shadow='md',
                ):
                    with dmc.HoverCardTarget([]):
                        yield DashIconify(
                            icon='material-symbols:info-outline',
                            width=20,
                        )
                    with dmc.HoverCardDropdown([], bg='#ffffaa', c='black'):
                        yield dcc.Markdown(TEXT_OCCUPANCY_HOVERCARD)
            with dmc.Group(align='baseline'):
                yield dmc.Button(
                    'Download example .xlsx file',
                    id='step1-button-download-occupancy-example',
                    color='teal'
                )
                yield dcc.Download(id='step1-download-occupancy-example')
                with dash.dcc.Upload(
                    id='step1-upload-occupancy',
                    accept='.xlsx'
                ):
                    with dmc.Button([], id='step1-button-upload-occupancy'):
                        yield 'Upload'
                        yield dmc.Loader(id='step1-loader-upload-occupancy',
                                         size='sm', ms='sm', color='white', display='none')
                yield dmc.Text(
                    'No file uploaded.',
                    id='step1-text-upload-occupancy-info',
                    c='red'
                )
    return ret
# endregion


# region callbacks
TOGGLE_OTHER_INPUT: JSCode = \
    read_file(Path(__file__).parent.resolve() / "js/toggle_other_input.js")

clientside_callback(
    TOGGLE_OTHER_INPUT,
    Output('step1-textInput-disease-name-other', 'display'),
    Input('step1-select-disease-name', 'value')
)


@callback(
    Output('step1-download-stays-example', 'data'),
    Input('step1-button-download-stays-example', 'n_clicks'),
    prevent_initial_call=True
)
def download_stays_example(_):
    """Triggered when user clicks Download button for patient stay data example .xlsx."""
    path = MODULE_ROOT / 'assets/stays_example.xlsx'
    return dcc.send_file(path.resolve())


@callback(
    Output('step1-download-occupancy-example', 'data'),
    Input('step1-button-download-occupancy-example', 'n_clicks'),
    prevent_initial_call=True
)
def download_occupancy_example(_):
    """Triggered when user clicks Download button for bed occupancy data example .xlsx."""
    path = MODULE_ROOT / 'assets/occupancy_example.xlsx'
    return dcc.send_file(path.resolve())


@callback(
    Output('step1-store', 'data', allow_duplicate=True),
    Output('step1-text-upload-stays-info', 'children'),
    Output('step1-text-upload-stays-info', 'c'),
    Input('step1-upload-stays', 'contents'),
    State('step1-upload-stays', 'filename'),
    State('step1-store', 'data'),
    prevent_initial_call=True,
    running=[
        (Output('step1-loader-upload-stays', 'display'), None, 'none'),
        (Output('step1-button-upload-stays', 'disabled'), True, False)
    ]
)
def upload_stays(contents: str, filename: str, step_data: dict[str, Any]):
    """Triggered when user uploads file for patient stays data."""
    if contents is None:
        info = 'No file uploaded.'
        color = 'red'
        los_df = None
    elif not (filename.endswith('.xlsx') or filename.endswith('.csv')):
        info = 'File extension must match one of: .xlsx, .csv'

    # Read the patient stays dataframe
    try:
        los_df = extract_df(contents, filename)

        # TODO validate dataframe (check columns and types)
        assert 'Age' in los_df.columns, \
            'Expected column "Age" not found.'
        assert 'Admission' in los_df.columns, \
            'Expected column "Admission" not found.'
        assert 'Discharge' in los_df.columns, \
            'Expected column "Discharge" not found.'
        assert 'ReAdmission' in los_df.columns, \
            'Expected column "ReAdmission" not found.'
        assert 'ReAdmissionDischarge' in los_df.columns, \
            'Expected column "ReAdmissionDischarge" not found.'
        assert 'FirstPosCollected' in los_df.columns, \
            'Expected column "FirstPosCollected" not found.'
        assert 'Acquisition' in los_df.columns, \
            'Expected column "Acquisition" not found.'

        assert pd.api.types.is_numeric_dtype(los_df.Age), \
            'Column "Age" must be of numeric type.'
        assert pd.api.types.is_datetime64_dtype(los_df.Admission), \
            'Column "Admission" must be of datetime type.'
        assert pd.api.types.is_datetime64_dtype(los_df.Discharge), \
            'Column "Discharge" must be of datetime type.'
        assert pd.api.types.is_datetime64_dtype(los_df.ReAdmission), \
            'Column "ReAdmission" must be of datetime type.'
        assert pd.api.types.is_datetime64_dtype(los_df.ReAdmissionDischarge), \
            'Column "ReAdmissionDischarge" must be of datetime type.'
        assert pd.api.types.is_datetime64_dtype(los_df.FirstPosCollected), \
            'Column "FirstPosCollected" must be of datetime type.'

        # Ensure string type
        los_df.Acquisition = los_df.Acquisition.astype(str)

        # Drop all other columns
        los_df = los_df[['Age', 'Admission', 'Discharge', 'ReAdmission',
                         'ReAdmissionDischarge', 'FirstPosCollected', 'Acquisition']]

        # Drop non-admitted patients
        los_df = los_df.loc[pd.notna(los_df.Admission), :]

        info = f'Successfully parsed "{filename}".'
        color = 'green'
    except pd.errors.EmptyDataError:
        info, color, los_df = f'File "{filename}" is empty.', 'red', None
    except AssertionError as e:
        info, color, los_df = str(e), 'red', None
    except Exception:
        info, color, los_df = f'Could not extract table from "{filename}".', 'red', None

    # Return values
    step_data['stays_df'] = los_df.to_dict(orient='tight') if los_df is not None else None
    return step_data, info, color


@callback(
    Output('step1-store', 'data', allow_duplicate=True),
    Output('step1-text-upload-occupancy-info', 'children'),
    Output('step1-text-upload-occupancy-info', 'c'),
    Input('step1-upload-occupancy', 'contents'),
    State('step1-upload-occupancy', 'filename'),
    State('step1-store', 'data'),
    prevent_initial_call=True,
    running=[
        (Output('step1-loader-upload-occupancy', 'display'), None, 'none'),
        (Output('step1-button-upload-occupancy', 'disabled'), True, False)
    ]
)
def upload_occupancy(contents: str, filename: str, step_data: dict[str, Any]):
    """Triggered when user uploads file for occupancy data."""
    if contents is None:
        info = 'No file uploaded.'
        color = 'red'
        occupancy_df = None
    elif not (filename.endswith('.xlsx') or filename.endswith('.csv')):
        info = 'File extension must match one of: .xlsx, .csv'

    # Read the patient occupancy dataframe
    try:
        occupancy_df = extract_df(contents, filename)

        # Validate dataframe (check columns and types)
        assert 'Date' in occupancy_df.columns, \
            'Expected column not found: "Date"'
        assert 'Critical Care' in occupancy_df.columns, \
            'Expected column not found: "Critical Care"'
        assert 'Non Critical Care' in occupancy_df.columns, \
            'Expected column not found: "Non Critical Care"'

        assert pd.api.types.is_datetime64_dtype(occupancy_df.Date), \
            'Column "Date" must be of datetime type'
        assert pd.api.types.is_integer_dtype(occupancy_df['Critical Care']), \
            'Column "Critical Care" must be of integer type'
        assert pd.api.types.is_integer_dtype(occupancy_df['Non Critical Care']), \
            'Column "Non Critical Care" must be of integer type'

        # Rename columns for easier handling in Python
        occupancy_df.rename(
            inplace=True,
            columns={
                'Date': 'date',
                'Critical Care': 'critical',
                'Non Critical Care': 'noncritical'
            }
        )

        info = f'Successfully parsed "{filename}".'
        color = 'green'
    except pd.errors.EmptyDataError:
        info, color, occupancy_df = f'File "{filename}" is empty.', 'red', None
    except AssertionError as e:
        info, color, occupancy_df = str(e), 'red', None
    except Exception:
        info, color, occupancy_df = f'Could not extract table from "{filename}".', 'red', None

    # Return values
    step_data['occupancy_df'] = (
        occupancy_df.to_dict(orient='tight') if occupancy_df is not None else None
    )
    return step_data, info, color


@callback(
    Output('stepper', 'active'),
    Output('store-appdata', 'data'),
    Output('modal-validation-error', 'opened'),
    Output('text-validation-error', 'children'),
    Input('btn-stepper-1-to-2', 'n_clicks'),
    State('step1-select-disease-name', 'value'),
    State('step1-textInput-disease-name-other', 'value'),
    State('step1-store', 'data'),
    State('store-appdata', 'data'),
    prevent_initial_call=True
)
def next_step(_, d_name: str, d_name_other: str,
              step1_data: dict[str, Any], app_data: dict[str, Any]):
    """Validate inputs for Step 1 and proceed to Step 2 if okay."""

    disease_name = d_name_other if d_name == 'Other' else d_name
    disease_name = '' if disease_name is None else str(disease_name).strip()

    try:
        assert disease_name != '', 'Disease name cannot be empty if "Other" is selected.'
        assert 'stays_df' in step1_data, 'Patient stay data not loaded.'
        assert 'occupancy_df' in step1_data, 'Occupancy data not loaded.'
    except AssertionError as e:
        return dash.no_update, dash.no_update, True, str(e)

    # Update the main data store for the web app
    old_data_json = json.dumps(app_data)
    app_data['step1'] = {
        'disease_name': disease_name,
        'stays_df': step1_data['stays_df'],
        'occupancy_df': step1_data['occupancy_df']
    }
    data_json = json.dumps(app_data)

    # If data changed, discard all steps after the current step
    if data_json != old_data_json:
        app_data = {'step1': app_data['step1']}

    # Proceed to the next step of the web app
    step = 2

    return step - 1, app_data, False, 'No errors detected.'

# endregion


# region helpers
def extract_df(dash_upload_str: str, filename: str):
    """Extract a Pandas dataframe from a .csv or .xlsx file.

    Parameters:
        dash_upload_str (str):
            File contents in the Dash Upload format.  Contains the file type and base64-encoded
            contents.
    """

    assert filename.endswith('.csv') or filename.endswith('.xlsx'), \
        "File extension must be .csv or .xlsx."

    _, content_string = dash_upload_str.split(',')
    decoded = b64decode(content_string)
    file = BytesIO(decoded)

    if filename.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    assert df is not None, f'Could not extract table from "{filename}".'
    assert not df.empty, f'Parsing "{filename}" resulted in an empty table.'

    return df
# endregion
