from pymodbus.client.sync import ModbusTcpClient
import time

# Modbus client setup to connect to the PLC (assuming same IP and port)
client = ModbusTcpClient('127.0.0.1')  # Replace with PLC IP if different

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
def test_modbus_system():
    try:
        # Loop to continuously test Modbus outputs
        while True:
            # Read sensor values from the Modbus registers
            soil_moisture = client.read_holding_registers(MODBUS_REGISTERS['SoilMoisture'], 1).registers[0]
            temperature = client.read_holding_registers(MODBUS_REGISTERS['Temperature'], 1).registers[0]
            humidity = client.read_holding_registers(MODBUS_REGISTERS['Humidity'], 1).registers[0]
            water_flow = client.read_holding_registers(MODBUS_REGISTERS['WaterFlow'], 1).registers[0]
            pressure = client.read_holding_registers(MODBUS_REGISTERS['Pressure'], 1).registers[0]
            
            # Read coil states for pump and valve control
            modbus_output = client.read_coils(MODBUS_COILS['PumpControl'], 2)
            pump_control = modbus_output.bits[0]
            valve_control = modbus_output.bits[1]
            
            # Print the Modbus register and coil values
            print(f"Sensor Data -> Soil Moisture: {soil_moisture}, Temperature: {temperature}, Humidity: {humidity}, Water Flow: {water_flow}, Pressure: {pressure}")
            print(f"Actuator Control -> Pump: {'ON' if pump_control else 'OFF'}, Valve: {'OPEN' if valve_control else 'CLOSED'}")
            
            # Check if the values are within expected ranges
            assert 200 <= soil_moisture <= 800, "Soil Moisture out of range!"
            assert 1500 <= temperature <= 3000, "Temperature out of range!"
            assert 4000 <= humidity <= 8000, "Humidity out of range!"
            assert 10 <= water_flow <= 100, "Water Flow out of range!"
            assert 50 <= pressure <= 150, "Pressure out of range!"
            
            # Print confirmation
            print("All values are within the expected range.\n")
            
            # Wait before next check (adjust as necessary)
            time.sleep(1)

    except AssertionError as e:
        print(f"Test failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

# Run the Modbus test
if __name__ == "__main__":
    test_modbus_system()