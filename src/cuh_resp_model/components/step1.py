"""Main module for Step 1 of the stepper: Upload files."""

from base64 import b64decode
from io import BytesIO
from pathlib import Path

import dash
import dash_mantine_components as dmc
import humanize
import numpy as np
import pandas as pd
from dash import Input, Output, State, callback, clientside_callback
from dash_compose import composition

from cuh_resp_model.components.ids import *
from cuh_resp_model.utils import JSCode, read_file

from .back_next import back_next
from .upload_box import upload_box

INITIAL_PROMPT = "Upload .xlsx (click or drag-and-drop)"


@composition
def stepper_step():
    """The contents for the Stepper Step 1 in the app."""

    with dmc.StepperStep(
        None,
        label="Upload files",
        description=dmc.Text(
            "Upload patient stay & occupancy records", size="xs")
    ) as ret:
        with dmc.Card():
            with dmc.Stack(gap="xl"):
                yield dmc.Text("Step 1: Upload Files", ta="center", size="xl")
                yield stack()
                yield back_next(None, ID_STEPPER_BTN_1_TO_2)
    return ret


@composition
def stack():
    """The DMC stack."""
    with dmc.Stack(gap=24) as ret:
        yield dmc.TextInput(
            label="Name of respiratory illness",
            id=ID_INPUT_RESP_NAME,
            placeholder="E.g., COVID, influenza, RSV"
        )
        yield upload_box(
            label="Historical patient stay data:",
            _id=ID_PATIENT_FILE_UPLOAD,
            prompt_id=ID_PATIENT_FILE_PROMPT,
            initial_prompt=INITIAL_PROMPT
        )
        yield upload_box(
            label="Historical occupancy data:",
            _id=ID_OCCUPANCY_FILE_UPLOAD,
            prompt_id=ID_OCCUPANCY_FILE_PROMPT,
            initial_prompt=INITIAL_PROMPT
        )
    return ret


# region callbacks
#
@callback(
    Output(ID_STEPPER, 'active', allow_duplicate=True),
    Output(ID_STORE_APPDATA, 'data', allow_duplicate=True),
    Input(ID_STEPPER_BTN_1_TO_2, 'n_clicks'),
    State(ID_INPUT_RESP_NAME, 'value'),
    State(ID_PATIENT_FILE_UPLOAD, 'contents'),
    State(ID_OCCUPANCY_FILE_UPLOAD, 'contents'),
    prevent_initial_call=True
)
def stepper_next(_,
                 disease_name: str,
                 patient_file_contents: str,
                 occupancy_file_contents: str):
    """Process app data for Step 1 and proceed to Step 2."""

    los_data, arr_data = get_los_data(to_bytesio(patient_file_contents))
    occupancy_data = get_occupancy_data(to_bytesio(occupancy_file_contents))

    # Data to save in app storage
    new_data = {
        "completed": 1,
        "step_1": {
            "disease_name": disease_name,
            "los_data": los_data,
            "arr_data": arr_data,
            "occupancy_data": occupancy_data
        }
    }

    # Validate inputs
    if not disease_name:
        return dash.no_update, dash.no_update

    # Go to next step in Stepper (subtract 1 as 0-based) and save computed data so far
    return 1, new_data


clientside_callback(
    """(d, c1, c2) => (!d || !c1 || !c2)""",
    Output(ID_STEPPER_BTN_1_TO_2, 'disabled'),
    Input(ID_INPUT_RESP_NAME, 'value'),
    Input(ID_PATIENT_FILE_UPLOAD, 'contents'),
    Input(ID_OCCUPANCY_FILE_UPLOAD, 'contents'),
)


CHECK_TEXTBOX_EMPTY: JSCode = read_file(
    Path(__file__).parent.resolve() / "js/check_textbox_empty.js")
"""Triggered when textbox is changed or Next button is pressed.
Display error message if textbox is empty."""

# Ensure a disease name is entered in the corresponding text input.
clientside_callback(
    CHECK_TEXTBOX_EMPTY,
    Output(ID_INPUT_RESP_NAME, 'error', allow_duplicate=True),
    Input(ID_INPUT_RESP_NAME, 'value'),
    Input(ID_STEPPER_BTN_1_TO_2, "n_clicks"),
    prevent_initial_call=True
)


@callback(
    Output(ID_PATIENT_FILE_PROMPT, 'children'),
    Output(ID_PATIENT_FILE_PROMPT, 'c'),
    Input(ID_PATIENT_FILE_UPLOAD, 'contents'),
    State(ID_PATIENT_FILE_UPLOAD, 'filename'),
    prevent_initial_call=True
)
def show_file_details_patient(contents, filename):
    """Show status message when a patient LOS file is uploaded."""
    return show_file_details(contents, filename)


@callback(
    Output(ID_OCCUPANCY_FILE_PROMPT, 'children'),
    Output(ID_OCCUPANCY_FILE_PROMPT, 'c'),
    Input(ID_OCCUPANCY_FILE_UPLOAD, 'contents'),
    State(ID_OCCUPANCY_FILE_UPLOAD, 'filename'),
    prevent_initial_call=True
)
def show_file_details_occupancy(contents, filename):
    """Show status message when an occupancy file is uploaded."""
    return show_file_details(contents, filename)


def show_file_details(contents: str | None, filename: str):
    """Show status message after file is uploaded."""
    if contents is None:
        return INITIAL_PROMPT, "var(--text-color)"
    if not filename:
        filename = "upload.xlsx"
    _, content_string = contents.split(',')
    decoded = b64decode(content_string)
    filesize = humanize.naturalsize(len(decoded))
    return (
        f"✅ Uploaded \"{filename}\" ({filesize}). Click or drop file here to change. ✅",
        "var(--mantine-color-green-text)"
    )
#
# endregion


# region helpers
#
def to_bytesio(file_contents: str) -> BytesIO:
    """Convert Dash Upload bytes to an Excel file object."""
    _, content_string = file_contents.split(',')
    file_bytes = b64decode(content_string)
    return BytesIO(file_bytes)


def get_los_data(file: BytesIO) -> tuple[dict, dict]:
    """Parse patient stay data into a Python dict (via Pandas dataframe), and
    compute daily arrivals, defined by the time of first positive test sample.

    Returns:
        tuple[dict,dict]:
            A pair of dicts, derived from Pandas dataframes.
            - [0]: Processed patient length-of-stay data
            - [1]: Daily arrival counts and 7-day rolling average.
    """
    los_raw = pd.read_excel(file)
    los = los_raw.copy()

    # Clean-up

    # Remove not admitted
    los = los.loc[los.Summary != 'Not Admitted']

    # Remove those not detected before discharge
    los = los.loc[los.First_Pos_Collected_All < los.Discharge]

    # Only start counting LOS from time of 1st positive test
    los = los.assign(
        Admission=np.maximum(los.Admission, los.First_Pos_Collected_All)
    )

    arr = pd.DataFrame(los).loc[:, ['First_Pos_Collected_All', 'Summary']]\
        .set_index('First_Pos_Collected_All')\
        .resample('D')\
        .count()\
        .rename(columns={'Summary': 'Count'})
    arr = arr.assign(seven_d_avg=arr.rolling('7d').mean()['Count'])\
        .rename(columns={'seven_d_avg': '7 day avg.'})

    return los.to_dict('tight'), arr.to_dict('tight')


def get_occupancy_data(file: BytesIO) -> dict:
    """Parse occupancy data into a Python dict (via Pandas dataframe).

    The table to be extracted should start in Cell A1 of the first sheet, and have columns
    (case sensitive):

    - Date
    - Critical Care
    - Non Critical Care
    """
    data = pd.read_excel(file, usecols='A:C')
    return data.set_index('Date').to_dict('tight')
#
# endregion
