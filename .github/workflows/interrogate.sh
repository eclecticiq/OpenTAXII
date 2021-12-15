#!/usr/bin/env bash

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

interrogate --fail-under=0 --config "$SCRIPT_DIR/../../pyproject.toml" $1 | grep -o "actual: [0-9]*\.[0-9]*%" | grep -o "[0-9]*\.[0-9]*"
