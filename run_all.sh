#!/bin/bash

# Activate virtual environment
source venv_linux/bin/activate

# Function to handle cleanup on exit
cleanup() {
    echo "Shutting down services..."
    pkill -f "uvicorn src.api.main:app"
    pkill -f "celery -A src.celery_app worker"
    pkill -f "celery -A src.celery_app beat"
    exit 0
}

# Set up trap to call cleanup on script exit
trap cleanup EXIT INT TERM

# Start services in background
echo "Starting FastAPI server..."
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &

echo "Starting Celery worker..."
celery -A src.celery_app worker --loglevel=info &

echo "Starting Celery beat..."
celery -A src.celery_app beat --loglevel=info &

echo "All services started. Press Ctrl+C to stop all services."

# Wait indefinitely
wait