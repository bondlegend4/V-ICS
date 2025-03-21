import os
import time
import threading

from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from pymodbus.exceptions import ModbusException

# Re-use the same ModbusIO class from your 'simulations/modbus_io' module
from simulations.modbus_io import ModbusIO

app = Flask(__name__)
CORS(app)

MODBUS_HOST = os.getenv("MODBUS_HOST", "127.0.0.1")
MODBUS_PORT = int(os.getenv("MODBUS_PORT", "502"))

modbus_io = ModbusIO(MODBUS_HOST, MODBUS_PORT)

connection_status = {
    "openplc_connected": False,     
    "openplc_last_read_time": 0.0,  
    "plc_error": "",
    "plc_values": {},               
    "pump_control": False,  # coil 0
    "valve_control": False, # coil 1

    "godot_connected": False,
    "godot_last_ok_time": 0.0,
}

register_history = {}
MAX_HISTORY = 50
GREEN_THRESHOLD = 10
POLL_INTERVAL = 5

def get_plc_color() -> str:
    if not connection_status["openplc_connected"]:
        return "red"
    now = time.time()
    diff = now - connection_status["openplc_last_read_time"]
    if diff < GREEN_THRESHOLD:
        return "green"
    return "yellow"

def get_godot_color() -> str:
    if not connection_status["godot_connected"]:
        return "red"
    now = time.time()
    diff = now - connection_status["godot_last_ok_time"]
    if diff < GREEN_THRESHOLD:
        return "green"
    return "yellow"

def monitor_plc_connection():
    connected = modbus_io.connect()
    if connected:
        connection_status["openplc_connected"] = True
        connection_status["plc_error"] = ""
    else:
        connection_status["openplc_connected"] = False
        connection_status["plc_error"] = f"Could not connect to PLC at {MODBUS_HOST}:{MODBUS_PORT}"

    while True:
        if not connection_status["openplc_connected"]:
            reconnected = modbus_io.connect()
            if reconnected:
                connection_status["openplc_connected"] = True
                connection_status["plc_error"] = ""
            else:
                connection_status["plc_error"] = f"Could not connect to PLC at {MODBUS_HOST}:{MODBUS_PORT}"
                time.sleep(POLL_INTERVAL)
                continue

        try:
            # 1) Read holding registers 0..4 (sensor data)
            hr_data = modbus_io.QR_plc(0, 5)
            if hr_data:
                connection_status["openplc_last_read_time"] = time.time()
                connection_status["plc_values"] = {
                    addr: val for addr, val in enumerate(hr_data)
                }
                now_ts = time.time()
                # Store rolling history
                for addr, val in enumerate(hr_data):
                    if addr not in register_history:
                        register_history[addr] = []
                    register_history[addr].append((now_ts, val))
                    if len(register_history[addr]) > MAX_HISTORY:
                        register_history[addr].pop(0)
            else:
                connection_status["plc_error"] = "Modbus read error (no holding registers)"

            # 2) Read coils 0..1 for PumpControl/ValveControl
            coil_data = modbus_io.QX_plc(0, 2)
            if coil_data is not None:
                # coil_data is a list of booleans
                connection_status["pump_control"] = coil_data[0]
                connection_status["valve_control"] = coil_data[1]

        except ModbusException as e:
            connection_status["plc_error"] = f"Modbus error: {e}"
            connection_status["openplc_connected"] = False
            modbus_io.close()

        except Exception as e:
            connection_status["plc_error"] = f"Exception: {e}"
            connection_status["openplc_connected"] = False
            modbus_io.close()

        time.sleep(POLL_INTERVAL)

threading.Thread(target=monitor_plc_connection, daemon=True).start()

@app.route("/api/ping", methods=["GET"])
def ping():
    now = time.time()
    connection_status["godot_connected"] = True
    connection_status["godot_last_ok_time"] = now
    return jsonify({"ok": True, "message": "Received ping from Godot"})

@app.route("/api/health-check", methods=["GET"])
def health_check():
    now = time.time()
    connection_status["godot_connected"] = True
    connection_status["godot_last_ok_time"] = now

    plc_color = get_plc_color()
    godot_color = get_godot_color()
    return jsonify({
        "openplc_status": plc_color,
        "openplc_error": connection_status["plc_error"],
        "openplc_values": connection_status["plc_values"],

        "pump_control": connection_status["pump_control"],
        "valve_control": connection_status["valve_control"],

        "godot_status": godot_color,
        "timestamp": time.time()
    })

@app.route("/api/register-history", methods=["GET"])
def register_history_endpoint():
    history_out = {}
    for addr, data_points in register_history.items():
        history_out[str(addr)] = data_points
    return jsonify(history_out)

@app.route("/status", methods=["GET"])
def status_page():
    plc_color = get_plc_color()
    godot_color = get_godot_color()
    plc_values = connection_status["plc_values"]

    regs_html = ""
    if plc_values:
        regs_html += "<table border='1'><tr><th>Register</th><th>Value</th></tr>"
        for addr in sorted(plc_values.keys()):
            regs_html += f"<tr><td>{addr}</td><td>{plc_values[addr]}</td></tr>"
        regs_html += "</table>"
    else:
        regs_html = "<p>No current register values.</p>"

    template = """
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        .circle {
          width: 50px;
          height: 50px;
          border-radius: 50%;
          display: inline-block;
          margin-right: 10px;
          vertical-align: middle;
        }
        table, th, td {
          border-collapse: collapse;
          padding: 6px;
        }
      </style>
    </head>
    <body>
      <h1>Connection Status</h1>
      <p>
        <strong>OpenPLC:</strong>
        <span class="circle" style="background-color: {{plc_color}};"></span>
        {{plc_color}}
      </p>
      <p>
        <strong>Godot:</strong>
        <span class="circle" style="background-color: {{godot_color}};"></span>
        {{godot_color}}
      </p>
      <h2>Current PLC Register Values</h2>
      {{regs_html | safe}}
      <h2>Coils</h2>
      <p>PumpControl (QX0.0): {{pump_control}}</p>
      <p>ValveControl (QX0.1): {{valve_control}}</p>
    </body>
    </html>
    """
    return render_template_string(
        template,
        plc_color=plc_color,
        godot_color=godot_color,
        regs_html=regs_html,
        pump_control=connection_status["pump_control"],
        valve_control=connection_status["valve_control"]
    )

###
# NEW: A simple "test run" route that writes different simulated conditions and verifies coil behavior.
###
@app.route("/api/test-run", methods=["GET"])
def run_test_scenarios():
    # Check if we're even connected to PLC
    if not connection_status["openplc_connected"]:
        return jsonify({"error": "Not connected to PLC. Cannot run tests."}), 500

    # Define a few test scenarios
    # Each scenario sets input registers [SoilMoisture, Temp, Humidity, WaterFlow, Pressure]
    # And we expect coil states [PumpControl, ValveControl] as booleans
    test_scenarios = [
        {
            "name": "Soil < Min + Tmp + Humidity",
            "ir_values": [300, 25, 50, 100, 80],  # dryness triggers pump
            "expected_pump": True,
            "expected_valve": True,
        },
    ]

    results = []
    for scenario in test_scenarios:
        scenario_result = {
            "name": scenario["name"],
            "written_ir": scenario["ir_values"],
            "expected_pump": scenario["expected_pump"],
            "expected_valve": scenario["expected_valve"],
            "actual_pump": None,
            "actual_valve": None,
            "pass": False
        }
        try:
            # 1) Write input registers 0..4
            write_result = modbus_io.IR_plc(0, len(scenario["ir_values"]), scenario["ir_values"])
            # 2) Wait a bit for the PLC to process logic
            time.sleep(2.0)
            # 3) Read coil states
            coil_data = modbus_io.QX_plc(0, 2)  # read 2 coils: pump & valve
            if coil_data is not None:
                scenario_result["actual_pump"]  = coil_data[0]
                scenario_result["actual_valve"] = coil_data[1]
                # 4) Check pass/fail
                pump_ok  = (coil_data[0] == scenario["expected_pump"])
                valve_ok = (coil_data[1] == scenario["expected_valve"])
                scenario_result["pass"] = (pump_ok and valve_ok)
            else:
                scenario_result["pass"] = False
                scenario_result["actual_pump"]  = "N/A"
                scenario_result["actual_valve"] = "N/A"
        except Exception as e:
            scenario_result["pass"] = False
            scenario_result["error"] = str(e)

        results.append(scenario_result)

    return jsonify({"test_results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
