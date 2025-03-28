# Variables
PYTHON = python3
SIMULATION = modbus_simulation.py
PLC_TEST = plc_test.py
PLOT_TEST = modbus_traffic_plot.py

# Docker variables
DOCKER_IMAGE = openplc:v3
DOCKER_COMPOSE = docker-compose.yml  # Ensure you have a docker-compose.yml file set up with services openplc, database, scadalts

# Default rule to start the simulation and both tests
all: setup_plc simulate test plot

# Rule to set up and run the OpenPLC Docker container
setup_plc:
	@echo "Setting up OpenPLC using Docker..."
	# Check if the Docker image exists
	@if [[ -z $$(docker images -q $(DOCKER_IMAGE)) ]]; then \
		echo "Building OpenPLC Docker image..."; \
		docker build -t $(DOCKER_IMAGE) .; \
	fi
	# Run the OpenPLC container (bind to port 8080)
	@echo "Starting OpenPLC Docker container..."
	@if ! docker ps --format '{{.Names}}' | grep -q openplc; then \
		docker run -d --rm --privileged -p 8080:8080 $(DOCKER_IMAGE); \
	else \
		echo "OpenPLC container is already running."; \
	fi

	# Start the necessary services via docker-compose
	@echo "Starting necessary Docker services with docker-compose..."
	@if ! docker ps --format '{{.Names}}' | grep -q openplc; then \
		echo "Starting openplc service..."; \
		docker compose up -d openplc; \
	fi

	@if ! docker ps --format '{{.Names}}' | grep -q database; then \
		echo "Starting database service..."; \
		docker compose up -d database; \
	fi

	@if ! docker ps --format '{{.Names}}' | grep -q scadalts; then \
		echo "Starting scadalts service..."; \
		docker compose up -d scadalts; \
	fi

	@echo "OpenPLC setup complete."

# Rule to start the Modbus simulation
simulate:
	@echo "Starting the Modbus TCP simulation server..."
	$(PYTHON) $(SIMULATION)

# Rule to run the first test (PLC response test)
test:
	@echo "Running the PLC response test..."
	$(PYTHON) $(PLC_TEST)

# Rule to run the second test (Modbus traffic plotting)
plot:
	@echo "Running the Modbus traffic plotting test..."
	$(PYTHON) $(PLOT_TEST)

# Rule to clean up any Python-generated files
clean:
	@echo "Cleaning up..."
	@find . -name "*.pyc" -exec rm -f {} \;
	@find . -name "__pycache__" -exec rm -rf {} \;
	@echo "Clean complete."

# Help rule to display usage information
help:
	@echo "Makefile for Python Modbus Simulation and Tests"
	@echo ""
	@echo "Targets:"
	@echo "  all        - Run the setup, simulation, and both tests."
	@echo "  setup_plc  - Set up and run the OpenPLC Docker container."
	@echo "  simulate   - Start the Modbus simulation server."
	@echo "  test       - Run the PLC response test."
	@echo "  plot       - Run the Modbus traffic plotting test."
	@echo "  clean      - Remove generated Python cache files."
	@echo "  help       - Display this help message."
