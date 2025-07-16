#!/bin/bash
# Production startup script for Railway

# Set default port if not provided
export PORT=${PORT:-8000}

# Set environment
export ENVIRONMENT=production

# Start the application
echo "🚀 Starting AutoForms on port $PORT"
uvicorn backend.main:app --host 0.0.0.0 --port $PORT --workers 1
