# ------------------------------------------------------------
# Advising Makefile
# ------------------------------------------------------------
# This Makefile acts as a living runbook for Ubuntu deployments.
# It documents and automates common steps: creating the virtualenv,
# installing Python/Node dependencies, running migrations, and
# collecting static assets.  Each target can be called individually
# (e.g., `make install`) or bundled via `make deploy`.
#
# Conventions:
#   - All commands assume you run `make` from the repo root.
#   - Python lives inside `.venv`.  If it does not exist, run `make venv`.
#   - Environment variables come from `.env` (copy from `.env.example`).
#   - Ubuntu services (gunicorn/nginx/systemd) are referenced but not
#     configured automatically; you can adapt these targets to your stack.
#
# Helpful pattern:
#   make venv
#   make install
#   make migrate
#   make build-frontend
#   make collectstatic
#   make gunicorn   # or hook into a systemd unit

SHELL := /bin/bash
PYTHON := .venv/bin/python
PIP := .venv/bin/pip
MANAGE := $(PYTHON) src/manage.py
NPM := npm

.PHONY: help \
        apt-deps \
        venv \
        install \
        install-dev \
        migrate \
        check \
        build-frontend \
        collectstatic \
        gunicorn \
        deploy \
        clean \
        clean-pyc

help:
	@echo "Available targets:"
	@echo "  make apt-deps        # Install system packages on Ubuntu (Python, build-essential, node, etc.)"
	@echo "  make venv            # Create Python virtualenv in .venv/"
	@echo "  make install         # Install production Python deps + npm install"
	@echo "  make install-dev     # Install dev Python deps (+ pre-commit tooling)"
	@echo "  make migrate         # Apply Django migrations"
	@echo "  make check           # Run Django system checks"
	@echo "  make build-frontend  # Compile Tailwind assets via npm run tw:build"
	@echo "  make collectstatic   # Collect Django static files"
	@echo "  make gunicorn        # Launch gunicorn locally (manual test)"
	@echo "  make deploy          # Full pipeline: install -> migrate -> build assets -> collectstatic"
	@echo "  make clean           # Remove build artifacts"

# ------------------------------------------------------------
# System prerequisites (run once on a fresh Ubuntu host).
# ------------------------------------------------------------
apt-deps:
	sudo apt update
	sudo apt install -y python3.13 python3.13-venv python3.13-dev build-essential \
	                   libpq-dev nodejs npm git

# ------------------------------------------------------------
# Python environment setup
# ------------------------------------------------------------
venv:
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtualenv..."; \
		python3.13 -m venv .venv; \
	fi
	@echo "Virtualenv ready at .venv/"

# Install runtime requirements (pip + npm).  Assumes `.env` exists.
install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(NPM) install

# Install dev requirements (linters, pytest, etc.)
install-dev: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(NPM) install

# ------------------------------------------------------------
# Django management helpers
# ------------------------------------------------------------
migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

check:
	$(MANAGE) check

# ------------------------------------------------------------
# Frontend build + static assets
# ------------------------------------------------------------
build-frontend:
	$(NPM) run tw:build

collectstatic:
	$(MANAGE) collectstatic --noinput

# ------------------------------------------------------------
# Application server helpers
# ------------------------------------------------------------
gunicorn:
	. .venv/bin/activate && \
	gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

# The deploy target ties everything together for a fresh release.
deploy: install migrate build-frontend collectstatic
	@echo "Deployment steps complete. Configure gunicorn/nginx/systemd separately."

# ------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------
clean: clean-pyc
	rm -rf build dist *.egg-info

clean-pyc:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
