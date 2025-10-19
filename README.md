# Virtual-Industrial Control System (V-ICS)

A Docker-based virtual industrial control system featuring physics-based simulation with Modelica, PLC control with OpenPLC, SCADA monitoring with SCADA-LTS, and 3D visualization with Godot.

**Code released under** [MIT license](https://github.com/bondlegend4/V-ICS/blob/main/LICENSE).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Service Access](#service-access)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [License](#license)

---

## Overview

V-ICS emulates a complete industrial control system stack with:

1. **Physics Simulation** (Modelica) – Realistic thermal dynamics
2. **PLC Control** (OpenPLC) – Programmable logic controller
3. **SCADA Monitoring** (SCADA-LTS) – Supervisory control and data acquisition
4. **Communication Layer** (Modbus TCP) – Industry-standard protocol
5. **3D Visualization** (Godot) – Interactive game-based interface

Perfect for:
- ICS security training and research
- Control system testing
- Educational demonstrations
- Cyber-physical system development

---

## Architecture
```
┌─────────────────┐
│  Godot (3D UI)  │ ← Player interaction
└────────┬────────┘
         │ WebSocket/HTTP
┌────────▼────────┐
│   Rust Bridge   │ ← Game ↔ PLC connector
└────────┬────────┘
         │ Modbus TCP
┌────────▼────────┐     ┌──────────────────┐
│    OpenPLC      │────→│   SCADA-LTS      │
│  (PLC Runtime)  │     │  (Monitoring)    │
└────────┬────────┘     └──────────────────┘
         │ Modbus TCP
┌────────▼────────┐
│ Modbus Server   │ ← Rust FFI wrapper
│  (Rust/Tokio)   │
└────────┬────────┘
         │
┌────────▼────────┐
│    Modelica     │ ← Physics simulation
│ SimpleThermalMVP│   (OpenModelica)
└─────────────────┘
```

---

## Quick Start

### Prerequisites

- **Docker Desktop** ([Download](https://www.docker.com/products/docker-desktop))
- **Git** (for cloning the repository)
- **8GB RAM minimum** (recommended: 16GB)

### Installation
```bash
# 1. Clone repository
git clone https://github.com/bondlegend4/V-ICS.git
cd V-ICS

# 2. Initialize submodules
git submodule update --init --recursive

# 3. Build OpenPLC image
docker build -t openplc:v3 ./openplc/OpenPLC_v3

# 4. Start all services
docker compose up -d --build

# 5. Wait for services to initialize (~ 2 minutes)
docker compose logs -f
```

---

## Service Access

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| **OpenPLC** | http://localhost:8082 | `openplc` / `openplc` |
| **SCADA-LTS** | http://localhost:8080/Scada-LTS | `admin` / `admin` |
| **Python Bridge** | http://localhost:5001/status | N/A (status endpoint) |
| **Modbus Server** | tcp://localhost:5502 | N/A (Modbus TCP) |
| **MySQL** | localhost:3306 | `root` / `root` |

---

## Usage Guide

### 1. Modbus Server (Physics Simulation)

The Rust-based Modbus server exposes the Modelica thermal simulation:

**Registers:**
- `100` (0x64): Temperature in K × 100 (e.g., 27315 = 273.15 K)
- `101` (0x65): Heater state (0=OFF, 100=ON)

**Coils:**
- `0`: Heater control (write TRUE to turn on)

**Test with modbus-cli:**
```bash
# Run integration test from inside container (if needed)
docker compose exec modbus-server cargo test --test modbus_client_test

**Monitor logs:**
```bash
docker compose logs -f modbus-server
```

### 2. OpenPLC Configuration

**Step 1: Access OpenPLC**
1. Navigate to http://localhost:8082
2. Login: `openplc` / `openplc`

**Step 2: Configure Modbus Slave Device**
1. Go to **Hardware** → **Slave Devices**
2. Click **Add new device**
3. Configure:
   - **Device Name**: `Thermal`
   - **Device Type**: Generic ModbusTCP
   - **IP Address**: `modbus-server`
   - **Port**: `5502`
   - **Slave ID**: `1`
   - **Registers**:
     - **AI (Analog Input)**: `%IW100` to `%IW101` (temperature, heater state)
     - **DO (Digital Output)**: `%QX0` (heater control)

**Step 3: Upload PLC Program**
1. Go to **Programs** → **Upload Program**
2. Upload your Structured Text (ST) program
3. Example ST code:
```st
PROGRAM ThermalControl
VAR
    temperature AT %IW100 : INT;      // Temperature × 100
    heater_state AT %IW101 : INT;     // 0=OFF, 100=ON
    heater_control AT %QX0 : BOOL;    // Heater output
    setpoint : INT := 29315;          // 293.15 K (20°C)
END_VAR

// Simple bang-bang control
IF temperature < setpoint - 200 THEN
    heater_control := TRUE;
ELSIF temperature > setpoint + 200 THEN
    heater_control := FALSE;
END_IF;
END_PROGRAM
```

4. Click **Start PLC** to run

**Verify Connection:**
- Check **Monitoring** page for live values
- Status should show "Connected" for Thermal device

### 3. SCADA-LTS Setup

**Step 1: Access SCADA-LTS**
1. Navigate to http://localhost:8080/Scada-LTS
2. Login: `admin` / `admin`

**Step 2: Import Configuration** (Already done if you imported settings.json)
1. Go to **Data Sources** → verify `Modelica - Thermal` is present
2. Check **Data Points** → verify `temperature` point exists
3. Enable the data source if disabled

**Step 3: Create Watchlist**
1. Go to **Watch Lists** → **Add new**
2. Name it "Thermal Monitoring"
3. Add data points:
   - `temperature` (from DS_THERMAL)
   - `heater_state` (if configured)

**Step 4: Create Dashboard**
1. Go to **Graphical Views** → **Add new**
2. Add components:
   - **Analog Graphic**: Temperature gauge (0-500 K)
   - **Binary Graphic**: Heater status (ON/OFF)
   - **Chart**: Temperature trend over time

**View Real-time Data:**
- Navigate to your watch list
- You should see live temperature updates every 1 second

### 4. Testing the Complete System

**Scenario: Manual Temperature Control**
```bash
# Start all services
docker compose up -d

# Check Modbus server logs
docker compose logs -f modbus-server

# Run integration test from inside container (if needed)
docker compose exec modbus-server cargo test --test modbus_client_test
```

**Expected Behavior:**
1. Temperature starts at ~250 K (ambient)
2. Turning heater ON causes temperature to rise
3. Turning heater OFF causes temperature to cool back down
4. OpenPLC reads these values at %IW100
5. SCADA-LTS shows live graph of temperature changes

---

## Troubleshooting

### Testing the Modbus Server

**Run Rust integration test:**
```bash
# Terminal 1: Start server
cd modelica-rust-modbus-server
cargo run

# Terminal 2: Run tests
cargo test --test modbus_client_test -- --nocapture
```

**Run example client:**
```bash
# Start server first
cargo run

# In another terminal
cargo run --example simple_client
```

**Expected test output:**
```
✓ Connected to Modbus server
✓ Temperature: 250.00 K (raw: 25000)
✓ Heater state: 0 (0=OFF, 100=ON)
✓ Turned heater ON
✓ Heater confirmed ON
✓ Temperature after heating: 251.25 K
✓ Turned heater OFF
✓ Heater confirmed OFF
✓ Multi-register read: temp=25125, heater=0

✅ All tests passed!
```

### Testing with Docker
```bash
# Start all services
docker compose up -d

# Check Modbus server logs
docker compose logs -f modbus-server

# Run integration test from inside container (if needed)
docker compose exec modbus-server cargo test --test modbus_client_test
```
### OpenPLC Issues

**Problem**: Device "Thermal" shows "Disconnected"

**Solutions**:
1. Verify Modbus server is running: `docker ps`
2. Check hostname is `modbus-server` (not `localhost`)
3. Verify port is `5502`
4. Check firewall/network settings in Docker

**Problem**: Values not changing in Monitoring page

**Solutions**:
1. Verify PLC program is running (green "Running" status)
2. Check that %IW100 address is correct (not %IW40001)
3. Review register mapping in Hardware → Slave Devices

### SCADA-LTS Issues

**Problem**: Data source shows "Not connected"

**Solutions**:
1. Verify `host` is set to `modbus-server` (not `localhost`)
2. Check port is `5502`
3. Enable the data source (may be disabled after import)
4. Check SCADA logs: `docker compose logs scadalts`

**Problem**: Values show as "N/A"

**Solutions**:
1. Check data point offset is `100` (not `40001`)
2. Verify multiplier is `0.01` for proper scaling
3. Enable data point logging
4. Check that Modbus server has data in register 100

### General Docker Issues

**View all logs:**
```bash
docker compose logs -f
```

**Restart everything:**
```bash
docker compose down
docker compose up -d --build
```

**Check service health:**
```bash
docker compose ps
```

**Clean restart (removes volumes):**
```bash
docker compose down -v
docker compose up -d --build
```

---

## Development

### Local Development (without Docker)

**Modbus Server:**
```bash
cd modelica-rust-modbus-server
cargo run
```

**Testing:**
```bash
# Run Rust tests
cd modelica-rust-modbus-server
cargo test -- --nocapture

# Run example client
cargo run --example simple_client
```

### Adding New Simulations

1. Create Modelica model in `modelica-rust-ffi/space-colony-modelica-core/models/`
2. Build component: `./scripts/build_component.sh YourModel`
3. Add Rust wrapper in `modelica-rust-ffi/src/components/`
4. Update `build.rs` to compile new component
5. Expose via Modbus registers in `main.rs`

### Testing Integration
```bash
# Start services
make all

# Run integration tests
cd tests
python3 integration_test.py
```

---

## Architecture Details

### Register Mapping

| Address | Type | Description | Units | R/W |
|---------|------|-------------|-------|-----|
| 100 | Holding Register | Temperature | K × 100 | R |
| 101 | Holding Register | Heater State | % (0 or 100) | R |
| 0 | Coil | Heater Control | Boolean | R/W |

### Network Topology

All services communicate via Docker network `ics`:
- `modbus-server:5502` - Physics simulation
- `openplc:502` - PLC Modbus slave
- `scadalts:8080` - SCADA web interface
- `database:3306` - MySQL backend

### Data Flow
```
User → SCADA-LTS (read temperature)
        ↓ Modbus TCP
    modbus-server:5502 (read register 100)
        ↓ FFI
    OpenModelica C Runtime (simulate physics)

User → OpenPLC (write heater control)
        ↓ Modbus TCP
    modbus-server:5502 (write coil 0)
        ↓ FFI
    OpenModelica (update heater state)
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- **Issues**: https://github.com/bondlegend4/V-ICS/issues
- **Wiki**: https://github.com/bondlegend4/V-ICS/wiki
- **Discussions**: https://github.com/bondlegend4/V-ICS/discussions

---

**V-ICS** - Virtual Industrial Control System for Education and Research