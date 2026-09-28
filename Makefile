PYTHON ?= python

.PHONY: help install dev test lint format typecheck run-api render-sample render-showcase showcase docker-build docker-up docker-down deploy clean check

help:
	@echo "QF pipeline commands:"
	@echo "  make install       - pip install -e .[dev]"
	@echo "  make run-api       - uvicorn qf_api.main:app --reload --port 8000"
	@echo "  make test          - pytest"
	@echo "  make lint          - ruff check ."
	@echo "  make format        - ruff format ."
	@echo "  make render-sample - sample MP4 (TOPIC=...)"
	@echo "  make render-showcase - re-render the 4 showcase clips"
	@echo "  make showcase      - compress showcase clips + posters for web"
	@echo "  make deploy        - vercel --prod (static site, needs vercel login)"
	@echo "  make docker-build  - build single-service image"
	@echo "  make docker-up     - compose up -d"
	@echo "  make check         - lint + test"

install:
	pip install -e ".[dev]"

run-api:
	$(PYTHON) -m uvicorn qf_api.main:app --reload --port 8000

run-java-api:
	workers/java-backend/build.bat
	java -cp workers/java-backend/classes qf.QfServer

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

render-sample:
	$(PYTHON) scripts/render_sample.py --topic "$(TOPIC)"

# Showcase set: full-quality renders -> web-compressed clips + posters.
showcase: render-showcase
	$(PYTHON) scripts/make_showcase.py

render-showcase:
	$(PYTHON) scripts/render_showcase.py

# Static showcase site (apps/web). The renderer API is NOT deployed here.
deploy:
	vercel --prod

build-java:
	workers/java-renderer/build.bat

docker-build:
	docker build -t qf-pipeline:local .

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov .coverage .pytest_cache 2>/dev/null || true

check: lint test
