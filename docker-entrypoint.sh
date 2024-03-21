#!/bin/sh

echo "Starting DANE audio extraction worker"

poetry run python worker.py "$@"

echo "The worker has finished"