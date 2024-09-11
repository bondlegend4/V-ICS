import time
import matplotlib.pyplot as plt
from pymodbus.client.sync import ModbusTcpClient
from collections import deque

# Modbus connection details
PLC_HOST = "localhost"  # Modbus server host (localhost if running locally)
PLC_PORT = 5020         # Modbus server port

# Create a Modbus client instance
client = ModbusTcpClient(PLC_HOST, PLC_PORT)

# Number of data points to display in the graph at once
BUFFER_SIZE = 50

# Queues to store real-time data for each sensor
soil_moisture_data = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
temperature_data = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
pressure_data = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)
water_flow_data = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

# Initialize the plot
plt.ion()  # Interactive mode on
fig, axs = plt.subplots(2, 2, figsize=(10, 8))

def update_plot():
    # Clear the previous plots
    for ax in axs.flat:
        ax.clear()

    # Plot soil moisture
    axs[0, 0].plot(soil_moisture_data, label="Soil Moisture", color='blue')
    axs[0, 0].set_title('Soil Moisture')
    axs[0, 0].set_ylim([200, 900])

    # Plot temperature
    axs[0, 1].plot(temperature_data, label="Temperature", color='red')
    axs[0, 1].set_title('Temperature (Celsius)')
    axs[0, 1].set_ylim([10, 45])

    # Plot pressure
    axs[1, 0].plot(pressure_data, label="Pressure", color='green')
    axs[1, 0].set_title('Pressure (psi)')
    axs[1, 0].set_ylim([30, 160])

    # Plot water flow
    axs[1, 1].plot(water_flow_data, label="Water Flow", color='orange')
    axs[1, 1].set_title('Water Flow (Liters/hour)')
    axs[1, 1].set_ylim([400, 1100])

    # Update the plots
    for ax in axs.flat:
        ax.legend()
        ax.grid(True)

    # Draw the updated plots
    plt.draw()
    plt.pause(0.01)  # Small pause to allow for real-time updating

def read_modbus_traffic():
    while True:
        # Read sensor values from Modbus server
        soil_moisture = client.read_holding_registers(0, 1).registers[0]  # Soil Moisture (register 0)
        temperature = client.read_holding_registers(1, 1).registers[0]    # Temperature (register 1)
        pressure = client.read_holding_registers(4, 1).registers[0]       # Pressure (register 4)
        water_flow = client.read_holding_registers(3, 1).registers[0]     # Water Flow (register 3)

        # Append the values to the respective data queues
        soil_moisture_data.append(soil_moisture)
        temperature_data.append(temperature)
        pressure_data.append(pressure)
        water_flow_data.append(water_flow)

        # Print the received values in the terminal for reference
        print(f"Soil Moisture: {soil_moisture}, Temperature: {temperature}, Pressure: {pressure}, Water Flow: {water_flow}")

        # Update the plot with new data
        update_plot()

        # Wait before reading the next set of values (adjust time as needed)
        time.sleep(1)

if __name__ == "__main__":
    try:
        # Start reading Modbus traffic and plotting
        read_modbus_traffic()
    except KeyboardInterrupt:
        print("Modbus client stopped.")
    finally:
        # Close the Modbus client connection when done
        client.close()
