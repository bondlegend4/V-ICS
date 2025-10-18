# Variables
DOCKER_COMPOSE = docker-compose.yml

# Default rule
all: setup_all

# Setup all services
setup_all:
	@echo "Starting all V-ICS services..."
	docker compose up -d

# Individual service controls
setup_plc:
	@echo "Starting OpenPLC..."
	docker compose up -d openplc

setup_scada:
	@echo "Starting SCADA-LTS..."
	docker compose up -d database scadalts

setup_modbus:
	@echo "Starting Modbus server..."
	docker compose up -d modbus-server

# Build services
build:
	@echo "Building all services..."
	docker compose build

build_modbus:
	@echo "Building Modbus server..."
	docker compose build modbus-server

# Test Modbus server
test_modbus:
	@echo "Testing Modbus server..."
	cd modelica-rust-modbus-server && cargo test --test modbus_client_test -- --nocapture

# Logs
logs:
	docker compose logs -f

logs_modbus:
	docker compose logs -f modbus-server

logs_openplc:
	docker compose logs -f openplc

# Stop services
stop:
	@echo "Stopping all services..."
	docker compose down

stop_modbus:
	docker compose stop modbus-server

# Clean up
clean:
	@echo "Cleaning up containers and volumes..."
	docker compose down -v
	@find . -name "*.pyc" -exec rm -f {} \;
	@find . -name "__pycache__" -exec rm -rf {} \;

# Status
status:
	@echo "Service status:"
	docker compose ps

# Help
help:
	@echo "V-ICS Makefile Commands"
	@echo ""
	@echo "Setup:"
	@echo "  all          - Start all services"
	@echo "  setup_plc    - Start OpenPLC only"
	@echo "  setup_scada  - Start SCADA-LTS and database"
	@echo "  setup_modbus - Start Modbus server only"
	@echo ""
	@echo "Build:"
	@echo "  build        - Build all services"
	@echo "  build_modbus - Build Modbus server"
	@echo ""
	@echo "Test:"
	@echo "  test_modbus  - Test Modbus connectivity"
	@echo ""
	@echo "Logs:"
	@echo "  logs         - View all logs"
	@echo "  logs_modbus  - View Modbus server logs"
	@echo "  logs_openplc - View OpenPLC logs"
	@echo ""
	@echo "Control:"
	@echo "  stop         - Stop all services"
	@echo "  stop_modbus  - Stop Modbus server"
	@echo "  clean        - Remove all containers and volumes"
	@echo "  status       - Show service status"