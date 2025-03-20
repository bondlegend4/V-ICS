# main.py
import os
import time
from irrigation_simulator import IrrigationSimulation
from modbus_io import ModbusIO
from pymodbus.exceptions import ModbusException

# Read environment variables
MODBUS_HOST = os.getenv("MODBUS_HOST", "127.0.0.1")
MODBUS_PORT = int(os.getenv("MODBUS_PORT", "502"))

# Instantiate simulator and ModbusIO
simulator = IrrigationSimulation()
modbus_io = ModbusIO(MODBUS_HOST, MODBUS_PORT)

try:
    if modbus_io.connect():
        print(f"Connected to Modbus server at {MODBUS_HOST}:{MODBUS_PORT}")
        while True:
            # Simulate sensor values
            soil_moisture = simulator.simulate_soil_moisture()
            temperature = simulator.simulate_temperature()
            humidity = simulator.simulate_humidity()
            water_flow = simulator.simulate_water_flow()
            pressure = simulator.simulate_pressure()

            # Write sensor values to Modbus registers
            modbus_io.IR_plc(0, 1, [soil_moisture])
            modbus_io.IR_plc(1, 1, [temperature])
            modbus_io.IR_plc(2, 1, [humidity])
            modbus_io.IR_plc(3, 1, [water_flow])
            modbus_io.IR_plc(4, 1, [pressure])

            time.sleep(1)
    else:
        print("Failed to connect to Modbus server")

except ModbusException as e:
    print(f"Modbus error: {e}")

finally:
    modbus_io.close()
    print("Connection closed")