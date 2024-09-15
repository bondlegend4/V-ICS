import time
from irrigation_simulator import IrrigationSimulation
from modbus_io import ModbusIO

# Instantiate simulator and ModbusIO
simulator = IrrigationSimulation()
modbus_io = ModbusIO('127.0.0.1', 502)

try:
    if modbus_io.connect():
        print("Connected to Modbus server")
        while True:
            # Simulate sensor values
            soil_moisture = simulator.simulate_soil_moisture()
            temperature = simulator.simulate_temperature()
            humidity = simulator.simulate_humidity()
            water_flow = simulator.simulate_water_flow()
            pressure = simulator.simulate_pressure()

            # Write sensor values to Modbus registers
            modbus_io.write_input_register(0, [soil_moisture])
            modbus_io.write_input_register(1, [temperature])
            modbus_io.write_input_register(2, [humidity])
            modbus_io.write_input_register(3, [water_flow])
            modbus_io.write_input_register(4, [pressure])

            time.sleep(1)
    else:
        print("Failed to connect to Modbus server")

except ModbusException as e:
    print(f"Modbus error: {e}")

finally:
    modbus_io.close()
    print("Connection closed")
