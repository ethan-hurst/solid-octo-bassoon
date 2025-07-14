.PHONY: run run-api run-worker run-beat run-all install setup-db clean

# Run all services
run: run-all

run-all:
	@echo "Starting all services..."
	@./run_all.sh

# Run individual services
run-api:
	source venv_linux/bin/activate && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	source venv_linux/bin/activate && celery -A src.celery_app worker --loglevel=info

run-beat:
	source venv_linux/bin/activate && celery -A src.celery_app beat --loglevel=info

# Setup commands
install:
	python -m venv venv_linux
	source venv_linux/bin/activate && pip install -r requirements.txt

setup-db:
	docker-compose up -d postgres redis
	sleep 5
	source venv_linux/bin/activate && alembic upgrade head

# Docker commands
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Clean up
clean:
	pkill -f "uvicorn src.api.main:app" || true
	pkill -f "celery -A src.celery_app worker" || true
	pkill -f "celery -A src.celery_app beat" || true