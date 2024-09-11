from pyModbusTCP.client import ModbusClient
from datetime import datetime, time

# Configure the Modbus client to connect to OpenPLC
openplc_host = '127.0.0.1'  # Change this if OpenPLC is running on another machine
modbus_client = ModbusClient(host=openplc_host, port=502)

# Irrigation parameters
watering_time = time(6, 0)  # 6:00 AM
water_per_grid = 10  # units of water per grid

# Connect to OpenPLC
if not modbus_client.is_open():
    if not modbus_client.open():
        print(f"Unable to connect to {openplc_host} on port 502")

def check_time_for_watering():
    """Check if the current time matches the watering time."""
    now = datetime.now().time()
    return now >= watering_time and now < (watering_time.replace(second=59))

def read_register(register):
    """Read a value from a Modbus register."""
    result = modbus_client.read_holding_registers(register, 1)
    return result[0] if result else None

def write_coil(coil, value):
    """Write a value to a Modbus coil."""
    success = modbus_client.write_single_coil(coil, value)
    return success

def perform_irrigation():
    """Perform the irrigation process."""
    water_available = read_register(0)  # D0 - Water available
    grids_to_water = read_register(1)  # D1 - Number of grids to water

    if water_available is not None and grids_to_water is not None:
        required_water = grids_to_water * water_per_grid

        if water_available >= required_water:
            print("Starting irrigation process...")
            # Turn on the irrigation system (set coil Q0.0)
            if write_coil(0, True):
                print(f"Irrigating {grids_to_water} grids...")
                # Simulate irrigation (e.g., sleep for a while, then turn off)
                # Turn off the irrigation system (reset coil Q0.0)
                write_coil(0, False)
                print("Irrigation complete.")
            else:
                print("Failed to turn on irrigation system.")
        else:
            print("Not enough water to irrigate.")
    else:
        print("Failed to read registers from PLC.")

# Main loop or scheduled task
if check_time_for_watering():
    perform_irrigation()
else:
    print("Not the right time for watering.")
