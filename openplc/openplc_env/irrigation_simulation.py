from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
import random
import time
from threading import Thread

# Helper function to generate random sensor values
def simulate_sensors(context):
    slave_id = 0x00
    while True:
        # Simulate Soil Moisture (register 0)
        soil_moisture = random.randint(300, 800)  # Simulate analog value between 300 and 800
        context[slave_id].setValues(3, 0, [soil_moisture])
        
        # Simulate Temperature (register 1)
        temperature = random.randint(20, 40)  # Simulate analog temperature in Celsius
        context[slave_id].setValues(3, 1, [temperature])
        
        # Simulate Humidity (register 2)
        humidity = random.randint(50, 90)  # Simulate humidity percentage
        context[slave_id].setValues(3, 2, [humidity])

        # Simulate Water Flow (register 3)
        water_flow = random.randint(500, 1000)  # Flow rate in liters per hour
        context[slave_id].setValues(3, 3, [water_flow])

        # Simulate Pressure (register 4)
        pressure = random.randint(50, 150)  # Pressure in psi
        context[slave_id].setValues(3, 4, [pressure])

        time.sleep(1)  # Update every second

# Initialize Modbus Server
def run_modbus_server():
    # Create a datastore with some predefined registers
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),
        co=ModbusSequentialDataBlock(0, [0]*100),
        hr=ModbusSequentialDataBlock(0, [0]*100),
        ir=ModbusSequentialDataBlock(0, [0]*100)
    )
    context = ModbusServerContext(slaves=store, single=True)
    
    # Start the sensor simulation in a separate thread
    thread = Thread(target=simulate_sensors, args=(context,))
    thread.start()

    # Modbus Server Identification
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'IrrigationSystem'
    identity.ProductCode = 'IR001'
    identity.VendorUrl = 'http://example.com'
    identity.ProductName = 'Irrigation System Simulation'
    identity.ModelName = 'Modbus Server'
    identity.MajorMinorRevision = '1.0'

    # Start the Modbus server on localhost and port 5020
    StartTcpServer(context, identity=identity, address=("localhost", 5020))

if __name__ == "__main__":
    run_modbus_server()
