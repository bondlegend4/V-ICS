import os

# --- General Settings ---
# How often background threads poll/sync data (in seconds)
POLL_INTERVAL = float(os.getenv('POLL_INTERVAL', '2.0'))
SYNC_INTERVAL = float(os.getenv('SYNC_INTERVAL', '1.0'))
# How long before considering a component disconnected (in seconds)
CONNECTION_TIMEOUT = float(os.getenv('CONNECTION_TIMEOUT', '10.0'))

# --- Modbus (OpenPLC) Connection ---
MODBUS_HOST = os.getenv('MODBUS_HOST', 'openplc')
MODBUS_PORT = int(os.getenv('MODBUS_PORT', '502'))
MODBUS_TIMEOUT = float(os.getenv('MODBUS_TIMEOUT', '1.0')) # Connection/read timeout

# --- Simulation Connector (Memcached) ---
CONNECTOR_TYPE = os.getenv('CONNECTOR_TYPE', 'memcache')
CONNECTOR_PATH = os.getenv('CONNECTOR_PATH', 'memcached:11211') # Memcached service name:port
CONNECTOR_NAME = os.getenv('CONNECTOR_NAME', 'sim_state') # Namespace/prefix (optional)

# --- PLC Address Mapping (Example - **ADJUST THESE**) ---
PLC_ADDR_SOIL_MOISTURE = 0 # %IW0.0
PLC_ADDR_TEMPERATURE = 1   # %IW0.1
PLC_ADDR_HUMIDITY = 2      # %IW0.2
PLC_ADDR_WATER_FLOW = 3    # %IW0.3
PLC_ADDR_PRESSURE = 4      # %IW0.4

PLC_ADDR_PUMP_CONTROL = 0  # %QX0.0
PLC_ADDR_VALVE_CONTROL = 1 # %QX0.1

PLC_INPUT_REGISTER_COUNT = 5
PLC_COIL_COUNT = 2

# --- Simulation Tag Mapping (Example - **ADJUST THESE**) ---
TAG_SIM_SOIL_MOISTURE = 'sim_SoilMoisture'
TAG_SIM_TEMPERATURE = 'sim_Temperature'
TAG_SIM_HUMIDITY = 'sim_Humidity'
TAG_SIM_WATER_FLOW = 'sim_WaterFlow'
TAG_SIM_PRESSURE = 'sim_Pressure'

TAG_SIM_PUMP_CONTROL = 'sim_PumpControl'   # Actuator state read by Sim
TAG_SIM_VALVE_CONTROL = 'sim_ValveControl' # Actuator state read by Sim

# List of sensor tags the bridge reads from Memcached and writes to PLC
SIM_SENSORS_TO_PLC_MAP = {
    TAG_SIM_SOIL_MOISTURE: PLC_ADDR_SOIL_MOISTURE,
    TAG_SIM_TEMPERATURE:   PLC_ADDR_TEMPERATURE,
    TAG_SIM_HUMIDITY:      PLC_ADDR_HUMIDITY,
    TAG_SIM_WATER_FLOW:    PLC_ADDR_WATER_FLOW,
    TAG_SIM_PRESSURE:      PLC_ADDR_PRESSURE,
}

# List of actuator tags the bridge reads from PLC and writes to Memcached
PLC_ACTUATORS_TO_SIM_MAP = {
    PLC_ADDR_PUMP_CONTROL:  TAG_SIM_PUMP_CONTROL,
    PLC_ADDR_VALVE_CONTROL: TAG_SIM_VALVE_CONTROL,
}

# --- History Settings ---
MAX_HISTORY_POINTS = int(os.getenv('MAX_HISTORY_POINTS', '100'))

# --- Flask Settings ---
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5001') )
FLASK_DEBUG = os.getenv('FLASK_ENV', 'development').lower() == 'development'