.PHONY: install test coverage test-bot run bot docker-up docker-down

install:
	pip install -r backend/requirements.txt -r backend/requirements-dev.txt

test:
	cd backend && CHECKER_ENABLED=false python -m pytest tests/

coverage:
	cd backend && CHECKER_ENABLED=false python -m pytest tests/ --cov=app --cov-report=term-missing

test-bot:
	cd bot && python -m pytest test_commands.py test_state.py

run:
	cd backend && uvicorn app.main:app --reload --port 8000

bot:
	cd bot && python bot.py

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down
