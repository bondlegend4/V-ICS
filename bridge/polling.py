import time
import threading
import logging

import config as config
from connections import ConnectionsManager
from state_manager import StateManager

logger = logging.getLogger(__name__)

def polling_loop(connections: ConnectionsManager, state: StateManager, stop_event: threading.Event):
    """Background thread function to poll data sources."""
    logger.info("Polling thread started.")
    while not stop_event.is_set():
        try:
            start_time = time.time()

            # --- Poll OpenPLC ---
            plc_connected = connections.is_modbus_connected()
            plc_error = ""
            plc_coils = None
            plc_inputs = None
            if plc_connected:
                # Read Coils
                coils = connections.read_plc_coils(config.PLC_ADDR_PUMP_CONTROL, config.PLC_COIL_COUNT)
                if coils is not None:
                    plc_coils = {i + config.PLC_ADDR_PUMP_CONTROL: coils[i] for i in range(len(coils))}
                else:
                    plc_error = "Failed to read PLC coils"
                    plc_connected = False # Assume connection lost if read fails

                # Read Input Registers (only if coils read was ok)
                if plc_connected:
                    inputs = connections.read_plc_input_registers(config.PLC_ADDR_SOIL_MOISTURE, config.PLC_INPUT_REGISTER_COUNT)
                    if inputs is not None:
                        plc_inputs = {i + config.PLC_ADDR_SOIL_MOISTURE: inputs[i] for i in range(len(inputs))}
                    else:
                        plc_error = "Failed to read PLC input registers"
                        plc_connected = False # Assume connection lost

            state.update_connection_status("openplc", plc_connected, connections.get_modbus_client().get_last_ok_time(), plc_error)
            if plc_coils is not None: state.update_plc_coils(plc_coils)
            if plc_inputs is not None: state.update_plc_input_registers(plc_inputs)

            # --- Poll Memcached (Simulation State) ---
            memcached_connected = connections.is_memcached_connected()
            memcached_error = ""
            sim_data = {}
            if memcached_connected:
                all_tags_found = True
                # Read all expected sensor/actuator tags from config
                tags_to_read = list(config.SIM_SENSORS_TO_PLC_MAP.keys()) + list(config.PLC_ACTUATORS_TO_SIM_MAP.values())
                for tag in tags_to_read:
                    value = connections.get_sim_state(tag)
                    if value is not None:
                        sim_data[tag] = value
                    else:
                        # Could be transient (sim hasn't written yet) or connection issue
                        memcached_error = f"Failed to read tag '{tag}' from Memcached"
                        # Don't immediately set disconnected unless multiple failures or prolonged absence
                        all_tags_found = False
                        # break # Option: stop reading if one fails

                if not sim_data: # If we couldn't read anything
                     memcached_connected = False
                     if not memcached_error: memcached_error="Failed to read any data from Memcached"

            state.update_connection_status("memcached", memcached_connected, connections._memcached_last_ok_time, memcached_error)
            if sim_data: state.update_simulation_data(sim_data)

            # --- Poll Scada-LTS (Optional Placeholder) ---
            # scada_connected = connections.is_scada_connected()
            # scada_status = connections.get_scada_status() if scada_connected else {"status": "disconnected"}
            # state.update_connection_status("scadalts", scada_connected, connections._scada_last_ok_time, scada_status.get("error", ""))
            # logger.debug(f"Scada Status: {scada_status}")


            # --- Poll MQTT (Optional Placeholder) ---
            # mqtt_connected = connections.is_mqtt_connected()
            # mqtt_status = connections.get_mqtt_status()
            # state.update_connection_status("mqtt", mqtt_connected, connections._mqtt_last_ok_time, mqtt_status.get("error", ""))
            # logger.debug(f"MQTT Status: {mqtt_status}")


            # --- Check Godot Timeout ---
            # (Handled directly in state_manager when ping is received)


            # --- Delay ---
            elapsed = time.time() - start_time
            sleep_time = max(0, config.POLL_INTERVAL - elapsed)
            if sleep_time > 0:
                stop_event.wait(sleep_time) # Use wait instead of sleep to be responsive to stop_event

        except Exception as e:
            logger.exception("Unhandled exception in polling loop:")
            state.add_system_error(f"Polling loop crash: {e}")
            stop_event.wait(config.POLL_INTERVAL) # Wait before retrying

    logger.info("Polling thread finished.")