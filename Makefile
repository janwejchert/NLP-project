# ATC Readback Verifier: common tasks.
# Usage: `make setup`, `make test`, `make run`, `make eval`, etc.

VENV ?= .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
MODEL ?= qwen2.5:3b

.PHONY: help setup pull-model run eval test lint fmt notebook clean

help:
	@echo "Targets:"
	@echo "  setup        Create venv and install runtime + dev dependencies"
	@echo "  pull-model   Pull the local Ollama model ($(MODEL))"
	@echo "  run          Launch the Streamlit app"
	@echo "  eval         Run the evaluation harness over the test set"
	@echo "  test         Run unit tests (comparator logic, no LLM needed)"
	@echo "  lint         Run ruff checks"
	@echo "  fmt          Auto-format with ruff"
	@echo "  notebook     Regenerate + execute notebooks/analysis.ipynb"
	@echo "  clean        Remove caches and build artifacts"

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt -r requirements-dev.txt
	$(PIP) install -e .
	@echo "Done. Activate with: source $(VENV)/bin/activate"

pull-model:
	ollama pull $(MODEL)

run:
	$(VENV)/bin/streamlit run app/streamlit_app.py

eval:
	$(PY) eval/run_eval.py

test:
	$(VENV)/bin/pytest

lint:
	$(VENV)/bin/ruff check src tests eval app

fmt:
	$(VENV)/bin/ruff format src tests eval app
	$(VENV)/bin/ruff check --fix src tests eval app

notebook:
	$(PY) notebooks/build_notebook.py
	$(VENV)/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/analysis.ipynb

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__ src/*.egg-info build dist
