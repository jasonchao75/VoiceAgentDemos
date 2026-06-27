// History Dashboard Logic

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

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.color = 'var(--text-secondary)';
    });
    const activeBtn = document.querySelector(`.tab-btn[onclick="switchTab('${tab}')"]`);
    if(activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.style.color = 'var(--brand-primary)';
    }

    document.getElementById('demo-section').style.display = tab === 'demo' ? 'block' : 'none';
    document.getElementById('benchmark-section').style.display = tab === 'benchmark' ? 'block' : 'none';

    if (tab === 'benchmark') {
        loadBenchmarkRuns();
    }
}

async function loadBenchmarkRuns() {
    const tbody = document.getElementById('benchmark-tbody');
    try {
        const response = await fetch(`${apiBaseUrl}/benchmark/runs`);
        const data = await response.json();
        
        if (data.runs && data.runs.length > 0) {
            tbody.innerHTML = '';
            data.runs.forEach(run => {
                const tr = document.createElement('tr');
                const dateObj = new Date(run.created_at + "Z");
                
                tr.innerHTML = `
                    <td class="col-id" style="font-weight:500;">${run.run_name}</td>
                    <td class="col-lang"><span style="background: var(--bg-surface-hover); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; border: 1px solid var(--border-subtle);">${run.language.toUpperCase()}</span></td>
                    <td><span class="status-badge status-${run.status}">${run.status}</span></td>
                    <td class="col-date" style="font-size: 0.875rem; color: var(--text-secondary);">${dateObj.toLocaleString()}</td>
                    <td class="col-action">
                        <button class="action-btn" onclick="showBenchmarkResults(${run.id})">
                            <i class="ph ph-eye"></i> View Results
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 4rem; color: var(--text-tertiary);">No benchmark runs found.</td></tr>`;
        }
    } catch (error) {
        console.error('Failed to load benchmark runs:', error);
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 3rem; color: var(--brand-danger);">Failed to load data.</td></tr>`;
    }
}

async function showBenchmarkResults(runId) {
    const modal = document.getElementById('benchmark-modal');
    const tbody = document.getElementById('benchmark-modal-tbody');
    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">Loading...</td></tr>';
    modal.style.display = 'flex';
    
    try {
        const response = await fetch(`${apiBaseUrl}/benchmark/status/${runId}`);
        const data = await response.json();
        
        tbody.innerHTML = '';
        data.results.forEach(res => {
            const tr = document.createElement('tr');
            
            const tdFile = document.createElement('td');
            tdFile.textContent = res.file_path;
            tdFile.style.padding = '0.5rem';
            tdFile.style.borderBottom = '1px solid var(--border-subtle)';
            
            const tdStatus = document.createElement('td');
            tdStatus.style.padding = '0.5rem';
            tdStatus.style.borderBottom = '1px solid var(--border-subtle)';
            tdStatus.innerHTML = `<span class="status-badge status-${res.status}">${res.status}</span>`;
            
            const tdTranscript = document.createElement('td');
            tdTranscript.style.padding = '0.5rem';
            tdTranscript.style.borderBottom = '1px solid var(--border-subtle)';
            if (res.status === 'error') {
                tdTranscript.textContent = res.error_message || 'Error';
                tdTranscript.style.color = 'var(--brand-danger)';
            } else {
                tdTranscript.textContent = res.final_transcript || '';
            }
            
            tr.appendChild(tdFile);
            tr.appendChild(tdStatus);
            tr.appendChild(tdTranscript);
            tbody.appendChild(tr);
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:red;">Error loading results</td></tr>';
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    const tbody = document.getElementById('history-tbody');
    
    let apiUrl = `${apiBaseUrl}/history`;
    
    try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (data.records && data.records.length > 0) {
            tbody.innerHTML = '';
            data.records.forEach(record => {
                const tr = document.createElement('tr');
                
                // Format Date
                const dateObj = new Date(record.created_at + "Z"); // SQLite default is UTC usually
                const dateStr = dateObj.toLocaleString();
                
                // Construct download URL
                let downloadUrl = `/api/download/${record.session_id}`;
                let downloadLogUrl = `/api/download_log/${record.session_id}`;
                if (window.location.protocol === 'file:') {
                    downloadUrl = `http://127.0.0.1:8010${downloadUrl}`;
                    downloadLogUrl = `http://127.0.0.1:8010${downloadLogUrl}`;
                } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    downloadUrl = `http://${window.location.hostname}:8010${downloadUrl}`;
                    downloadLogUrl = `http://${window.location.hostname}:8010${downloadLogUrl}`;
                } else if (window.location.port && window.location.port !== '80' && window.location.port !== '443') {
                    downloadUrl = `http://${window.location.hostname}:8010${downloadUrl}`;
                    downloadLogUrl = `http://${window.location.hostname}:8010${downloadLogUrl}`;
                }

                // Truncate text for snippet
                const snippet = record.final_transcript || "<span style='color: var(--text-tertiary); font-style: italic;'>No speech detected</span>";

                tr.innerHTML = `
                    <td style="padding-left: 1rem;">
                        <input type="checkbox" class="history-checkbox" value="${record.session_id}">
                    </td>
                    <td class="col-id" style="font-family: 'Satoshi', monospace; font-size: 0.8rem; color: var(--text-secondary);">
                        ${record.session_id.substring(0, 8)}...
                    </td>
                    <td class="col-lang">
                        <span style="background: var(--bg-surface-hover); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; border: 1px solid var(--border-subtle);">
                            ${record.language.toUpperCase()}
                        </span>
                    </td>
                    <td class="col-text">
                        <div class="text-preview" dir="${record.language.startsWith('ar') ? 'rtl' : 'ltr'}">${snippet}</div>
                    </td>
                    <td class="col-date" style="font-size: 0.875rem; color: var(--text-secondary);">
                        ${dateStr}
                    </td>
                    <td class="col-action" style="display: flex; gap: 0.5rem;">
                        <a href="${downloadUrl}" target="_blank" class="action-btn">
                            <i class="ph ph-download-simple"></i> Audio
                        </a>
                        <a href="${downloadLogUrl}" target="_blank" class="action-btn">
                            <i class="ph ph-file-text"></i> Log
                        </a>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 4rem; color: var(--text-tertiary);">
                        <i class="ph ph-folder-open" style="font-size: 3rem; opacity: 0.5; margin-bottom: 1rem; display: block;"></i>
                        No transcription history found in the database.
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Failed to load history:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 3rem; color: var(--brand-danger);">
                    <i class="ph ph-warning-circle" style="font-size: 2rem; margin-bottom: 1rem; display: block;"></i>
                    Failed to connect to the backend server. Please ensure it is running.
                </td>
            </tr>
        `;
    }

    const selectAll = document.getElementById('select-all-history');
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCount = document.getElementById('selected-count');
    const exportBtn = document.getElementById('export-benchmark-btn');
    const exportModal = document.getElementById('export-modal');
    const confirmExportBtn = document.getElementById('confirm-export-btn');
    const folderInput = document.getElementById('export-folder-name');

    function updateBulkActions() {
        if (!bulkActions) return;
        const checkboxes = document.querySelectorAll('.history-checkbox');
        const checked = Array.from(checkboxes).filter(cb => cb.checked);
        if (checked.length > 0) {
            bulkActions.style.display = 'flex';
            selectedCount.textContent = `${checked.length} selected`;
            if(selectAll) selectAll.checked = checked.length === checkboxes.length;
        } else {
            bulkActions.style.display = 'none';
            if(selectAll) selectAll.checked = false;
        }
    }

    if (selectAll) {
        selectAll.addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.history-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
            updateBulkActions();
        });
    }

    if (tbody) {
        tbody.addEventListener('change', (e) => {
            if (e.target.classList.contains('history-checkbox')) {
                updateBulkActions();
            }
        });
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', () => {
            folderInput.value = '';
            exportModal.style.display = 'flex';
        });
    }

    if (confirmExportBtn) {
        confirmExportBtn.addEventListener('click', async () => {
            const folderName = folderInput.value.trim();
            if (!folderName) {
                alert('Please enter a folder name');
                return;
            }
            const checked = Array.from(document.querySelectorAll('.history-checkbox:checked')).map(cb => cb.value);
            if (checked.length === 0) return;

            confirmExportBtn.disabled = true;
            confirmExportBtn.textContent = 'Exporting...';

            try {
                const response = await fetch(`${apiBaseUrl}/history/export_to_benchmark`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_ids: checked,
                        target_folder: folderName
                    })
                });

                if (response.ok) {
                    alert('Exported successfully!');
                    exportModal.style.display = 'none';
                    document.querySelectorAll('.history-checkbox').forEach(cb => cb.checked = false);
                    updateBulkActions();
                } else {
                    alert('Export failed.');
                }
            } catch (error) {
                console.error(error);
                alert('Export error.');
            } finally {
                confirmExportBtn.disabled = false;
                confirmExportBtn.textContent = 'Export';
            }
        });
    }
});
