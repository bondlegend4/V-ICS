from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import random
import time

# Create Modbus client instance
client = ModbusTcpClient('127.0.0.1', port=502)

def IX_plc (register, count, input_values):
    # Write `value` to coil at `address`.
    input_register_address = 0  # %QW0.0 in the PLC is Modbus address 0
    write_result = client.write_coils(input_register_address, count, input_values)
    if not write_result.isError():  # Check if the write was successful
        print(f"Wrote value to input register %IW0.0: {write_result}")
    else:
        print(f"Error writing to output register: {write_result}")

def QX_plc (output_register_address, count, client):
    # Reads `count` coils from a given slave starting at `address`.
    read_result = client.read_coils(output_register_address, count, client)
    output_value = read_result.registers
    if not write_result.isError():  # Check if the write was successful
        print(f"Wrote value to output register %QW0.0: {output_value}")
    else:
        print(f"Error writing to output register: {read_result}")

def IR_plc (input_register_address, count, input_values):
    # Write list of `values` to registers starting at `address`.
    write_result = client.write_register(input_register_address, count, input_values)
    if not write_result.isError():  # Check if the write was successful
        print(f"Wrote value to input register %IW0.0: {write_result}")
    else:
        print(f"Error writing to output register: {write_result}")

def QR_plc (output_register_address, count):
    # Read `count` number of holding registers starting at `address`.
    read_result = client.read_holding_registers(output_register_address, count)
    output_value = read_result.registers
    if not write_result.isError():  # Check if the write was successful
        print(f"Wrote value to output register %QW0.0: {output_value}")
    else:
        print(f"Error writing to output register: {read_result}")
try:
    # Establish connection
    if client.connect():
        print("Connected to Modbus server")
        while True:
            # Simulate Soil Moisture (register 0)
            soil_moisture = random.randint(300, 800)  # Simulate analog value between 300 and 800
            IR_plc(0, 1, [soil_moisture])

            # Simulate Temperature (register 1)
            temperature = random.randint(20, 40)  # Simulate analog temperature in Celsius
            IR_plc(1, 1, [temperature])

            # Simulate Humidity (register 2)
            humidity = random.randint(50, 90)  # Simulate humidity percentage
            IR_plc(2, 1, [humidity])

            # Simulate Water Flow (register 3)
            water_flow = random.randint(500, 1000)  # Flow rate in liters per hour
            IR_plc(3, 1, [water_flow])

            # Simulate Pressure (register 4)
            pressure = random.randint(50, 150)  # Pressure in psi
            IR_plc(4, 1, [pressure])

            time.sleep(1)  # Update every second

    else:
        print("Failed to connect to Modbus server")

except ModbusException as e:
    print(f"Modbus error: {e}")

finally:
    # Close the client connection
    client.close()
    print("Connection closed")
