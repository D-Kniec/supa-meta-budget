PYTHON = python3
PIP = pip
SRC_DIR = src
SETUP_SCRIPT = scripts/setup_env.py
MIGRATE_SCRIPT = scripts/migrate.py

.PHONY: help setup install run docker-up docker-down clean

help:
	@echo "Supa-Meta-Budget Management System"
	@echo "-----------------------------------"
	@echo "  make setup       -> Run interactive configuration and database migration"
	@echo "  make install     -> Install Python dependencies"
	@echo "  make docker-up   -> Start infrastructure (DB/Metabase)"
	@echo "  make run         -> Run desktop application"
	@echo "  make clean       -> Remove cache and temp files"

setup:
	$(PIP) install -r requirements.txt
	$(PYTHON) $(SETUP_SCRIPT)
	$(PYTHON) $(MIGRATE_SCRIPT)

install:
	$(PIP) install -r requirements.txt

run:
	set PYTHONPATH=$(CURDIR)\$(SRC_DIR) && $(PYTHON) $(SRC_DIR)\main.py

docker-up:
	docker-compose up -d
	@echo "Infrastructure started."

docker-down:
	docker-compose down

clean:
	del /s /q *.pyc
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"