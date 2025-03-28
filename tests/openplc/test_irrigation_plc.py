import time
import matplotlib.pyplot as plt
from modbus_io import ModbusIO
from irrigation_simulator import IrrigationSimulation

# Simulated Sensor Values
soil_moisture_values = []
temperature_values = []
pressure_values = []
flow_values = []

# PLC Response (Pump and Valve)
pump_states = []
valve_states = []

# ModbusIO setup
modbus_io = ModbusIO('127.0.0.1', 502)
simulator = IrrigationSimulation()

# Simulate and test data
def generate_and_test_plc():
    if not modbus_io.connect():
        print("Failed to connect to Modbus server")
        return

    for i in range(20):  # Simulate 20 data points
        # Generate random values for the sensors using the simulator
        soil_moisture = simulator.simulate_soil_moisture()
        temperature = simulator.simulate_temperature()
        pressure = simulator.simulate_pressure()
        water_flow = simulator.simulate_water_flow()

        # Send values to PLC via Modbus registers
        modbus_io.IR_plc(0, 1, [soil_moisture])  # Soil Moisture in Register 0
        modbus_io.IR_plc(1, 1, [temperature])    # Temperature in Register 1
        modbus_io.IR_plc(2, 1, [pressure])       # Pressure in Register 2
        modbus_io.IR_plc(3, 1, [water_flow])     # Water Flow in Register 3

        # Store sensor values for plotting
        soil_moisture_values.append(soil_moisture)
        temperature_values.append(temperature)
        pressure_values.append(pressure)
        flow_values.append(water_flow)

        # Wait for PLC to process and read output (Pump and Valve states)
        time.sleep(1)  # Give PLC time to process

        # Read pump and valve states from Modbus coils
        pump_control = modbus_io.QX_plc(0, 1, [0])  # Pump Control at Coil 0
        valve_control = modbus_io.QX_plc(1, 1, [0])  # Valve Control at Coil 1

        # Store PLC outputs for plotting
        pump_states.append(pump_control)
        valve_states.append(valve_control)

        # Print the test results in the terminal
        print(f"Test {i+1}: Soil Moisture: {soil_moisture}, Temperature: {temperature}, Pressure: {pressure}, Flow: {water_flow}")
        print(f"Pump State: {'ON' if pump_control else 'OFF'}, Valve State: {'ON' if valve_control else 'OFF'}")
        print("-" * 50)

    # Close Modbus client
    modbus_io.close()

# Function to plot results
def plot_results():
    x = list(range(1, 21))  # Test steps (1 to 20)
    
    # Create subplots
    fig, axs = plt.subplots(3, figsize=(10, 8))
    
    # Plot sensor values
    axs[0].plot(x, soil_moisture_values, label="Soil Moisture", marker="o")
    axs[0].plot(x, temperature_values, label="Temperature", marker="x")
    axs[0].plot(x, pressure_values, label="Pressure", marker="s")
    axs[0].plot(x, flow_values, label="Water Flow", marker="^")
    axs[0].set_title("Sensor Values")
    axs[0].set_ylabel("Values")
    axs[0].legend()
    
    # Plot pump states
    axs[1].plot(x, pump_states, label="Pump State", marker="o", color="blue")
    axs[1].set_title("Pump Control")
    axs[1].set_ylabel("State (ON=1, OFF=0)")
    
    # Plot valve states
    axs[2].plot(x, valve_states, label="Valve State", marker="x", color="red")
    axs[2].set_title("Valve Control")
    axs[2].set_ylabel("State (ON=1, OFF=0)")

    # Set common labels
    for ax in axs:
        ax.set_xlabel("Test Step")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    generate_and_test_plc()  # Simulate and test the PLC
    plot_results()           # Plot the results graphically
