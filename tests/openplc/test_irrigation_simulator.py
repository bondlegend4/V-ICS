import time
from modbus_io import ModbusIO
from irrigation_simulator import IrrigationSimulation
from pymodbus.exceptions import ModbusException

# Define the address mapping based on Modbus register addresses (same as simulation)
MODBUS_REGISTERS = {
    'SoilMoisture': 0,
    'Temperature': 1,
    'Humidity': 2,
    'WaterFlow': 3,
    'Pressure': 4
}

MODBUS_COILS = {
    'PumpControl': 0,
    'ValveControl': 1
}

# Function to read and test Modbus data
def test_modbus_system(modbus_io, simulator):
    try:
        # Loop to continuously test Modbus outputs
        while True:
            # Simulate sensor values
            modbus_io.IR_plc(MODBUS_REGISTERS['SoilMoisture'], 1, [simulator.simulate_soil_moisture()])
            modbus_io.IR_plc(MODBUS_REGISTERS['Temperature'], 1, [simulator.simulate_temperature()])
            modbus_io.IR_plc(MODBUS_REGISTERS['Humidity'], 1, [simulator.simulate_humidity()])
            modbus_io.IR_plc(MODBUS_REGISTERS['WaterFlow'], 1, [simulator.simulate_water_flow()])
            modbus_io.IR_plc(MODBUS_REGISTERS['Pressure'], 1, [simulator.simulate_pressure()])

            # Read sensor values from the Modbus registers
            soil_moisture = modbus_io.QR_plc(MODBUS_REGISTERS['SoilMoisture'], 1)[0]
            temperature = modbus_io.QR_plc(MODBUS_REGISTERS['Temperature'], 1)[0]
            humidity = modbus_io.QR_plc(MODBUS_REGISTERS['Humidity'], 1)[0]
            water_flow = modbus_io.QR_plc(MODBUS_REGISTERS['WaterFlow'], 1)[0]
            pressure = modbus_io.QR_plc(MODBUS_REGISTERS['Pressure'], 1)[0]
            
            # Read coil states for pump and valve control
            modbus_output = modbus_io.QX_plc(MODBUS_COILS['PumpControl'], 2)
            pump_control = modbus_output[0]
            valve_control = modbus_output[1]
            
            # Print the Modbus register and coil values
            print(f"Sensor Data -> Soil Moisture: {soil_moisture}, Temperature: {temperature}, Humidity: {humidity}, Water Flow: {water_flow}, Pressure: {pressure}")
            print(f"Actuator Control -> Pump: {'ON' if pump_control else 'OFF'}, Valve: {'OPEN' if valve_control else 'CLOSED'}")
            
            # Check if the values are within expected ranges
            assert 300 <= soil_moisture <= 800, "Soil Moisture out of range!"
            assert 20 <= temperature <= 40, "Temperature out of range!"
            assert 50 <= humidity <= 90, "Humidity out of range!"
            assert 500 <= water_flow <= 1000, "Water Flow out of range!"
            assert 50 <= pressure <= 150, "Pressure out of range!"
            
            # Print confirmation
            print("All values are within the expected range.\n")
            
            # Wait before next check (adjust as necessary)
            time.sleep(1)

    except AssertionError as e:
        print(f"Test failed: {e}")
    except ModbusException as e:
        print(f"Modbus error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        modbus_io.close()

# Run the Modbus test
if __name__ == "__main__":
    # Instantiate simulator and ModbusIO
    simulator = IrrigationSimulation()
    modbus_io = ModbusIO('127.0.0.1', 502)
    
    if modbus_io.connect():
        print("Connected to Modbus server")
        test_modbus_system(modbus_io, simulator)
    else:
        print("Failed to connect to Modbus server")
