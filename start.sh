#!/bin/bash
# Set Python path to include the project root
export PYTHONPATH="${PYTHONPATH}:."
# Start the application from project root
uvicorn backend.main:app --host 0.0.0.0 --port 10000
