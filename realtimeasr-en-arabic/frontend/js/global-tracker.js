// Global Benchmark Task Tracker
(function() {
    // Determine API Base URL
    let apiBaseUrl = '/api';
    if (window.location.protocol === 'file:') {
        apiBaseUrl = 'http://127.0.0.1:8010/api';
    } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        apiBaseUrl = `http://${window.location.hostname}:8010/api`;
    } else if (window.location.port && window.location.port !== '80' && window.location.port !== '443') {
        apiBaseUrl = `http://${window.location.hostname}:8010/api`;
    } else {
        apiBaseUrl = '/api';
    }

    async function checkActiveRuns() {
        try {
            const response = await fetch(`${apiBaseUrl}/benchmark/runs`);
            if (!response.ok) return;
            const data = await response.json();
            
            const activeRun = (data.runs || []).find(run => run.status === 'running');
            
            const indicator = document.getElementById('global-benchmark-indicator');
            const text = document.getElementById('global-benchmark-text');
            
            if (activeRun) {
                if (indicator && text) {
                    // Truncate run name if too long
                    let display_name = activeRun.run_name;
                    if (display_name.length > 20) {
                        display_name = display_name.substring(0, 17) + '...';
                    }
                    text.textContent = `Running: ${display_name}`;
                    indicator.style.display = 'flex';
                }
            } else {
                if (indicator) {
                    indicator.style.display = 'none';
                }
            }
        } catch (error) {
            console.error('Failed to check active runs:', error);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        // Initial check
        checkActiveRuns();
        // Poll every 5 seconds
        setInterval(checkActiveRuns, 5000);
    });
})();
