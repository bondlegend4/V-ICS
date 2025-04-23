from flask import Blueprint, jsonify, request, current_app
import time

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- Status & Data Endpoints ---

@api_bp.route('/system-state', methods=['GET'])
def get_system_state():
    """Returns the current aggregated state of the system."""
    state_manager = current_app.state_manager
    # Add timestamp to the state
    state = state_manager.get_full_state()
    state["timestamp"] = time.time()
    return jsonify(state)

@api_bp.route('/connection-status', methods=['GET'])
def get_connection_status():
    """Returns just the connection status of components."""
    state_manager = current_app.state_manager
    return jsonify(state_manager.get_component_status())

@api_bp.route('/latest-values', methods=['GET'])
def get_latest_values():
    """Returns latest PLC and Simulation values."""
    state_manager = current_app.state_manager
    return jsonify(state_manager.get_latest_values())

# --- Godot Interaction Endpoints ---

@api_bp.route('/ping', methods=['GET', 'POST']) # Allow POST just in case
def godot_ping():
    """Endpoint for Godot to signal it's alive."""
    state_manager = current_app.state_manager
    now = time.time()
    state_manager.update_godot_status(now)
    return jsonify({"ok": True, "message": "Pong!", "timestamp": now})

# Keep health-check similar to original for compatibility if needed
@api_bp.route('/health-check', methods=['GET'])
def godot_health_check():
    """Endpoint for Godot to check bridge/PLC status."""
    state_manager = current_app.state_manager
    connections_manager = current_app.connections_manager
    now = time.time()
    state_manager.update_godot_status(now) # Also update status on health check

    state = state_manager.get_full_state() # Get current snapshot

    def get_color(component_status):
        if not component_status["connected"]: return "red"
        if (now - component_status["last_ok"]) < config.CONNECTION_TIMEOUT: return "green"
        return "yellow" # Stale

    # Simplify the response compared to full state if desired
    return jsonify({
        "openplc_status": get_color(state["connections"]["openplc"]),
        "openplc_error": state["connections"]["openplc"]["error"],
        "openplc_values": state["plc_data"].get("input_registers", {}), # Or combine all plc_data
        "pump_control": state["plc_data"].get("coils", {}).get(config.PLC_ADDR_PUMP_CONTROL),
        "valve_control": state["plc_data"].get("coils", {}).get(config.PLC_ADDR_VALVE_CONTROL),
        "simulation_status": get_color(state["connections"]["memcached"]),
        "simulation_error": state["connections"]["memcached"]["error"],
        "simulation_values": state["simulation_data"],
        "godot_status": get_color(state["connections"]["godot"]),
        "timestamp": now
    })

# --- Testing Endpoints ---

@api_bp.route('/test-scenarios', methods=['GET'])
def get_test_scenarios():
    """Returns the definitions of available test scenarios."""
    from testing import TEST_SCENARIOS
    return jsonify(TEST_SCENARIOS)

@api_bp.route('/test-results', methods=['GET'])
def get_test_results():
    """Returns the current results of all test scenarios."""
    state_manager = current_app.state_manager
    return jsonify(state_manager.get_test_results())


@api_bp.route('/test-scenario/<int:scenario_id>/run', methods=['POST'])
def run_test_scenario_api(scenario_id):
    """Triggers a specific test scenario to run."""
    test_runner = current_app.test_runner
    result = test_runner.run_scenario(scenario_id)
    if "error" in result:
        return jsonify(result), 400 if result["error"] == "Invalid scenario ID" else 500
    return jsonify(result)

@api_bp.route('/test-scenario/<int:scenario_id>/visual-check', methods=['POST'])
def record_visual_check_api(scenario_id):
    """Records the result of a manual visual check for a scenario."""
    test_runner = current_app.test_runner
    data = request.get_json()
    if not data or 'passed' not in data or not isinstance(data['passed'], bool):
        return jsonify({"error": "Missing or invalid 'passed' boolean in request body"}), 400

    result = test_runner.record_visual_check(scenario_id, data['passed'])
    if "error" in result:
         return jsonify(result), 400 # Or appropriate error code
    return jsonify(result)


# --- History Endpoint ---

@api_bp.route('/history/<tag_name>', methods=['GET'])
def get_tag_history(tag_name):
    """Returns historical data points for a specific tag."""
    state_manager = current_app.state_manager
    history = state_manager.get_history(tag_name)
    # Format might need adjustment depending on charting library
    return jsonify({tag_name: history})