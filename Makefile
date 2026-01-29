PYTHON = python3
PIP = pip
SRC_DIR = src
SETUP_SCRIPT = scripts/setup_env.py

.PHONY: help setup install run docker-up docker-down clean

help:
	@echo "Supa-Meta-Budget Management System"
	@echo "-----------------------------------"
	@echo "  make setup       -> Run interactive configuration"
	@echo "  make install     -> Install Python dependencies"
	@echo "  make docker-up   -> Start infrastructure (DB/Metabase)"
	@echo "  make run         -> Run desktop application"
	@echo "  make clean       -> Remove cache and temp files"

setup:
	$(PIP) install -r requirements.txt
	$(PYTHON) $(SETUP_SCRIPT)

install:
	$(PIP) install -r requirements.txt

run:
	export PYTHONPATH=$${PYTHONPATH}:$(shell pwd)/$(SRC_DIR) && $(PYTHON) $(SRC_DIR)/main.py

docker-up:
	docker-compose up -d
	@echo "Infrastructure started. Metabase available at localhost:3000"

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete