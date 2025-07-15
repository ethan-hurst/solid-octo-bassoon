#!/bin/bash

echo "🚀 Starting Sports Betting Edge Finder on Replit..."

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate

if [ ! -f ".deps_installed" ]; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    pip install psycopg2-binary asyncpg aiosqlite
    touch .deps_installed
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start PostgreSQL if not running
if ! pg_isready -q; then
    echo "🐘 Starting PostgreSQL..."
    pg_ctl start -D /tmp/postgres_data -l /tmp/postgres.log &
    sleep 3
    
    # Create database if it doesn't exist
    createdb sportsbetting 2>/dev/null || true
fi

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "🔴 Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
fi

# Run migrations
echo "🔧 Running database migrations..."
alembic upgrade head 2>/dev/null || echo "⚠️  Migrations failed, but continuing..."

# Function to handle cleanup on exit
cleanup() {
    echo "🛑 Shutting down services..."
    pkill -f "uvicorn src.api.main:app"
    pkill -f "celery -A src.celery_app worker"
    pkill -f "celery -A src.celery_app beat"
    pkill -f "npm run dev"
    exit 0
}

# Set up trap to call cleanup on script exit
trap cleanup EXIT INT TERM

# Start services in background
echo "🌐 Starting FastAPI server..."
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &

echo "⚙️  Starting Celery worker..."
celery -A src.celery_app worker --loglevel=info &

echo "⏰ Starting Celery beat..."
celery -A src.celery_app beat --loglevel=info &

echo "🎨 Starting frontend..."
cd frontend && npm run dev -- --host 0.0.0.0 --port 3000 &
cd ..

echo "✅ All services started!"
echo "📊 Backend API: https://$REPL_SLUG.$REPL_OWNER.repl.co"
echo "🎯 Frontend: https://$REPL_SLUG-3000.$REPL_OWNER.repl.co"
echo "📚 API Docs: https://$REPL_SLUG.$REPL_OWNER.repl.co/docs"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait indefinitely
wait