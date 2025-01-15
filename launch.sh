#!/usr/bin/env bash
pushd "$(dirname "$0")/src"
uv run python -m cuh_resp_model
popd
