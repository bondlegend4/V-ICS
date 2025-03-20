# Virtual-Industrial_Control_System (V-ICS)

A Docker-based virtual industrial control system for simulating a municipal water system (inspired by the Flint, Michigan municipal water infrastructure).

**Code released under** [MIT license](https://github.com/bondlegend4/V-ICS/blob/main/LICENSE).

---

## Table of Contents

- [Overview](#overview)  
- [Quick Start with Docker Compose](#quick-start-with-docker-compose)  
- [Usage](#usage)  
- [Troubleshooting & Restarting](#troubleshooting--restarting)  
- [Issues and Ideas](#issues-and-ideas)  
- [Development](#development)  
- [License](#license)

---

## Overview

V-ICS is designed to emulate typical components of a modern industrial control system. This project includes containers for:

1. [**OpenPLC**](http://localhost:8082/login) – For programmable logic controller logic.  
2. [**SCADA-LTS**](http://localhost:8080/Scada-LTS/login.htm#/watch-list) – For supervisory control and data acquisition tasks.
3. **Godot HTML** - Your browser visualizing a Mar's Colony getting cyberattacked.
4. [**Godot Bridge**](http://localhost:5001/status) – A bridging service connecting a Godot-based visualization/game to the PLC.  
5. **Simulation Containers** – Generates sensor data (e.g., water flow, pressure, etc.).

You can customize each container and scenario to explore ICS security concepts, train staff, or test new control strategies.

---

## Quick Start with Docker Compose

1. **Install Docker**  
   - [Install Docker Desktop](https://www.docker.com/products/docker-desktop) if on Windows or macOS.  
   - On Linux, install the [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose Plugin](https://docs.docker.com/compose/install/).

2. **Clone the Repository**  
   ```bash
   git clone https://github.com/bondlegend4/V-ICS.git
   cd V-ICS
   ```

3. **Configure Environment (Optional)**  
   - Edit any relevant environment variables in `docker-compose.yml` or `.env` if you have one.  
   - Review or modify the bridging container settings, e.g. `MODBUS_HOST`, `MODBUS_PORT`, etc.

4. **Build & Start**  
   ```bash
   docker compose up -d --build
   ```
   - The `-d` flag runs containers in the background (detached).  
   - The `--build` flag rebuilds images if Dockerfiles or dependencies changed.  

---

## Usage

1. **OpenPLC**  
   - Use the OpenPLC web interface to load a PLC program simulating a water system.  
   - Deploy the logic to the runtime and confirm it is running.
   - Check the logs to figure out where everything went wrong. 

2. **SCADA-LTS**  
   - Connect to SCADA-LTS, configure dashboards or tags, and link it to the PLC for monitoring.

3. **Simulation Containers**
   - The enviroment simulation container generate sensor data (soil moisture, temperature, etc.) and write them to the PLC registers.

4. **Godot Visualization**   
   - The bridging container ensures real-time data from the PLC or simulation is reflected in this game.

---

## Troubleshooting & Restarting

1. **View Logs**  
   ```bash
   docker compose logs -f
   ```
   - Follow logs for all containers.  
   - Add a service name (e.g. `docker compose logs -f openplc`) to target one container.

2. **Restart a Single Service**  
   ```bash
   docker compose restart <service_name>
   ```
   - For instance, `docker compose restart python_bridge`.

3. **Full Restart**  
   ```bash
   docker compose down
   docker compose up -d --build
   ```
   - This stops all containers and rebuilds/runs them cleanly.

4. **Port Conflicts**  
   - If you see “address already in use,” change the host port mappings in `docker-compose.yml` or stop any conflicting services.

5. **Connection Problems**  
   - Check environment variables in `docker-compose.yml`.  
   - Verify that the bridging and simulation containers reference `openplc` as the hostname if they need to connect by name over Docker’s internal network.  
   - Verify the PLC program is running and that you’re writing/reading the correct Modbus registers in your ST code vs. the bridging code.

---

## Issues and Ideas

Found a bug? Have an idea for a new feature? Please open a [new Issue](https://github.com/bondlegend4/V-ICS/issues) on our GitHub.

We follow guidelines for:

- **Bug reports**  
- **Feature requests**  
- **Security vulnerability reports**  

When submitting, please describe your issue or proposal and provide enough details (screenshots, logs, steps to reproduce) so we can assist you effectively.

---

## Development

If you plan to develop new features or extend the ICS:

1. **Local Development**  
   - Make changes in your local copy of the code (e.g., bridging code in `godot-bridge-openplc`, simulation logic in `simulations`, etc.).  
   - Rebuild your containers using:
     ```bash
     docker compose up -d --build
     ```
2. **Tests**  
   - If you have automated tests in `tests/`, run them locally with your Python environment or integrate them into a CI pipeline.  
   - For container-level testing, you might stand up everything with Docker Compose and run end-to-end checks.

3. **Documentation**  
   - Check out our [GitHub Wiki](https://github.com/bondlegend4/V-ICS/wiki) for deeper setup instructions, architecture diagrams, or advanced usage scenarios.  
   - Feel free to contribute by creating new wiki pages or updating existing ones.

---

## License

This project is licensed under the terms of the [MIT license](https://github.com/bondlegend4/V-ICS/blob/main/LICENSE).  

Feel free to use, modify, and distribute this software in personal and commercial projects under the terms of the MIT license. If you find it helpful, please consider contributing back your improvements or bug fixes.

---

Thank you for using **V-ICS**. If you have any questions or run into issues, please open an [Issue](https://github.com/bondlegend4/V-ICS/issues) or check our [Wiki](https://github.com/bondlegend4/V-ICS/wiki). Contributions and feedback are always welcome!