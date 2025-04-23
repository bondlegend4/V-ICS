from flask import Blueprint, render_template, current_app

# Import your custom config module
# Assuming your project structure allows this import based on how app.py is run
import config # Import your custom config module

# Use current_app to access shared objects like state_manager
# Alternatively, pass them during blueprint registration in app.py

web_bp = Blueprint('web', __name__, template_folder='../templates', static_folder='../static')

@web_bp.route('/')
@web_bp.route('/status')
def status_page():
    """Renders the main status dashboard."""
    state_manager = current_app.state_manager # Access from app context
    # Pass necessary data AND the config module to the template
    return render_template('status.html',
                           title="System Status",
                           config=config) # Pass the imported config module

@web_bp.route('/details')
def details_page():
    """Renders the detailed values page."""
    state_manager = current_app.state_manager
    # Pass config here too if details.html needs it
    return render_template('details.html',
                           title="Detailed Values",
                           config=config)

@web_bp.route('/tests')
def tests_page():
    """Renders the test runner page."""
    state_manager = current_app.state_manager
    # Pass scenario definitions and current results
    # If testing.py is inside bridge/, use 'from testing import ...'
    from testing import TEST_SCENARIOS # Import here or pass from app
    test_results = state_manager.get_test_results()
    return render_template('tests.html',
                           title="System Tests",
                           scenarios=TEST_SCENARIOS,
                           results=test_results,
                           config=config) # Pass config here too if tests.html needs it

@web_bp.route('/history')
def history_page():
    """Renders the history/graphing page."""
    # Data for graphs will likely be fetched via JS calling an API endpoint
    # Pass config here too if history.html needs it
    return render_template('history.html',
                           title="Variable History",
                           config=config)