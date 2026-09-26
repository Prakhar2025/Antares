.PHONY: install lint type test gates

ifeq ($(OS),Windows_NT)
PY := .venv/Scripts/python.exe
else
PY := .venv/bin/python
endif

install:
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check .

type:
	$(PY) -m mypy src

test:
	$(PY) -m pytest --cov=src/antares --cov-fail-under=90

gates: lint type test
