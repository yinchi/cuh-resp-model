param(
    [int]$Port = 8050      # default if -Port isn’t supplied
)

Push-Location -Path (Join-Path $PSScriptRoot 'src')

# Silence most messages from the `fitter` module
$env:LOGURU_AUTOINIT = '0'

# Run the model via uv
& uv run python -m cuh_resp_model $Port

Pop-Location
