from pyModbusTCP.client import ModbusClient

# Configure the Modbus client
openplc_host = '127.0.0.1'  # Replace with your OpenPLC IP address if it's on another machine
modbus_client = ModbusClient(host=openplc_host, port=502)

# Connect to OpenPLC
if not modbus_client.is_open():
    if not modbus_client.open():
        print(f"Unable to connect to {openplc_host} on port 502")

# Function to read a coil
def read_coil(address):
    result = modbus_client.read_coils(address, 1)
    if result is not None:
        print(f"Coil at address {address} has value: {result[0]}")
    else:
        print(f"Failed to read coil at address {address}")

# Function to write to a coil
def write_coil(address, value):
    success = modbus_client.write_single_coil(address, value)
    if success:
        print(f"Successfully wrote {value} to coil at address {address}")
    else:
        print(f"Failed to write to coil at address {address}")

# Example usage
read_coil(0)  # Read the coil at address 0
write_coil(0, True)  # Write True (1) to the coil at address 0
read_coil(0)  # Read again to verify