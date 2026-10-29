ifeq ($(OS),Windows_NT)
VENV_PYTHON := .venv/Scripts/python.exe
else
VENV_PYTHON := .venv/bin/python
endif

ROBOT_ARGS ?=

.PHONY: setup lint typecheck test test-firefox report

setup:
	python -m venv .venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.lock.txt

lint:
	$(VENV_PYTHON) -m ruff check libraries mock_portal config tests_unit
	$(VENV_PYTHON) -m robocop check --ignore SPC03 --ignore MISC04 --ignore VAR05 resources tests
	$(VENV_PYTHON) -m robotidy --check resources tests

typecheck:
	$(VENV_PYTHON) -m mypy

test:
	$(VENV_PYTHON) libraries/run_robot.py --outputdir results $(ROBOT_ARGS) tests/group_benefits.robot

test-firefox:
	$(VENV_PYTHON) libraries/run_robot.py --variable BROWSER:firefox --outputdir results $(ROBOT_ARGS) tests/group_benefits.robot

report:
	$(VENV_PYTHON) -m robot.rebot --outputdir results/reports --output output.xml --log log.html --report report.html results/output.xml
