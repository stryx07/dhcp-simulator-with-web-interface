let trafficChart = null;
let typeChart = null;

async function runSimulation(type) {
    const statusDiv = document.getElementById('sim-status');
    statusDiv.textContent = `Running ${type} simulation...`;

    try {
        const response = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type })
        });

        const data = await response.json();
        if (data.error) {
            statusDiv.textContent = `Error: ${data.error}`;
            return;
        }

        statusDiv.textContent = `Simulation complete (ID: ${data.scenario_id}). Loading data...`;
        loadScenarioData(data.scenario_id);
    } catch (e) {
        statusDiv.textContent = `Error: ${e.message}`;
    }
}

async function loadScenarioData(scenarioId) {
    const response = await fetch(`/api/scenario/${scenarioId}/data`);
    const data = await response.json();

    updateCharts(data.logs);
    updateLogs(data.logs);
}

function updateCharts(logs) {
    // Process data for charts
    const timeLabels = [];
    const packetCounts = {};
    const messageTypes = {};

    logs.forEach(log => {
        const time = log.timestamp.split('T')[1].split('.')[0]; // HH:MM:SS
        if (!timeLabels.includes(time)) timeLabels.push(time);

        packetCounts[time] = (packetCounts[time] || 0) + 1;
        messageTypes[log.message_type] = (messageTypes[log.message_type] || 0) + 1;
    });

    // Traffic Chart
    const trafficCtx = document.getElementById('trafficChart').getContext('2d');
    if (trafficChart) trafficChart.destroy();

    trafficChart = new Chart(trafficCtx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: 'Packets / Second',
                data: timeLabels.map(t => packetCounts[t]),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                x: { grid: { display: false } }
            }
        }
    });

    // Type Chart
    const typeCtx = document.getElementById('typeChart').getContext('2d');
    if (typeChart) typeChart.destroy();

    typeChart = new Chart(typeCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(messageTypes),
            datasets: [{
                data: Object.values(messageTypes),
                backgroundColor: [
                    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'right' } }
        }
    });
}

function updateLogs(logs) {
    const viewer = document.getElementById('log-viewer');
    viewer.innerHTML = logs.map(log => `
        <div class="log-entry ${log.is_anomaly ? 'anomaly' : ''}">
            [${log.timestamp.replace('T', ' ')}] ${log.message_type} - ${log.mac_address} ${log.ip_address ? '-> ' + log.ip_address : ''} : ${log.details}
        </div>
    `).join('');
    viewer.scrollTop = viewer.scrollHeight;
}

// --- Real Attack Dashboard Logic ---

async function startAttack(type) {
    const iface = document.getElementById('iface').value;
    const targetIp = document.getElementById('target_ip').value;
    
    // UI Feedback immediately
    const row = document.getElementById(`row-${type}`);
    const startBtn = row.querySelector('.start-btn');
    startBtn.disabled = true;
    startBtn.textContent = "Starting...";

    try {
        const response = await fetch('/api/attack/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                type: type,
                iface: iface,
                target_ip: targetIp
            })
        });
        const data = await response.json();
        if (data.status !== 'started') {
            alert("Error: " + data.message);
            startBtn.disabled = false;
            startBtn.textContent = "Start Attack";
        } else {
            checkStatus(); // Update UI
        }
    } catch(e) {
        alert("Network Error: " + e);
        startBtn.disabled = false;
        startBtn.textContent = "Start Attack";
    }
}

async function stopAttack(type) {
    try {
        await fetch('/api/attack/stop', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({type: type})
        });
        checkStatus();
    } catch(e) {
        console.error(e);
    }
}

async function checkStatus() {
    try {
        const response = await fetch('/api/attack/status');
        const status = await response.json();
        
        // Loop through keys and update UI
        for (const [type, isRunning] of Object.entries(status)) {
            updateRowStatus(type, isRunning);
        }
    } catch(e) {
        console.error("Status poll failed", e);
    }
}

function updateRowStatus(type, isRunning) {
    const row = document.getElementById(`row-${type}`);
    if (!row) return; // Not on dashboard page
    
    const badge = row.querySelector('.status-badge');
    const startBtn = row.querySelector('.start-btn');
    const stopBtn = row.querySelector('.stop-btn');
    
    if (isRunning) {
        badge.className = 'badge bg-success status-badge fw-bold px-3 py-2';
        badge.innerHTML = '<span class="spinner-grow spinner-grow-sm me-1" role="status" aria-hidden="true"></span>Running';
        
        startBtn.classList.add('d-none');
        startBtn.disabled = false; // Reset state
        startBtn.textContent = "Start Attack";
        
        stopBtn.classList.remove('d-none');
    } else {
        badge.className = 'badge bg-secondary status-badge';
        badge.textContent = 'Stopped';
        
        startBtn.classList.remove('d-none');
        startBtn.disabled = false;
        
        stopBtn.classList.add('d-none');
    }
}

async function runRecon() {
    const btn = document.querySelector('button[onclick="runRecon()"]');
    const spinner = document.getElementById('recon-spinner');
    const resultDiv = document.getElementById('recon-result');
    const iface = document.getElementById('iface').value;

    btn.disabled = true;
    spinner.classList.remove('d-none');
    resultDiv.innerHTML = "Scanning...";

    try {
        const response = await fetch('/api/recon', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({iface: iface})
        });
        const data = await response.json();
        
        if (data.error) {
            resultDiv.innerHTML = `<span class="text-danger">Error: ${data.error}</span>`;
        } else if (data.result) {
             resultDiv.innerHTML = `<span class="text-warning">${data.result}</span>`;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-success mt-2">
                    <strong>DHCP Server Found!</strong><br>
                    IP: ${data.server_ip}<br>
                    MAC: ${data.server_mac}<br>
                    Offer IP: ${data.offered_ip}
                </div>
            `;
        }
    } catch(e) {
        resultDiv.innerHTML = `<span class="text-danger">Communication Error</span>`;
    } finally {
        btn.disabled = false;
        spinner.classList.add('d-none');
    }
}

// Poll status if on dashbaord
if (document.getElementById('row-starvation')) {
    setInterval(checkStatus, 2000);
    checkStatus();
}
