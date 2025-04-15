#!/usr/bin/env bash
pushd "$(dirname "$0")/src"

# disable most messages from the `fitter` module
export LOGURU_AUTOINIT=0

uv run python -m cuh_resp_model
popd
