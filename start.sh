#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting AutoForms deployment..."

# Set Python path to include the project root
export PYTHONPATH="${PYTHONPATH}:."

# Set default environment variables for production
export ENV=${ENV:-production}
export DEBUG=${DEBUG:-false}

# Check critical environment variables
if [ -z "$MONGODB_URI" ]; then
    echo "❌ MONGODB_URI environment variable is required"
    exit 1
fi

if [ -z "$OPENAI_KEY" ]; then
    echo "❌ OPENAI_KEY environment variable is required"
    exit 1
fi

echo "✅ Environment variables configured"
echo "🔌 Testing database connection..."

# Test database connection before starting server
python3 -c "
import asyncio
import sys
import os
sys.path.append('.')

async def test_db():
    try:
        from backend.db import get_db
        db = await get_db()
        await db.command('ping')
        print('✅ Database connection successful')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

if not asyncio.run(test_db()):
    sys.exit(1)
"

echo "🌐 Starting web server..."
# Start the application with proper error handling
exec uvicorn backend.main:app --host 0.0.0.0 --port 10000 --workers 1
