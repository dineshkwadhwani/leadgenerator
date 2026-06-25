#!/bin/bash

# Lead Generator CLI Runner Script

cd "$(dirname "$0")"

# Activate virtual environment and run the app
source venv/bin/activate
python main.py "$@"
