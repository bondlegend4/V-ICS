import time
import threading
from collections import deque
import logging

import config as config

logger = logging.getLogger(__name__)

class StateManager:
    """Thread-safe class to hold and manage the overall system state."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = {
            "connections": {
                "openplc": {"connected": False, "last_ok": 0.0, "error": ""},
                "memcached": {"connected": False, "last_ok": 0.0, "error": ""},
                "scadalts": {"connected": False, "last_ok": 0.0, "error": ""}, # Placeholder
                "mqtt": {"connected": False, "last_ok": 0.0, "error": ""},      # Placeholder
                "godot": {"connected": False, "last_ok": 0.0},
            },
            "plc_data": {
                "coils": {}, # {addr: bool}
                "input_registers": {}, # {addr: int}
                # Add holding_registers if needed
            },
            "simulation_data": {}, # {tag_name: value} - From Memcached
            "system_errors": [], # List of recent critical errors
            "test_results": {}, # Stores results from testing.py {scenario_id: result_dict}
            "history": {} # {tag_name: deque([(timestamp, value), ...])}
        }

    def update_connection_status(self, component: str, connected: bool, last_ok: float, error: str = ""):
        """Update the connection status for a component."""
        with self._lock:
            if component in self._state["connections"]:
                self._state["connections"][component]["connected"] = connected
                self._state["connections"][component]["last_ok"] = last_ok
                self._state["connections"][component]["error"] = error
            else:
                logger.warning(f"Attempted to update status for unknown component: {component}")

    def update_plc_coils(self, coils: dict[int, bool]):
        """Update PLC coil values."""
        with self._lock:
            self._state["plc_data"]["coils"].update(coils)

    def update_plc_input_registers(self, registers: dict[int, int]):
        """Update PLC input register values."""
        with self._lock:
            self._state["plc_data"]["input_registers"].update(registers)
            # Update history
            now = time.time()
            for addr, value in registers.items():
                self._add_history_point(f"PLC_IW_{addr}", now, value)


    def update_simulation_data(self, sim_data: dict[str, any]):
        """Update simulation state values from Memcached."""
        with self._lock:
            self._state["simulation_data"].update(sim_data)
             # Update history
            now = time.time()
            for tag, value in sim_data.items():
                 # Only add if it's likely a numerical sensor value
                 if isinstance(value, (int, float)):
                    self._add_history_point(tag, now, value)

    def update_godot_status(self, last_ok: float):
        """Record a ping from Godot."""
        with self._lock:
            self._state["connections"]["godot"]["connected"] = True
            self._state["connections"]["godot"]["last_ok"] = last_ok
            # Check if connection timed out implicitly
            if time.time() - last_ok > config.CONNECTION_TIMEOUT * 2: # Use a longer timeout for Godot pings
                 self._state["connections"]["godot"]["connected"] = False


    def add_system_error(self, error_msg: str):
        """Add a critical system error message."""
        with self._lock:
            self._state["system_errors"].append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}")
            # Optional: Limit the size of the error list
            if len(self._state["system_errors"]) > 50:
                self._state["system_errors"].pop(0)

    def update_test_result(self, scenario_id: int, result: dict):
        """Update the result for a specific test scenario."""
        with self._lock:
             self._state["test_results"][scenario_id] = result

    def _add_history_point(self, tag: str, timestamp: float, value: any):
        """Internal method to add a point to the history deque."""
        if tag not in self._state["history"]:
            self._state["history"][tag] = deque(maxlen=config.MAX_HISTORY_POINTS)
        self._state["history"][tag].append((timestamp, value))

    def get_full_state(self) -> dict:
        """Return a copy of the current state."""
        with self._lock:
            # Return a deep copy if nested dicts/lists might be modified by caller
            # For read-only purposes, a shallow copy might suffice
            # Using dict comprehension for a shallow copy here:
            state_copy = {k: v.copy() if isinstance(v, dict) else v[:] if isinstance(v, list) else v for k, v in self._state.items()}
            # Special handling for nested dicts
            state_copy["connections"] = {k: v.copy() for k, v in self._state["connections"].items()}
            state_copy["plc_data"] = {k: v.copy() for k, v in self._state["plc_data"].items()}
            # History needs careful copying if deques are involved
            state_copy["history"] = {k: list(v) for k, v in self._state["history"].items()} # Convert deque to list for JSON serialization
            return state_copy

    def get_component_status(self) -> dict:
         """Return just the connection statuses."""
         with self._lock:
             return {k: v.copy() for k, v in self._state["connections"].items()}

    def get_latest_values(self) -> dict:
        """Return latest PLC and Simulation values."""
        with self._lock:
            return {
                "plc": {k: v.copy() for k, v in self._state["plc_data"].items()},
                "simulation": self._state["simulation_data"].copy()
            }

    def get_test_results(self) -> dict:
         """Return test results."""
         with self._lock:
             return self._state["test_results"].copy()

    def get_history(self, tag: str) -> list:
        """Return history for a specific tag as a list of tuples."""
        with self._lock:
            return list(self._state["history"].get(tag, []))