from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

# Create Modbus client instance
client = ModbusTcpClient('127.0.0.1', port=502)

try:
    # Establish connection
    if client.connect():
        print("Connected to Modbus server")

        # Step 1: Read from the input register (Modbus address 0)
        output_register_address = 0  # %IW0.0 in the PLC is Modbus address 0
        result = client.read_holding_registers(output_register_address, 1)
        output_value = result.registers[0]
        if not result.isError():  # Check if the read was successful
            print(f"Read value from output register %QW0.0: {output_value}")
        else:
            print(f"Error reading output register: {read_result}")

        # Step 2: Write the value to the output register (holding register)
        input_register_address = 0  # %QW0.0 in the PLC is Modbus address 0
        write_result = client.write_register(input_register_address, output_value+1)
        if not write_result.isError():  # Check if the write was successful
            print(f"Wrote value to output register %IW0.0: {write_result}")
        else:
            print(f"Error writing to output register: {write_result}")
        
        
        # Step 3: Read from the input register (Modbus address 0)
        output_register_address = 0  # %IW0.0 in the PLC is Modbus address 0
        result = client.read_holding_registers(output_register_address, 1)
        output_value = result.registers[0]
        if not result.isError():  # Check if the read was successful
            print(f"Read value from output register %QW0.0: {output_value}")
        else:
            print(f"Error reading output register: {read_result}")
    else:
        print("Failed to connect to Modbus server")

except ModbusException as e:
    print(f"Modbus error: {e}")

finally:
    # Close the client connection
    client.close()
    print("Connection closed")
