# CUH respiratory viruses modelling

**Author**: Yin-Chi Chan [\<yinchi.chan@nhs.net\>](mailto:yinchi.chan@nhs.net), Institute for Manufacturing, University of Cambridge

## To run:

> [!NOTE]
> For more detailed instructions on Windows, see the .docx file.

1. Download this code
2. Install uv: <https://docs.astral.sh/uv/getting-started/installation/#standalone-installer>
3. `cd /path/to/project`
4. `uv sync`

Some dependencies may need to be compiled, in which case the above step may fail. To resolve this:

- On Linux (Debian or Ubuntu), use `apt install build-essential`.
- On Windows, use [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022).

![Visual Studio Build Tools installation](build_tools.png)

Then, run Step 4 again.

5. Run the launcher:
    - Linux: `chmod+x launch.sh; ./launch.sh [port number]`
    - Windows: `.\launch.ps1 -Port [port number]` (You will need to set ExecutionPolicy first; see the .docx file.)
