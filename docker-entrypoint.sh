#!/bin/sh

echo "Starting audio extraction worker"

python main.py --service=y "$@"

echo "The worker has finished"