"""Main module for Step 1 of the stepper: Upload files."""

from base64 import b64decode
from pathlib import Path
import dash
from dash_compose import composition
import dash_mantine_components as dmc
from dash import callback, clientside_callback, Input, Output, State
import humanize

from cuh_resp_model.components.ids import (
    ID_STEPPER,
    ID_STORE_APPDATA,

    # Stepper button
    ID_STEPPER_BTN_0_TO_1,

    # Step controls
    ID_INPUT_RESP_NAME,
    ID_PATIENT_FILE_UPLOAD,
    ID_PATIENT_FILE_PROMPT,
    ID_OCCUPANCY_FILE_UPLOAD,
    ID_OCCUPANCY_FILE_PROMPT,
)
from cuh_resp_model.utils import read_file

from ..back_next import back_next
from ..upload_box import upload_box


INITIAL_PROMPT = "Upload .xlsx (click or drag-and-drop)"


@composition
def stepper_step():
    """The contents for the current stepper step."""

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
                yield back_next(None, ID_STEPPER_BTN_0_TO_1)
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
            id=ID_PATIENT_FILE_UPLOAD,
            prompt_id=ID_PATIENT_FILE_PROMPT,
            initial_prompt=INITIAL_PROMPT
        )
        yield upload_box(
            label="Historical occupancy data:",
            id=ID_OCCUPANCY_FILE_UPLOAD,
            prompt_id=ID_OCCUPANCY_FILE_PROMPT,
            initial_prompt=INITIAL_PROMPT
        )
    return ret


# region callbacks

CHECK_TEXTBOX_EMPTY = read_file(Path(__file__).parent.resolve() / "../js/check_textbox_empty.js")

# Triggered when textbox is changed or Next button is pressed.
# Display error message if textbox is empty.
clientside_callback(
    CHECK_TEXTBOX_EMPTY,
    Output(ID_INPUT_RESP_NAME, 'error', allow_duplicate=True),
    Input(ID_INPUT_RESP_NAME, 'value'),
    Input(ID_STEPPER_BTN_0_TO_1, "n_clicks"),
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
    return show_file_details(contents, filename)


@callback(
    Output(ID_OCCUPANCY_FILE_PROMPT, 'children'),
    Output(ID_OCCUPANCY_FILE_PROMPT, 'c'),
    Input(ID_OCCUPANCY_FILE_UPLOAD, 'contents'),
    State(ID_OCCUPANCY_FILE_UPLOAD, 'filename'),
    prevent_initial_call=True
)
def show_file_details_occupancy(contents, filename):
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


@callback(
    Output(ID_STEPPER, "active", allow_duplicate=True),
    Output(ID_STORE_APPDATA, "data", allow_duplicate=True),
    Input(ID_STEPPER_BTN_0_TO_1, "n_clicks"),
    State(ID_INPUT_RESP_NAME, "value"),
    prevent_initial_call=True
)
def stepper_next_1(_, disease_name):
    """Process app data for Step 1 (0 internally) and proceed to Step 2 (1 internally)."""
    new_data = {
        "completed": 1,
        "step_1": {
            "disease_name": disease_name
        }
    }

    # Validate inputs
    if not disease_name:
        return dash.no_update, dash.no_update

    # Go to next step in Stepper
    return 1, new_data
# endregion
