// Base URL for API calls
const API_BASE_URL = '/api';
// How often to refresh status/details (in milliseconds)
const REFRESH_INTERVAL = 2000; // e.g., 2 seconds

let statusIntervalId = null;
let detailsIntervalId = null;
let historyChart = null;

console.log("Bridge app.js loaded");

// --- Helper Functions ---
function getStatusIndicatorClass(status) {
    if (!status || !status.connected) return 'red';
    // Use config timeout? Requires passing config to JS or hardcoding
    const timeoutThreshold = 10.0; // seconds (match config.CONNECTION_TIMEOUT)
    const now = Date.now() / 1000;
    if ((now - status.last_ok) < timeoutThreshold) return 'green';
    return 'yellow'; // Stale
}

function formatTimestamp(unixTimestamp) {
    if (!unixTimestamp) return 'N/A';
    return new Date(unixTimestamp * 1000).toLocaleTimeString();
}

// --- Status Page Logic ---
function updateStatusCard(componentId, statusData) {
    const card = document.querySelector(`.status-card[data-component="${componentId}"]`);
    if (!card) return;

    const indicator = card.querySelector('.status-indicator');
    const text = card.querySelector('.status-text');
    const errorMsg = card.querySelector('.error-message');

    const indicatorClass = getStatusIndicatorClass(statusData);
    indicator.className = `status-indicator ${indicatorClass}`; // Reset classes

    let statusText = 'Unknown';
    if (indicatorClass === 'green') statusText = 'Connected';
    else if (indicatorClass === 'yellow') statusText = 'Stale';
    else if (indicatorClass === 'red') statusText = 'Disconnected';

    text.textContent = statusText;
    errorMsg.textContent = statusData?.error || '';
    errorMsg.style.display = statusData?.error ? 'block' : 'none';
}

function updateSystemErrors(errors) {
     const errorContainer = document.getElementById('system-errors');
     if (!errorContainer) return;
     if (!errors || errors.length === 0) {
         errorContainer.innerHTML = '<p>No recent system errors.</p>';
         return;
     }
     let html = '<ul>';
     // Show latest errors first
     for (let i = errors.length - 1; i >= 0; i--) {
         html += `<li>${errors[i]}</li>`;
     }
     html += '</ul>';
     errorContainer.innerHTML = html;
}


async function fetchAndUpdateStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/system-state`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const state = await response.json();
        console.debug("Fetched system state:", state);

        // Update status cards
        if (state.connections) {
             for (const componentId in state.connections) {
                 updateStatusCard(componentId, state.connections[componentId]);
             }
        }

        // Update system errors
        updateSystemErrors(state.system_errors);


        // Update last updated timestamp
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = formatTimestamp(state.timestamp);
        }

    } catch (error) {
        console.error("Error fetching system status:", error);
        // Optionally display a general error message on the page
        const grid = document.getElementById('status-grid');
        if(grid && !grid.querySelector('.fetch-error')) {
            const errorDiv = document.createElement('p');
            errorDiv.textContent = "Error fetching status updates.";
            errorDiv.style.color = 'red';
            errorDiv.className = 'fetch-error';
            grid.prepend(errorDiv);
        }
         // Update last updated timestamp even on error
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = `Error at ${new Date().toLocaleTimeString()}`;
        }
    }
}

function initializeStatusPage() {
    console.log("Initializing Status Page...");
    if (statusIntervalId) clearInterval(statusIntervalId); // Clear previous interval if any
    fetchAndUpdateStatus(); // Initial fetch
    statusIntervalId = setInterval(fetchAndUpdateStatus, REFRESH_INTERVAL);
    console.log("Status Page initialized, interval set.");
}

// --- Details Page Logic ---
function updateTable(tableId, dataObject) {
    const tableBody = document.querySelector(`#${tableId} tbody`);
    if (!tableBody) return;
    tableBody.innerHTML = ''; // Clear existing rows
    if (!dataObject || Object.keys(dataObject).length === 0) {
        tableBody.innerHTML = '<tr><td colspan="2">No data available.</td></tr>';
        return;
    }
    for (const key in dataObject) {
        const row = tableBody.insertRow();
        const cell1 = row.insertCell();
        const cell2 = row.insertCell();
        cell1.textContent = key;
        cell1.classList.add(tableId === 'sim-state-table' ? 'tag-col' : 'addr-col'); // Add class for styling
        // Format value (e.g., floats to 2 decimal places)
        let value = dataObject[key];
        if(typeof value === 'number' && !Number.isInteger(value)) {
            value = value.toFixed(2);
        }
        cell2.textContent = value;
        cell2.classList.add('value-col');
    }
}

async function fetchAndUpdateDetails() {
     try {
        // Could use system-state or a dedicated latest-values endpoint
        const response = await fetch(`${API_BASE_URL}/latest-values`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const values = await response.json();
        console.debug("Fetched latest values:", values);

        updateTable('plc-coils-table', values.plc?.coils);
        updateTable('plc-inputs-table', values.plc?.input_registers);
        // Update other PLC tables if needed
        updateTable('sim-state-table', values.simulation);

        // Update last updated timestamp
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = new Date().toLocaleTimeString();
        }

    } catch (error) {
        console.error("Error fetching detailed values:", error);
         // Update last updated timestamp even on error
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = `Error at ${new Date().toLocaleTimeString()}`;
        }
    }
}


function initializeDetailsPage() {
    console.log("Initializing Details Page...");
    if (detailsIntervalId) clearInterval(detailsIntervalId);
    fetchAndUpdateDetails(); // Initial fetch
    detailsIntervalId = setInterval(fetchAndUpdateDetails, REFRESH_INTERVAL);
     console.log("Details Page initialized, interval set.");
}

// --- Tests Page Logic ---
function updateScenarioUI(scenarioId, resultData) {
    const scenarioDiv = document.getElementById(`scenario-${scenarioId}`);
    if (!scenarioDiv) return;

    const statusTextEl = scenarioDiv.querySelector('.status-text');
    const coilCheckEl = scenarioDiv.querySelector('.coil-check');
    const visualCheckEl = scenarioDiv.querySelector('.visual-check');
    const errorTextEl = scenarioDiv.querySelector('.error-text');
    const detailsTextEl = scenarioDiv.querySelector('.details-text');
    const visualButtonsDiv = scenarioDiv.querySelector('.visual-buttons');
    const runButton = scenarioDiv.querySelector('.run-button');

    // Update Status Text and Class
    statusTextEl.textContent = resultData.status || 'Unknown';
    statusTextEl.className = 'scenario-status status-text'; // Reset class
    if (resultData.status === 'Passed') statusTextEl.classList.add('passed');
    else if (resultData.status?.includes('Failed') || resultData.status === 'Error') statusTextEl.classList.add('failed');
    else if (resultData.status === 'Running') statusTextEl.classList.add('running');
    else if (resultData.status === 'Coil Check Passed') statusTextEl.classList.add('waiting'); // Waiting for visual

    // Update Checks
    coilCheckEl.textContent = resultData.coil_pass === true ? 'PASS' : resultData.coil_pass === false ? 'FAIL' : 'N/A';
    visualCheckEl.textContent = resultData.visual_pass === true ? 'PASS' : resultData.visual_pass === false ? 'FAIL' : 'N/A';
    coilCheckEl.style.color = resultData.coil_pass === true ? 'green' : resultData.coil_pass === false ? 'red' : 'inherit';
    visualCheckEl.style.color = resultData.visual_pass === true ? 'green' : resultData.visual_pass === false ? 'red' : 'inherit';


    // Update Error/Details
    errorTextEl.textContent = resultData.error || '';
    let detailsHtml = '';
    if(resultData.details) {
        for(const key in resultData.details) {
            detailsHtml += ` ${key}=${resultData.details[key]}`;
        }
    }
    detailsTextEl.textContent = detailsHtml.trim();


    // Show/Hide Visual Buttons
    const showVisualButtons = resultData.status === 'Coil Check Passed' && resultData.visual_pass === null;
    visualButtonsDiv.style.display = showVisualButtons ? 'block' : 'none';

    // Enable/Disable Run Button
    runButton.disabled = (resultData.status === 'Running');

}


async function runTest(scenarioId) {
    const scenarioDiv = document.getElementById(`scenario-${scenarioId}`);
    const runButton = scenarioDiv.querySelector('.run-button');
    const statusTextEl = scenarioDiv.querySelector('.status-text');
    const errorTextEl = scenarioDiv.querySelector('.error-text');

    runButton.disabled = true;
    statusTextEl.textContent = 'Running';
    statusTextEl.className = 'scenario-status status-text running';
    errorTextEl.textContent = ''; // Clear previous errors

     try {
        const response = await fetch(`${API_BASE_URL}/test-scenario/${scenarioId}/run`, { method: 'POST' });
        const result = await response.json();
         if (!response.ok) {
            // API returned an error status code
            throw new Error(result.error || `HTTP error ${response.status}`);
        }
        updateScenarioUI(scenarioId, result); // Update UI with final result from API

    } catch(error) {
        console.error(`Error running test ${scenarioId}:`, error);
        // Update UI to show error state
         updateScenarioUI(scenarioId, {
             status: 'Error',
             error: error.message || 'Failed to run test.',
             coil_pass: false, // Assume fail on error
             visual_pass: null
         });
    } finally {
        // Re-enable button unless it's now waiting for visual check
        const finalResult = window.testResultsData[scenarioId]; // Use global state if updated by API call
        if(finalResult && finalResult.status !== 'Coil Check Passed') {
             runButton.disabled = false;
        }
    }
}

async function recordVisual(scenarioId, passed) {
     const scenarioDiv = document.getElementById(`scenario-${scenarioId}`);
     const visualButtons = scenarioDiv.querySelector('.visual-buttons');
     visualButtons.style.display = 'none'; // Hide buttons immediately

      try {
        const response = await fetch(`${API_BASE_URL}/test-scenario/${scenarioId}/visual-check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ passed: passed })
        });
        const result = await response.json();
         if (!response.ok) {
             throw new Error(result.error || `HTTP error ${response.status}`);
         }
         updateScenarioUI(scenarioId, result); // Update UI with final result
         window.testResultsData[scenarioId] = result; // Update global state

    } catch(error) {
        console.error(`Error recording visual check for ${scenarioId}:`, error);
        alert(`Error recording visual check: ${error.message}`);
        // Optionally re-enable buttons or show error in UI
        visualButtons.style.display = 'block'; // Show buttons again on error
    }
}


function initializeTestsPage(scenarios, initialResults) {
    console.log("Initializing Tests Page...");
    // Store results globally for updates
    window.testResultsData = initialResults || {};

    document.querySelectorAll('.scenario').forEach(scenarioDiv => {
        const scenarioId = parseInt(scenarioDiv.dataset.scenarioId);
        const scenarioData = scenarios[scenarioId];

        // Populate initial state
        const initialResult = window.testResultsData[scenarioId] || { status: "Not Started" };
         // Display input values clearly
        const inputsTextEl = scenarioDiv.querySelector('.inputs-text');
        let inputsStr = '';
        if (scenarioData?.sim_inputs) { // or plc_inputs if using that
            inputsStr = Object.entries(scenarioData.sim_inputs).map(([key, val]) => `${key}=${val}`).join(', ');
        }
        inputsTextEl.textContent = inputsStr;

        updateScenarioUI(scenarioId, initialResult);


        // Add event listeners
        scenarioDiv.querySelector('.run-button').addEventListener('click', () => runTest(scenarioId));
        scenarioDiv.querySelector('.visual-pass-button').addEventListener('click', () => recordVisual(scenarioId, true));
        scenarioDiv.querySelector('.visual-fail-button').addEventListener('click', () => recordVisual(scenarioId, false));
    });
    console.log("Tests Page Initialized.");
}


// --- History Page Logic ---
function initializeHistoryPage() {
    console.log("Initializing History Page...");
    const tagSelect = document.getElementById('tag-select');
    const loadBtn = document.getElementById('load-history-btn');
    const chartCanvas = document.getElementById('history-chart');
    const statusEl = document.getElementById('history-status');

    if (!tagSelect || !loadBtn || !chartCanvas || !statusEl || typeof Chart === 'undefined') {
        console.error("History page elements or Chart.js not found.");
        statusEl.textContent = "Error initializing history page components.";
        return;
    }

    // Initialize Chart
    const ctx = chartCanvas.getContext('2d');
    historyChart = new Chart(ctx, {
        type: 'line',
        data: {
            // labels: [], // Timestamps
            datasets: [{
                label: 'Selected Tag Value',
                data: [], // {x: timestamp, y: value}
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
             responsive: true,
             maintainAspectRatio: false,
             scales: {
                 x: {
                     type: 'time', // Use time scale
                     time: {
                         unit: 'second', // Adjust unit as needed
                         displayFormats: {
                             second: 'HH:mm:ss'
                         }
                     },
                     title: { display: true, text: 'Time' }
                 },
                 y: {
                     beginAtZero: false, // Adjust as needed
                     title: { display: true, text: 'Value' }
                 }
             },
             plugins: {
                 tooltip: {
                     mode: 'index',
                     intersect: false
                 }
             }
        }
    });


    // Populate tag select dropdown (fetch available tags from state?)
    async function populateTags() {
         try {
            const response = await fetch(`${API_BASE_URL}/system-state`); // Fetch full state once
            const state = await response.json();
            tagSelect.innerHTML = '<option value="">-- Select Tag --</option>'; // Clear existing

            const tags = new Set();
            // Add PLC tags
            if (state.plc_data?.input_registers) {
                 Object.keys(state.plc_data.input_registers).forEach(addr => tags.add(`PLC_IW_${addr}`));
            }
             if (state.plc_data?.coils) {
                 Object.keys(state.plc_data.coils).forEach(addr => tags.add(`PLC_QX_${addr}`));
             }
            // Add Sim tags
            if (state.simulation_data) {
                 Object.keys(state.simulation_data).forEach(tag => tags.add(tag));
            }

            // Sort and add options
             Array.from(tags).sort().forEach(tag => {
                 const option = document.createElement('option');
                 option.value = tag;
                 option.textContent = tag;
                 tagSelect.appendChild(option);
             });

         } catch(error) {
             console.error("Error populating history tags:", error);
             statusEl.textContent = "Error loading available tags.";
         }
    }


    // Load history button action
    loadBtn.addEventListener('click', async () => {
        const selectedTag = tagSelect.value;
        if (!selectedTag) {
            statusEl.textContent = "Please select a tag.";
            return;
        }
        statusEl.textContent = `Loading history for ${selectedTag}...`;
        historyChart.data.datasets[0].label = `${selectedTag} Value`;


        try {
            const response = await fetch(`${API_BASE_URL}/history/${selectedTag}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const historyData = await response.json();
             const tagHistory = historyData[selectedTag] || [];

             // Format data for Chart.js time scale: {x: Date object, y: value}
             const chartData = tagHistory.map(point => ({
                 x: new Date(point[0] * 1000), // Convert Unix timestamp (seconds) to JS milliseconds
                 y: point[1]
             }));

             historyChart.data.datasets[0].data = chartData;
             historyChart.update();
             statusEl.textContent = `Loaded ${chartData.length} points for ${selectedTag}.`;


        } catch (error) {
             console.error(`Error fetching history for ${selectedTag}:`, error);
             statusEl.textContent = `Error loading history: ${error.message}`;
             historyChart.data.datasets[0].data = []; // Clear chart on error
             historyChart.update();
        }

    });

    populateTags(); // Populate tags on load
    console.log("History Page Initialized.");

}


// --- Global Cleanup ---
// Add logic to clear intervals if navigating away from SPA-like pages if needed
// window.addEventListener('beforeunload', () => {
//     if (statusIntervalId) clearInterval(statusIntervalId);
//     if (detailsIntervalId) clearInterval(detailsIntervalId);
// });