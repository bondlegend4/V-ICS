import time
import threading
import logging

import config as config
from connections import ConnectionsManager
from state_manager import StateManager

logger = logging.getLogger(__name__)

def synchronization_loop(connections: ConnectionsManager, state: StateManager, stop_event: threading.Event):
    """Background thread function to synchronize data between PLC and Simulation."""
    logger.info("Synchronization thread started.")
    while not stop_event.is_set():
        try:
            start_time = time.time()
            full_state = state.get_full_state() # Get a consistent snapshot

            # --- Sync 1: PLC Actuators -> Simulation Connector ---
            if full_state["connections"]["openplc"]["connected"] and full_state["connections"]["memcached"]["connected"]:
                plc_coils = full_state["plc_data"]["coils"]
                success_count = 0
                for plc_addr, sim_tag in config.PLC_ACTUATORS_TO_SIM_MAP.items():
                    if plc_addr in plc_coils:
                        plc_value = plc_coils[plc_addr]
                        # Optional: Only write if value changed? Might add complexity.
                        if connections.set_sim_state(sim_tag, plc_value):
                            success_count += 1
                        else:
                            logger.warning(f"Sync: Failed to write PLC coil {plc_addr} state to sim tag {sim_tag}")
                            # Don't break, try to sync others
                # logger.debug(f"Sync: Wrote {success_count}/{len(config.PLC_ACTUATORS_TO_SIM_MAP)} PLC actuators to sim.")
            else:
                logger.debug("Sync: Skipping PLC -> Sim sync (PLC or Memcached disconnected).")


            # --- Sync 2: Simulation Sensors -> PLC Registers ---
            if full_state["connections"]["memcached"]["connected"] and full_state["connections"]["openplc"]["connected"]:
                sim_data = full_state["simulation_data"]
                registers_to_write = {} # {addr: value}
                all_sensors_found = True
                for sim_tag, plc_addr in config.SIM_SENSORS_TO_PLC_MAP.items():
                    if sim_tag in sim_data:
                        # Ensure value is integer for PLC register
                        try:
                            # TODO: Apply any necessary scaling/conversion here
                            register_value = int(sim_data[sim_tag])
                            registers_to_write[plc_addr] = register_value
                        except (ValueError, TypeError) as e:
                             logger.warning(f"Sync: Could not convert sim tag '{sim_tag}' value '{sim_data[sim_tag]}' to int for PLC: {e}")
                             all_sensors_found = False # Treat conversion error as missing data for this cycle
                    else:
                        logger.debug(f"Sync: Sim sensor tag '{sim_tag}' not found in current state.")
                        all_sensors_found = False
                        # Don't write incomplete data? Or write default? Decide strategy.
                        # For now, we proceed but might only write available ones depending on ModbusIO behavior.

                if registers_to_write and all_sensors_found: # Only write if all expected sensors were present
                    # Prepare list in correct order for write_multiple_registers
                    ordered_values = [0] * config.PLC_INPUT_REGISTER_COUNT # Initialize with zeros or last known?
                    for addr, value in registers_to_write.items():
                         index = addr - config.PLC_ADDR_SOIL_MOISTURE # Calculate index based on starting address
                         if 0 <= index < config.PLC_INPUT_REGISTER_COUNT:
                              ordered_values[index] = value
                         else:
                              logger.warning(f"Sync: Calculated invalid index {index} for PLC address {addr}")

                    if not connections.write_plc_registers(config.PLC_ADDR_SOIL_MOISTURE, ordered_values):
                         logger.warning("Sync: Failed to write simulation sensors to PLC input registers.")
                elif not registers_to_write:
                     logger.debug("Sync: No simulation sensor data available to write to PLC.")
                else: # registers_to_write exists but not all_sensors_found
                    logger.debug("Sync: Skipping write to PLC - not all simulation sensors found.")

            else:
                logger.debug("Sync: Skipping Sim -> PLC sync (Memcached or PLC disconnected).")


            # --- Delay ---
            elapsed = time.time() - start_time
            sleep_time = max(0, config.SYNC_INTERVAL - elapsed)
            if sleep_time > 0:
                stop_event.wait(sleep_time) # Use wait for responsiveness

        except Exception as e:
            logger.exception("Unhandled exception in synchronization loop:")
            state.add_system_error(f"Sync loop crash: {e}")
            stop_event.wait(config.SYNC_INTERVAL) # Wait before retrying

    logger.info("Synchronization thread finished.")