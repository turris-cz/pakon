#   Copyright (C) 2020 CZ.NIC, z. s. p. o. (https://www.nic.cz/)
#
#   This is free software, licensed under the GNU General Public License v3.
#   See /LICENSE for more information.

.PHONY: all prepare-dev venv lint run-create-db clean build
SHELL=/bin/bash

export ENV?=dev

VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=$(shell pwd)/${VENV_NAME}/bin/python3


all:
	@echo "make prepare-dev"
	@echo "         Create python virtual environment and install dependencies."
	@echo "make run-create-db"
	@echo "         Run create_db job."
	@echo "make lint"
	@echo "         Lint project using pylint."
	@echo "make clean"
	@echo "         Remove python artifacts and virtualenv."


prepare-dev:
	python3 -m pip install virtualenv
	make venv

venv: $(VENV_NAME)/bin/activate
$(VENV_NAME)/bin/activate: setup.py
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -e .[devel]
	touch $(VENV_NAME)/bin/activate

lint: venv
	${PYTHON} -m pylint --rcfile=pylintrc pakon_light

test: venv
	${PYTHON} -m pytest tests

run-create-db: venv
	${PYTHON} -m pakon_light.cli.create_db

run-monitor: venv
	${PYTHON} -m pakon_light.cli.monitor

clean:
	find . -name '*.pyc' -exec rm --force {} +
	rm -rf $(VENV_NAME) *.eggs *.egg-info dist build docs/_build .cache tmp
