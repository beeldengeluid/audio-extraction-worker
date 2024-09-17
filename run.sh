#!/bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"

# Load the environment vars
if [ -f "$SCRIPTPATH/.env.override" ]; then
    set -a
    source $SCRIPTPATH/.env.override
    set +a
else
    echo "No .env.override found"
fi

poetry run python main.py