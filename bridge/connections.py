import memcache
import time
import logging
import requests # For Scada-LTS API (optional)
# import paho.mqtt.client as mqtt # For MQTT (optional)

from typing import Union, Any, Dict # Make sure Union and Any are imported here

from modbus_io import ModbusIO
import config as config

logger = logging.getLogger(__name__)

class ConnectionsManager:
    """Manages connections to external systems (PLC, Memcached, etc.)."""

    def __init__(self):
        self._modbus_client = ModbusIO(
            host=config.MODBUS_HOST,
            port=config.MODBUS_PORT,
            timeout=config.MODBUS_TIMEOUT
        )
        self._memcached_client = None
        self._memcached_connected = False
        self._memcached_last_ok_time = 0.0
        self.connect_memcached() # Initial connection attempt

        # --- Optional Connections ---
        self._scada_client = None # Placeholder for ScadaLTS API client
        self._scada_connected = False
        self._scada_last_ok_time = 0.0

        self._mqtt_client = None # Placeholder for Paho MQTT client
        self._mqtt_connected = False
        self._mqtt_last_ok_time = 0.0
        # self.connect_mqtt() # Add MQTT connection logic if needed

    # --- Modbus (OpenPLC) Methods ---
    def get_modbus_client(self) -> ModbusIO:
        return self._modbus_client

    def is_modbus_connected(self) -> bool:
        # Check connection status and if the last communication was recent
        if not self._modbus_client.is_connected():
            return False
        return (time.time() - self._modbus_client.get_last_ok_time()) < config.CONNECTION_TIMEOUT

    def read_plc_coils(self, start_addr: int, count: int) -> list[bool] | None:
        return self._modbus_client.read_coils(start_addr, count)

    def read_plc_input_registers(self, start_addr: int, count: int) -> list[int] | None:
        return self._modbus_client.read_input_registers(start_addr, count)

    def write_plc_registers(self, start_addr: int, values: list[int]) -> bool:
        # Typically writes to Holding Registers, mapped via ModbusIO's IR_plc logic if needed
        return self._modbus_client.write_multiple_registers(start_addr, values)

    # --- Memcached (Simulation Connector) Methods ---
    def connect_memcached(self):
        try:
            logger.info(f"Attempting Memcached connection to {config.CONNECTOR_PATH}")
            # Ensure path is treated as server list if needed, e.g., ['host:port']
            servers = [config.CONNECTOR_PATH] if ':' in config.CONNECTOR_PATH else config.CONNECTOR_PATH
            self._memcached_client = memcache.Client(servers, debug=0)
            # Test connection with a simple operation
            stats = self._memcached_client.get_stats()
            if stats: # If we get stats back, assume connection is ok
                self._memcached_connected = True
                self._memcached_last_ok_time = time.time()
                logger.info("Memcached connection successful.")
            else:
                 self._memcached_connected = False
                 logger.warning("Memcached connection established but get_stats failed.")

        except Exception as e:
            self._memcached_connected = False
            logger.error(f"Failed to connect to Memcached at {config.CONNECTOR_PATH}: {e}")

    def is_memcached_connected(self) -> bool:
        if not self._memcached_connected:
            return False
        # Add a check for recent activity if needed, or just rely on connection flag
        return (time.time() - self._memcached_last_ok_time) < config.CONNECTION_TIMEOUT

    def get_sim_state(self, key: str) -> Union[Any, None]: # This line should no longer cause a NameError
        """Gets a value from Memcached."""
        if not self._memcached_connected or self._memcached_client is None:
            self.connect_memcached() # Attempt reconnect
            if not self._memcached_connected:
                return None
        try:
            full_key = f"{config.CONNECTOR_NAME}_{key}" # Optional namespacing
            value = self._memcached_client.get(full_key)
            if value is not None:
                self._memcached_last_ok_time = time.time()
            # Consider logging if key not found vs. actual error
            # else: logger.debug(f"Key '{full_key}' not found in Memcached.")
            return value
        except Exception as e:
            logger.error(f"Error getting key '{key}' from Memcached: {e}")
            self._memcached_connected = False # Assume connection lost on error
            return None

    def get_sim_state(self, key: str) -> Union[Any, None]:
        """Retrieve a specific key from the simulation state cache."""
        if not self._memcached_connected or self._memcached_client is None:
            self.connect_memcached() # Attempt reconnect
            if not self._memcached_connected:
                return False
        try:
            full_key = f"{config.CONNECTOR_NAME}_{key}" # Optional namespacing
            success = self._memcached_client.set(full_key, value)
            if success:
                self._memcached_last_ok_time = time.time()
                return True
            else:
                # set() in python-memcached often returns True even if server is down later,
                # so success check isn't fully reliable for connection status.
                 logger.warning(f"Memcached set command for key '{key}' returned non-True (unusual).")
                 return False # Or return True and rely on next get/stats failing
        except Exception as e:
            logger.error(f"Error setting key '{key}' in Memcached: {e}")
            self._memcached_connected = False # Assume connection lost on error
            return False

    # --- Scada-LTS Methods (Placeholder) ---
    def connect_scada(self):
        # TODO: Implement Scada-LTS API connection logic (e.g., using requests)
        logger.warning("Scada-LTS connection logic not implemented.")
        self._scada_connected = False # Default to not connected

    def is_scada_connected(self) -> bool:
         # TODO: Implement actual check
        return self._scada_connected and (time.time() - self._scada_last_ok_time) < config.CONNECTION_TIMEOUT

    def get_scada_status(self) -> dict:
         # TODO: Implement API call to get Scada-LTS status
        logger.warning("Scada-LTS get_status not implemented.")
        return {"status": "unknown"}

    # --- MQTT Methods (Placeholder) ---
    def connect_mqtt(self):
         # TODO: Implement MQTT connection logic using paho-mqtt
        logger.warning("MQTT connection logic not implemented.")
        self._mqtt_connected = False

    def is_mqtt_connected(self) -> bool:
         # TODO: Implement actual check
        return self._mqtt_connected and (time.time() - self._mqtt_last_ok_time) < config.CONNECTION_TIMEOUT

    def get_mqtt_status(self) -> dict:
        return {"connected": self.is_mqtt_connected()}

    def close_all(self):
        """Cleanly close all managed connections."""
        logger.info("Closing all connections...")
        self._modbus_client.close()
        if self._memcached_client:
            try:
                self._memcached_client.disconnect_all()
            except Exception as e:
                logger.error(f"Error disconnecting from Memcached: {e}")
        # TODO: Add close logic for ScadaLTS API client and MQTT client
        logger.info("Connections closed.")