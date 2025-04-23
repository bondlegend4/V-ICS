# V-ICS System Bridge

## Overview

The V-ICS System Bridge is a central component of the Virtual Industrial Control System (V-ICS) learning environment. It acts as an intermediary layer, facilitating communication and data synchronization between the simulated physical process (e.g., Irrigation Simulation), the Programmable Logic Controller (PLC - OpenPLC), and potentially other components like SCADA systems (Scada-LTS) or external interfaces.

Built with Python and Flask, the bridge provides:

1.  **Real-time State Synchronization:** Polls the PLC for its current state (inputs/outputs) and the simulation for its state (sensor readings, actuator status), making them accessible.
2.  **Data Exchange:** Writes commands or setpoints from the PLC to the simulation (via a connector like Memcached) and potentially vice-versa.
3.  **Web Interface:** A user interface to monitor the status of connections, view system state, and trigger predefined tests.
4.  **API:** A RESTful API for programmatic access to system status, state, and test results.
5.  **Testing Framework:** Enables running predefined tests to validate system behavior and security scenarios.

## Architecture

* **Framework:** Python, Flask (Web Framework), Waitress (WSGI Server)
* **Communication:**
    * **PLC:** Modbus TCP (using `pyModbusTCP`) to interact with OpenPLC.
    * **Simulation:** Connector interface (currently configured for Memcached via `python-memcached`) to exchange state data with the simulation container.
* **Concurrency:** Uses background threads for polling the PLC and synchronizing with the simulation.

## Setup and Running

### Prerequisites

* **Python:** Version 3.10 or higher (due to type hinting syntax used).
* **Docker & Docker Compose:** Required for running the full V-ICS environment.
* **Dependencies:** Listed in `requirements.txt`.

### Running with Docker Compose (Recommended)

The bridge is designed to be run as part of the main V-ICS `docker-compose.yml` setup.

1.  **Navigate** to the root `V-ICS` directory.
2.  **Build/Rebuild** the bridge image if changes were made:
    ```bash
    docker-compose build bridge
    ```
3.  **Start** the entire V-ICS stack (including the bridge):
    ```bash
    docker-compose up -d
    ```
4.  **Access:** The bridge web interface will be available at `http://localhost:5001` (or the host IP if running Docker elsewhere).
5.  **Logs:** View logs using `docker-compose logs bridge`.
6.  **Stop:** Stop the stack using `docker-compose down`.

### Running Locally (for Development/Debugging)

1.  **Navigate** to the root `V-ICS` directory.
2.  **Create and Activate Virtual Environment:**
    ```bash
    python3 -m venv venv # Use python3.10 or higher
    source venv/bin/activate # (Linux/macOS)
    # .\venv\Scripts\activate # (Windows)
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r bridge/requirements.txt
    ```
4.  **Ensure Dependencies are Running:** The local setup assumes that the PLC (OpenPLC) and the connector (Memcached) are running and accessible from your host machine at the addresses specified in `bridge/config.py` or environment variables. This is often simpler to manage using Docker Compose.
5.  **Run the Application:** Use one of the following commands from the **root `V-ICS` directory**:
    * **Using Waitress (mimics production):**
        ```bash
        waitress-serve --host=0.0.0.0 --port=5001 bridge.app:app
        ```
    * **Using Flask Development Server:**
        ```bash
        # Set environment variables (adjust for your shell)
        export FLASK_APP=bridge.app
        export FLASK_ENV=development
        # Run
        flask run --host=0.0.0.0 --port=5001
        ```
6.  **Access:** The bridge web interface will be available at `http://localhost:5001`.

## Web Interface

Accessible via a web browser at the bridge's base URL (e.g., `http://localhost:5001`).

* **`/` or `/status` (`status.html`):**
    * Displays the current connection status to the PLC (OpenPLC) and the Simulation Connector (Memcached).
    * Shows a high-level overview of the PLC state (key inputs/outputs) and simulation state.
* **`/details` (`details.html`):**
    * Provides a more granular view of the data being exchanged.
    * Lists specific Modbus register values read from/written to the PLC.
    * Shows detailed key-value pairs representing the simulation state retrieved from the connector.
* **`/tests` (`tests.html`):**
    * Lists available system tests defined in `testing.py`.
    * Allows users to trigger selected tests.
    * Displays the status (Running, Passed, Failed) and results of recently run tests.
* **`/history` (`history.html`):**
    * (Functionality may depend on implementation) Intended to display historical test results or potentially logged state transitions over time.

## API Endpoints

The bridge exposes a RESTful API for programmatic interaction. Base URL: `http://localhost:5001/api`

* **`GET /api/status`:**
    * Returns a JSON object containing the connection status (PLC, Simulation) and a summary of the system state.
* **`GET /api/state`:**
    * Returns a more detailed JSON object representing the current PLC register values and simulation state variables.
* **`GET /api/tests`:**
    * Returns a JSON list of available tests, including their IDs and descriptions.
* **`POST /api/tests/<test_id>/run`:**
    * Triggers the execution of the specified `test_id`. Returns a task ID or immediate status.
* **`GET /api/test_results/<test_id>`:**
    * Returns the status and results (output, pass/fail) for the specified test run.

*(Note: Specific API endpoint details might vary based on the implementation in `routes/api.py`)*

## Testing

The V-ICS project incorporates testing at multiple levels:

1.  **Unit/Integration Tests:** Located in the `V-ICS/tests/` directory (e.g., `modbus_io_test.py`, `irrigation_simulator_test.py`). These test individual components or their interactions in isolation. They are typically run using a test runner like `pytest`.
2.  **System Tests (via Bridge):** Defined within the bridge's `testing.py` module and executed via the `/tests` web page or `/api/tests/...` endpoints. These tests often simulate specific operational sequences or security scenarios outlined in the project's research goals (e.g., verifying correct PLC logic execution based on simulated sensor inputs, testing resilience to certain data manipulations). Refer to the project proposal/thesis documentation for details on the specific scenarios implemented.

## Configuration

Key configuration parameters are managed in:

* **`bridge/config.py`:** Defines default values for connection details (Modbus host/port, connector path), polling intervals, timeouts, etc.
* **Environment Variables:** Several settings in `config.py` can be overridden by environment variables set in the `docker-compose.yml` file or locally. Common overrides include:
    * `MODBUS_HOST`, `MODBUS_PORT`
    * `CONNECTOR_TYPE`, `CONNECTOR_PATH`, `CONNECTOR_NAME`
    * `FLASK_ENV` (set to `development` for debug mode)

## Dependencies

All Python dependencies required by the bridge are listed in `bridge/requirements.txt`. These are installed automatically when building the Docker image or manually when setting up a local virtual environment.