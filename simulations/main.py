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
            # 1) Read the pump and valve states from the PLC (coils)
            #    Let's assume:
            #    PumpControl is coil %QX0.0 => read_coils(address=0, count=1)
            #    ValveControl is coil %QX0.1 => read_coils(address=1, count=1)
            #    For convenience, we'll do them in a single read_coils if your PLC supports that.
            #    Or read them separately as needed:
            pump_state_bits = modbus_io.QX_plc(0, 1)  # Returns a list of bits
            valve_state_bits = modbus_io.QX_plc(1, 1)
            
            if pump_state_bits is not None and valve_state_bits is not None:
                pump_on = pump_state_bits[0]
                valve_open = valve_state_bits[0]
            else:
                # Default to false if read error
                pump_on = False
                valve_open = False
            
            # 2) Update sensor readings based on the pump/valve states + atmospheric conditions
            soil_moisture, temperature, humidity, water_flow, pressure = \
                simulator.update_sensors(pump_on, valve_open)

            # 3) Write sensor values to Modbus registers
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