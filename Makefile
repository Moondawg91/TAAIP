# Developer convenience Makefile

.PHONY: api web dev

api:
	python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 --reload

web:
	cd apps/web && npm start

# Start both in parallel (requires GNU make job support or run in background)
dev:
	@echo "Starting API and web in background..."
	python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 --reload &
	cd apps/web && npm start

.PHONY: archive-staging
archive-staging:
	python3 scripts/archive_staging.py

