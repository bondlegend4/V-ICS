# bridge/app.py

import threading
import time
import logging
import signal
import sys
import os # Import os to read FLASK_ENV if needed

from flask import Flask
from flask_cors import CORS

# Imports from other modules within the bridge package
# These imports should work because app.py is at the root level (/app)
import config
from connections import ConnectionsManager
from state_manager import StateManager
from polling import polling_loop
from synchronization import synchronization_loop
from testing import TestRunner
from routes.web import web_bp # Import blueprint from routes subdir
from routes.api import api_bp # Import blueprint from routes subdir

# --- Logging Setup ---
# Determine log level based on environment variable
log_level = logging.DEBUG if os.getenv('FLASK_ENV', 'production').lower() == 'development' else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
        # logging.FileHandler("bridge.log") # Optional
    ])
# Suppress overly verbose logs from libraries if needed
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("memcache").setLevel(logging.INFO)
logging.getLogger("pyModbusTCP").setLevel(logging.INFO)

logger = logging.getLogger(__name__) # Get logger for this module

# --- Global Variables for Threads & Shutdown ---
stop_event = threading.Event()
polling_thread = None
sync_thread = None
connections_manager = None
state_manager = None
test_runner = None

# --- Signal Handling for Graceful Shutdown ---
def signal_handler(sig, frame):
    logger.warning(f"Received signal {sig}. Initiating shutdown...")
    stop_event.set()
    # Give threads time to finish current loop
    time.sleep(max(config.POLL_INTERVAL, config.SYNC_INTERVAL) + 0.5)
    if connections_manager:
        connections_manager.close_all()
    logger.info("Shutdown complete.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler) # Handle Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # Handle docker stop

# --- Flask Application Factory ---
def create_app():
    # Use global variables for components to ensure they are shared
    global connections_manager, state_manager, test_runner, polling_thread, sync_thread

    flask_app_instance = Flask(__name__, template_folder='templates', static_folder='static')
    # Load config if needed by extensions, though we primarily use config.py directly
    # flask_app_instance.config.from_object(config)
    CORS(flask_app_instance) # Enable CORS

    logger.info("Initializing Bridge components...")
    # --- Initialize Shared Components ---
    # Ensure these are initialized only once if create_app can be called multiple times
    if state_manager is None:
        state_manager = StateManager()
    if connections_manager is None:
        connections_manager = ConnectionsManager()
    if test_runner is None:
        test_runner = TestRunner(connections_manager, state_manager)

    # --- Store shared components in app context ---
    # Makes them accessible in routes via current_app
    flask_app_instance.state_manager = state_manager
    flask_app_instance.connections_manager = connections_manager
    flask_app_instance.test_runner = test_runner

    # --- Register Blueprints ---
    flask_app_instance.register_blueprint(web_bp)
    flask_app_instance.register_blueprint(api_bp)
    logger.info("Registered Flask blueprints.")

    # --- Start Background Threads ---
    # Ensure threads are started only once
    if polling_thread is None or not polling_thread.is_alive():
        logger.info("Starting background threads...")
        polling_thread = threading.Thread(target=polling_loop, args=(connections_manager, state_manager, stop_event), daemon=True, name="PollingThread")
        sync_thread = threading.Thread(target=synchronization_loop, args=(connections_manager, state_manager, stop_event), daemon=True, name="SyncThread")
        polling_thread.start()
        sync_thread.start()
        logger.info("Background threads started.")
    else:
         logger.info("Background threads already running.")


    return flask_app_instance

# --- Create the app object by calling the factory ---
# This 'app' variable is what waitress will target (app:app)
app = create_app()

# --- Main Execution Block (Only for direct execution / Flask development server) ---
if __name__ == '__main__':
    # This block is NOT run when using Waitress in the container CMD
    is_debug = os.getenv('FLASK_ENV', 'production').lower() == 'development'
    logger.info(f"Starting Flask DEVELOPMENT server on {config.FLASK_HOST}:{config.FLASK_PORT} (Debug: {is_debug})")
    # Use the 'app' object created above
    # use_reloader=False is important to prevent background threads starting twice
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=is_debug, use_reloader=False)

    # --- Cleanup (if Flask dev server stops gracefully) ---
    # This part might not be reached if using Ctrl+C due to signal handler exiting
    logger.info("Flask development server stopped. Cleaning up...")
    stop_event.set()
    if polling_thread: polling_thread.join(timeout=5)
    if sync_thread: sync_thread.join(timeout=5)
    if connections_manager: connections_manager.close_all()
    logger.info("Bridge application finished.")