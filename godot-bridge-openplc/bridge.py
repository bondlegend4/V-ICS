import os
import time
import threading
import json

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

# ----------------------------------------------------------------
# GLOBAL CONNECTION + PLC TRACKING
# ----------------------------------------------------------------
connection_status = {
    "openplc_connected": False,
    "openplc_last_read_time": 0.0,
    "plc_error": "",
    "plc_values": {},       # sensor registers read from the PLC
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
    """
    Returns 'green' if last PLC read was < GREEN_THRESHOLD seconds ago,
    'yellow' if connected but stale,
    'red' if not connected at all.
    """
    if not connection_status["openplc_connected"]:
        return "red"
    now = time.time()
    diff = now - connection_status["openplc_last_read_time"]
    if diff < GREEN_THRESHOLD:
        return "green"
    return "yellow"

def get_godot_color() -> str:
    """
    Similar logic for Godot heartbeats (via /api/health-check or /api/ping).
    """
    if not connection_status["godot_connected"]:
        return "red"
    now = time.time()
    diff = now - connection_status["godot_last_ok_time"]
    if diff < GREEN_THRESHOLD:
        return "green"
    return "yellow"

def monitor_plc_connection():
    """
    Continually tries to connect to the PLC, read registers/coils every POLL_INTERVAL,
    and store them in connection_status.
    """
    if modbus_io.connect():
        connection_status["openplc_connected"] = True
        connection_status["plc_error"] = ""
    else:
        connection_status["openplc_connected"] = False
        connection_status["plc_error"] = f"Could not connect to PLC at {MODBUS_HOST}:{MODBUS_PORT}"

    while True:
        if not connection_status["openplc_connected"]:
            # Attempt reconnect
            if modbus_io.connect():
                connection_status["openplc_connected"] = True
                connection_status["plc_error"] = ""
            else:
                connection_status["plc_error"] = f"Could not connect to PLC at {MODBUS_HOST}:{MODBUS_PORT}"
                time.sleep(POLL_INTERVAL)
                continue

        try:
            # 1) Read holding registers 0..4
            hr_data = modbus_io.QR_plc(0, 5)
            if hr_data:
                connection_status["openplc_last_read_time"] = time.time()
                connection_status["plc_values"] = {addr: val for addr, val in enumerate(hr_data)}
                now_ts = time.time()
                # Keep rolling history
                for addr, val in enumerate(hr_data):
                    if addr not in register_history:
                        register_history[addr] = []
                    register_history[addr].append((now_ts, val))
                    if len(register_history[addr]) > MAX_HISTORY:
                        register_history[addr].pop(0)
            else:
                connection_status["plc_error"] = "Modbus read error (no holding registers)"

            # 2) Read coils 0..1 => PumpControl/ValveControl
            coil_data = modbus_io.QX_plc(0, 2)
            if coil_data is not None and len(coil_data) == 2:
                connection_status["pump_control"]  = coil_data[0]
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

# ----------------------------------------------------------------
# ROUTES: Basic status & health
# ----------------------------------------------------------------

@app.route("/api/ping", methods=["GET"])
def ping():
    """
    Godot can ping this to indicate it's alive.
    """
    now = time.time()
    connection_status["godot_connected"] = True
    connection_status["godot_last_ok_time"] = now
    return jsonify({"ok": True, "message": "Received ping from Godot"})

@app.route("/api/health-check", methods=["GET"])
def health_check():
    """
    Another route for Godot to confirm it can see the PLC status.
    """
    now = time.time()
    connection_status["godot_connected"] = True
    connection_status["godot_last_ok_time"] = now

    return jsonify({
        "openplc_status": get_plc_color(),
        "openplc_error": connection_status["plc_error"],
        "openplc_values": connection_status["plc_values"],
        "pump_control": connection_status["pump_control"],
        "valve_control": connection_status["valve_control"],
        "godot_status": get_godot_color(),
        "timestamp": time.time()
    })

@app.route("/api/register-history", methods=["GET"])
def register_history_endpoint():
    """
    Returns a JSON array of time-stamped register values for debugging.
    """
    history_out = {}
    for addr, data_points in register_history.items():
        history_out[str(addr)] = data_points
    return jsonify(history_out)

# ----------------------------------------------------------------
# ROUTE: Status page with color-coded indicators
# ----------------------------------------------------------------

@app.route("/status", methods=["GET"])
def status_page():
    plc_color = get_plc_color()
    godot_color = get_godot_color()
    plc_values = connection_status["plc_values"]

    # Build an HTML table of registers
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
        nav a {
          margin-right: 20px;
        }
      </style>
    </head>
    <body>
      <nav>
        <a href="/status">Status</a>
        <a href="/test">Test</a>
      </nav>
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

# ----------------------------------------------------------------
# BASIC TEST-RUN EXAMPLE: /api/test-run
# ----------------------------------------------------------------

@app.route("/api/test-run", methods=["GET"])
def run_test_scenarios():
    """
    Demonstrates a quick approach: define one or more test scenarios,
    write them to the PLC, read coil states, return JSON only.
    This approach does not create a UI, just raw JSON.
    """
    if not connection_status["openplc_connected"]:
        return jsonify({"error": "Not connected to PLC. Cannot run tests."}), 500

    test_scenarios_quick = [
        {
            "name": "Soil < Min => Pump On",
            "ir_values": [300, 25, 50, 100, 80],
            "expected_pump": True,
            "expected_valve": True,
        },
    ]

    results = []
    for scenario in test_scenarios_quick:
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
            # Write input registers 0..4
            modbus_io.IR_plc(0, len(scenario["ir_values"]), scenario["ir_values"])
            # Wait for PLC logic to update
            time.sleep(2.0)

            coil_data = modbus_io.QX_plc(0, 2)
            if coil_data is not None and len(coil_data) == 2:
                scenario_result["actual_pump"]  = coil_data[0]
                scenario_result["actual_valve"] = coil_data[1]
                pump_ok  = (coil_data[0] == scenario["expected_pump"])
                valve_ok = (coil_data[1] == scenario["expected_valve"])
                scenario_result["pass"] = (pump_ok and valve_ok)
            else:
                scenario_result["pass"] = False

        except Exception as e:
            scenario_result["pass"] = False
            scenario_result["error"] = str(e)

        results.append(scenario_result)

    return jsonify({"test_results": results})

# ----------------------------------------------------------------
# FULL SINGLE-PAGE TEST SCENARIOS ( /test ) with multiple scenarios
# ----------------------------------------------------------------

# You can define multiple scenarios here:
test_scenarios = {
    1: {
        "name": "Low moisture, high temp => Expect Pump ON, Valve ON",
        "values": [300, 40, 40, 500, 90],
        "expected_pump": True,
        "expected_valve": True
    },
    2: {
        "name": "High moisture, normal temp => Expect Pump OFF, Valve OFF",
        "values": [700, 25, 60, 300, 80],
        "expected_pump": False,
        "expected_valve": False
    }
}

# Each scenario's test results: started, coil_pass, visual_pass, failed
test_results = {
    1: {"started": False, "coil_pass": False, "visual_pass": False, "failed": False},
    2: {"started": False, "coil_pass": False, "visual_pass": False, "failed": False}
}

@app.route("/api/test-scenario/<int:scenario_id>", methods=["POST"])
def run_test_scenario(scenario_id: int):
    """
    Write the scenario's sensor values, then read coil states to see if they match
    expected_pump/valve. Return JSON. The front-end updates in place (AJAX).
    """
    if scenario_id not in test_scenarios:
        return jsonify({"error": "Invalid scenario ID"}), 400

    scenario = test_scenarios[scenario_id]
    tdata = test_results[scenario_id]

    # Reset test info
    tdata["started"] = True
    tdata["failed"] = False
    tdata["coil_pass"] = False
    tdata["visual_pass"] = False

    try:
        modbus_io.IR_plc(0, 5, scenario["values"])
        time.sleep(1.0)

        coil_data = modbus_io.QX_plc(0, 2)
        if coil_data is not None and len(coil_data) == 2:
            pump_state, valve_state = coil_data
            if (pump_state == scenario["expected_pump"] and
                valve_state == scenario["expected_valve"]):
                tdata["coil_pass"] = True
            else:
                tdata["failed"] = True
        else:
            tdata["failed"] = True

    except Exception as e:
        tdata["failed"] = True
        return jsonify({"error": str(e)}), 500

    return jsonify({"test_results": tdata})

@app.route("/api/test-check/<int:scenario_id>", methods=["POST"])
def test_check(scenario_id: int):
    """
    The user hits 'Visual Pass' or 'Visual Fail' for the scenario.
    POST body = { "type": "visual", "pass": <true|false> }
    """
    if scenario_id not in test_scenarios:
        return jsonify({"error": "Invalid scenario ID"}), 400

    body = request.json or {}
    check_type = body.get("type", "")
    pass_bool = body.get("pass", False)

    tdata = test_results[scenario_id]
    if check_type == "visual":
        if pass_bool:
            tdata["visual_pass"] = True
        else:
            tdata["failed"] = True

    return jsonify({"test_results": tdata})

@app.route("/test", methods=["GET"])
def test_page():
    """
    Single-page scenario test UI. 
    We'll embed scenario+results as JSON, plus a bit of JS to do AJAX calls.
    Also add a nav link back to /status.
    """
    scenario_data_json = json.dumps(test_scenarios)
    test_results_json = json.dumps(test_results)

    # Using standard string concatenation (no backticks) for compatibility
    html = """
<!DOCTYPE html>
<html>
<head>
  <title>OpenPLC / Godot Test Scenarios</title>
  <style>
    .scenario {
      border: 1px solid #ccc;
      margin: 10px;
      padding: 10px;
    }
    .fail {
      color: red;
    }
    .pass {
      color: green;
    }
    button {
      margin-right: 5px;
    }
    nav a {
      margin-right: 20px;
    }
  </style>
</head>
<body>
  <nav>
    <a href="/status">Status</a>
    <a href="/test">Test</a>
  </nav>
  <h1>OpenPLC / Godot Test Scenarios</h1>

  <div id="scenario-container"></div>

  <script>
    var scenarios = """ + scenario_data_json + """;
    var testResults = """ + test_results_json + """;

    function renderScenarios() {
      var container = document.getElementById("scenario-container");
      container.innerHTML = "";

      for (var sid in scenarios) {
        var scenario = scenarios[sid];
        var result = testResults[sid];

        var scenarioDiv = document.createElement("div");
        scenarioDiv.className = "scenario";

        // Title
        var title = document.createElement("h3");
        title.textContent = "Scenario " + sid + ": " + scenario.name;
        scenarioDiv.appendChild(title);

        // Sensor values
        var valP = document.createElement("p");
        valP.innerHTML = "<strong>Sensor Values:</strong> [Soil=" + scenario.values[0] + 
                         ", Temp=" + scenario.values[1] + 
                         ", Hum=" + scenario.values[2] + 
                         ", Flow=" + scenario.values[3] + 
                         ", Pressure=" + scenario.values[4] + "]";
        scenarioDiv.appendChild(valP);

        // Expected coil states
        var expP = document.createElement("p");
        expP.innerHTML = "<strong>Expected Pump:</strong> " + scenario.expected_pump +
                         ", <strong>Expected Valve:</strong> " + scenario.expected_valve;
        scenarioDiv.appendChild(expP);

        // Coil check
        var coilP = document.createElement("p");
        coilP.innerHTML = "<strong>Coil Check:</strong> ";
        if (result.failed) {
          coilP.innerHTML += '<span class="fail">FAIL</span>';
        } else if (!result.started) {
          coilP.innerHTML += "Not Started";
        } else if (result.coil_pass) {
          coilP.innerHTML += '<span class="pass">PASS</span>';
        } else {
          coilP.innerHTML += "Ongoing";
        }
        scenarioDiv.appendChild(coilP);

        // Visual check
        var visP = document.createElement("p");
        visP.innerHTML = "<strong>Visual Check:</strong> ";
        if (result.failed) {
          visP.innerHTML += '<span class="fail">FAIL</span>';
        } else if (!result.started) {
          visP.innerHTML += "Not Started";
        } else if (result.visual_pass) {
          visP.innerHTML += '<span class="pass">PASS</span>';
        } else {
          // If started but not passed => show pass/fail buttons
          visP.innerHTML += '<button onclick="sendVisualCheck(' + sid + ', true)">Visual Pass</button>'
                         + '<button onclick="sendVisualCheck(' + sid + ', false)">Visual Fail</button>';
        }
        scenarioDiv.appendChild(visP);

        // Overall scenario result
        var overallP = document.createElement("p");
        overallP.innerHTML = "<strong>Scenario Result:</strong> ";
        var coilPass = result.coil_pass;
        var visPass = result.visual_pass;
        if (result.failed) {
          overallP.innerHTML += '<span class="fail">FAILED</span>';
        } else if (result.started && coilPass && visPass) {
          overallP.innerHTML += '<span class="pass">PASSED</span>';
        } else if (result.started) {
          overallP.innerHTML += "Ongoing";
        } else {
          overallP.innerHTML += "Not Started";
        }
        scenarioDiv.appendChild(overallP);

        // Start test button
        var btnDiv = document.createElement("p");
        var startBtn = document.createElement("button");
        startBtn.textContent = "Start Test";
        startBtn.onclick = (function(id) {
          return function() {
            startTestScenario(id);
          }
        })(sid);
        btnDiv.appendChild(startBtn);

        scenarioDiv.appendChild(btnDiv);
        container.appendChild(scenarioDiv);
      }
    }

    function startTestScenario(sid) {
      fetch("/api/test-scenario/" + sid, {
        method: "POST"
      })
      .then(function(resp) { return resp.json(); })
      .then(function(data) {
        if (data.error) {
          alert("Error: " + data.error);
        } else {
          testResults[sid] = data.test_results;
          renderScenarios();
        }
      })
      .catch(function(err) {
        console.error(err);
      });
    }

    function sendVisualCheck(sid, passVal) {
      fetch("/api/test-check/" + sid, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ type: "visual", pass: passVal })
      })
      .then(function(resp) { return resp.json(); })
      .then(function(data) {
        if (data.error) {
          alert("Error: " + data.error);
        } else {
          testResults[sid] = data.test_results;
          renderScenarios();
        }
      })
      .catch(function(err) {
        console.error(err);
      });
    }

    document.addEventListener("DOMContentLoaded", renderScenarios);
  </script>
</body>
</html>
    """
    return render_template_string(html)

# ----------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
