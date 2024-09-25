#!/bin/sh

echo "Starting audio extraction worker"

python main.py "$@"

echo "The worker has finished"