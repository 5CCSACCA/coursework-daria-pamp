#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="$(pwd)/src"
python -m pytest -q

