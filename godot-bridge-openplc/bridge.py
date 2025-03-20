import os
import time
import threading

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
from pymodbus.exceptions import ModbusException

# Import your existing ModbusIO class
from simulations.modbus_io import ModbusIO

app = Flask(__name__)
CORS(app)

# Read environment variables for Modbus host/port
MODBUS_HOST = os.getenv("MODBUS_HOST", "127.0.0.1")
MODBUS_PORT = int(os.getenv("MODBUS_PORT", "502"))

# Create a single ModbusIO instance we can reuse.
modbus_io = ModbusIO(MODBUS_HOST, MODBUS_PORT)

# Dictionary to track connection status & PLC reads
connection_status = {
    "openplc_last_ok_time": 0.0,
    "plc_error": "",
    "plc_value": None,
}

GREEN_THRESHOLD = 10    # in seconds => green if last update < 10s
YELLOW_THRESHOLD = 30   # in seconds => yellow if 10-30s

def get_color_for_timestamp(last_ok: float) -> str:
    """
    Returns 'green', 'yellow', or 'red' based on
    how long it's been since 'last_ok'.
    """
    now = time.time()
    diff = now - last_ok
    if diff < GREEN_THRESHOLD:
        return "green"
    elif diff < YELLOW_THRESHOLD:
        return "yellow"
    return "red"

def monitor_plc_connection():
    """
    Background thread that connects to the PLC, reads holding registers,
    and updates 'connection_status' every few seconds.
    """
    global connection_status

    while True:
        connected = modbus_io.connect()
        if not connected:
            connection_status["plc_error"] = f"Could not connect to PLC at {MODBUS_HOST}:{MODBUS_PORT}"
        else:
            try:
                # Example: read 1 holding register from address 0
                # since your simulation writes IR_plc(0, 1, [value])
                # which uses "write_registers(0, ...)" => holding register #0
                read_result = modbus_io.QR_plc(0, 1)
                if read_result:
                    connection_status["plc_value"] = read_result[0]
                    connection_status["openplc_last_ok_time"] = time.time()
                    connection_status["plc_error"] = ""
                else:
                    connection_status["plc_error"] = "Modbus read error (empty result)"
            except ModbusException as e:
                connection_status["plc_error"] = f"Modbus error: {e}"
            except Exception as e:
                connection_status["plc_error"] = f"Exception: {e}"
            finally:
                # Close after each cycle (optional).
                # Some prefer to hold it open if you poll frequently.
                modbus_io.close()

        time.sleep(5)  # Wait 5s before next read

# Start the monitoring thread
threading.Thread(target=monitor_plc_connection, daemon=True).start()

@app.route("/api/health-check", methods=["GET"])
def health_check():
    """
    Returns a simple JSON with the last read value
    and the connection status (color-coded by time).
    """
    now = time.time()
    plc_color = get_color_for_timestamp(connection_status["openplc_last_ok_time"])

    return jsonify({
        "plc_value": connection_status["plc_value"],
        "plc_error": connection_status["plc_error"],
        "plc_status": plc_color,
        "timestamp": now
    })

@app.route("/status", methods=["GET"])
def status_page():
    """
    A simple inline HTML page showing red/yellow/green for PLC status.
    """
    plc_color = get_color_for_timestamp(connection_status["openplc_last_ok_time"])
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
      </style>
    </head>
    <body>
      <h1>PLC Connection Status</h1>
      <p>PLC: 
         <span class="circle" style="background-color: {{plc_color}};"></span>
         {{plc_color}}
      </p>
    </body>
    </html>
    """
    return render_template_string(template, plc_color=plc_color)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
