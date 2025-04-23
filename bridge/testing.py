import time
import logging

import config as config
from connections import ConnectionsManager
from state_manager import StateManager

logger = logging.getLogger(__name__)

# Define test scenarios (Adapted from your original py)
# ** ADJUST VALUES AND EXPECTATIONS AS NEEDED **
TEST_SCENARIOS = {
    1: {
        "name": "Low moisture, high temp => Expect Pump ON, Valve ON",
        "sim_inputs": { # Write these values to Memcached (simulating sensor changes)
            config.TAG_SIM_SOIL_MOISTURE: 300,
            config.TAG_SIM_TEMPERATURE: 40,
            config.TAG_SIM_HUMIDITY: 40,
            config.TAG_SIM_WATER_FLOW: 500,
            config.TAG_SIM_PRESSURE: 90
        },
         "plc_inputs": [300, 40, 40, 500, 90], # Corresponding values written to PLC %IW
        "expected_pump": True,  # Expected state of PLC coil %QX0.0 after sync + PLC logic run
        "expected_valve": True  # Expected state of PLC coil %QX0.1
    },
    2: {
        "name": "High moisture, normal temp => Expect Pump OFF, Valve OFF",
        "sim_inputs": {
            config.TAG_SIM_SOIL_MOISTURE: 700,
            config.TAG_SIM_TEMPERATURE: 25,
            config.TAG_SIM_HUMIDITY: 60,
            config.TAG_SIM_WATER_FLOW: 300,
            config.TAG_SIM_PRESSURE: 80
        },
        "plc_inputs": [700, 25, 60, 300, 80],
        "expected_pump": False,
        "expected_valve": False
    }
    # Add more scenarios...
}

class TestRunner:
    def __init__(self, connections: ConnectionsManager, state: StateManager):
        self.connections = connections
        self.state = state
        # Initialize test results in state manager
        initial_results = {
            sid: {"name": data["name"], "status": "Not Started", "coil_pass": None, "visual_pass": None, "error": None}
            for sid, data in TEST_SCENARIOS.items()
        }
        for sid, result in initial_results.items():
            self.state.update_test_result(sid, result)


    def run_scenario(self, scenario_id: int) -> dict:
        """Runs a specific test scenario."""
        if scenario_id not in TEST_SCENARIOS:
            return {"error": "Invalid scenario ID"}

        scenario = TEST_SCENARIOS[scenario_id]
        result = {
            "name": scenario["name"],
            "status": "Running",
            "coil_pass": None,
            "visual_pass": None, # Visual pass remains until user input
            "error": None,
            "details": {}
        }
        self.state.update_test_result(scenario_id, result) # Update status immediately

        logger.info(f"Starting test scenario {scenario_id}: {scenario['name']}")

        try:
            # --- Pre-conditions Check ---
            if not self.connections.is_modbus_connected():
                raise RuntimeError("OpenPLC not connected.")
            if not self.connections.is_memcached_connected():
                 # Decide if tests should write directly to PLC if sim connector is down
                 # raise RuntimeError("Simulation connector (Memcached) not connected.")
                 logger.warning(f"Test {scenario_id}: Memcached not connected, will write directly to PLC.")


            # --- Step 1: Set Simulation/PLC Inputs ---
            # Option A: Write to Memcached (preferred, lets sync loop handle PLC write)
            if self.connections.is_memcached_connected():
                write_success = True
                for tag, value in scenario["sim_inputs"].items():
                     if not self.connections.set_sim_state(tag, value):
                          write_success = False
                          logger.error(f"Test {scenario_id}: Failed to set sim tag {tag}")
                if not write_success:
                    raise RuntimeError("Failed to set simulation state in Memcached.")
                result["details"]["input_method"] = "Memcached"
                # Wait for sync loop to potentially write to PLC + PLC logic cycle
                time.sleep(config.SYNC_INTERVAL + config.POLL_INTERVAL + 0.5) # Generous wait

            # Option B: Write directly to PLC (fallback or alternative)
            else:
                if not self.connections.write_plc_registers(config.PLC_ADDR_SOIL_MOISTURE, scenario["plc_inputs"]):
                    raise RuntimeError("Failed to write inputs directly to PLC.")
                result["details"]["input_method"] = "Direct PLC Write"
                # Wait for PLC logic cycle
                time.sleep(config.POLL_INTERVAL + 0.5) # Allow time for PLC logic


            # --- Step 2: Read PLC Coil Outputs ---
            coil_data = self.connections.read_plc_coils(config.PLC_ADDR_PUMP_CONTROL, config.PLC_COIL_COUNT)
            if coil_data is None or len(coil_data) != config.PLC_COIL_COUNT:
                raise RuntimeError("Failed to read PLC coil outputs after setting inputs.")

            actual_pump = coil_data[config.PLC_ADDR_PUMP_CONTROL]
            actual_valve = coil_data[config.PLC_ADDR_VALVE_CONTROL]
            result["details"]["actual_pump"] = actual_pump
            result["details"]["actual_valve"] = actual_valve

            # --- Step 3: Check Results ---
            pump_ok = (actual_pump == scenario["expected_pump"])
            valve_ok = (actual_valve == scenario["expected_valve"])
            result["coil_pass"] = pump_ok and valve_ok

            if result["coil_pass"]:
                result["status"] = "Coil Check Passed"
                logger.info(f"Test {scenario_id}: Coil check PASSED.")
            else:
                result["status"] = "Coil Check Failed"
                result["error"] = f"Coil mismatch: Expected P={scenario['expected_pump']}, V={scenario['expected_valve']}. Got P={actual_pump}, V={actual_valve}"
                logger.warning(f"Test {scenario_id}: Coil check FAILED. {result['error']}")


        except Exception as e:
            logger.exception(f"Error running test scenario {scenario_id}:")
            result["status"] = "Error"
            result["error"] = str(e)
            result["coil_pass"] = False # Mark as fail on error

        self.state.update_test_result(scenario_id, result)
        return result # Return the final result dict

    def record_visual_check(self, scenario_id: int, passed: bool):
        """Records the result of a manual visual check."""
        if scenario_id not in TEST_SCENARIOS:
             return {"error": "Invalid scenario ID"}

        current_results = self.state.get_test_results().get(scenario_id, {})
        if not current_results or current_results.get("status") == "Not Started":
             return {"error": f"Test {scenario_id} has not been run yet."}
        if current_results.get("status") == "Error":
             return {"error": f"Test {scenario_id} ended in error, cannot record visual pass."}


        current_results["visual_pass"] = passed
        if passed:
             logger.info(f"Test {scenario_id}: Visual check recorded as PASSED.")
             # Update overall status if coil check also passed
             if current_results.get("coil_pass"):
                  current_results["status"] = "Passed"
        else:
             logger.warning(f"Test {scenario_id}: Visual check recorded as FAILED.")
             current_results["status"] = "Visual Check Failed" # Update overall status

        self.state.update_test_result(scenario_id, current_results)
        return current_results