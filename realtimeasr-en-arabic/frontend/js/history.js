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
                
                let extra_actions = '';
                if (run.status === 'running') {
                    extra_actions = `
                        <button class="action-btn" style="color: var(--brand-danger); border-color: rgba(225,29,72,0.3); background: rgba(225,29,72,0.02);" onclick="stopBenchmarkRun(${run.id}, event)">
                            <i class="ph ph-stop"></i> Stop
                        </button>
                    `;
                } else if (['cancelled', 'interrupted', 'failed'].includes(run.status)) {
                    extra_actions = `
                        <button class="action-btn" style="color: var(--brand-success); border-color: rgba(46,204,113,0.3); background: rgba(46,204,113,0.02);" onclick="resumeBenchmarkRun(${run.id}, event)">
                            <i class="ph ph-play"></i> Continue
                        </button>
                    `;
                }

                tr.innerHTML = `
                    <td class="col-id" style="font-weight:500;">${run.run_name}</td>
                    <td class="col-lang"><span style="background: var(--bg-surface-hover); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; border: 1px solid var(--border-subtle);">${run.language.toUpperCase()}</span></td>
                    <td><span class="status-badge status-${run.status}">${run.status}</span></td>
                    <td class="col-date" style="font-size: 0.875rem; color: var(--text-secondary);">${dateObj.toLocaleString()}</td>
                    <td class="col-action" style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                        <button class="action-btn" onclick="showBenchmarkResults(${run.id})">
                            <i class="ph ph-eye"></i> View Results
                        </button>
                        ${extra_actions}
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

async function stopBenchmarkRun(runId, event) {
    if (event) event.stopPropagation();
    if (!confirm("Are you sure you want to stop this benchmark run?")) return;
    
    try {
        const response = await fetch(`${apiBaseUrl}/benchmark/stop/${runId}`, {
            method: 'POST'
        });
        if (response.ok) {
            await loadBenchmarkRuns();
        } else {
            const err = await response.json();
            alert("Error: " + (err.detail || "Failed to stop run"));
        }
    } catch (error) {
        console.error('Failed to stop benchmark run:', error);
    }
}

async function resumeBenchmarkRun(runId, event) {
    if (event) event.stopPropagation();
    if (!confirm("Do you want to continue this benchmark run? Already completed files will be skipped.")) return;
    
    try {
        const response = await fetch(`${apiBaseUrl}/benchmark/resume/${runId}`, {
            method: 'POST'
        });
        if (response.ok) {
            await loadBenchmarkRuns();
        } else {
            const err = await response.json();
            alert("Error: " + (err.detail || "Failed to resume run"));
        }
    } catch (error) {
        console.error('Failed to resume benchmark:', error);
    }
}

async function showBenchmarkResults(runId) {
    const modal = document.getElementById('benchmark-modal');
    const tbody = document.getElementById('benchmark-modal-tbody');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Loading...</td></tr>';
    modal.style.display = 'flex';
    
    const overallWerContainer = document.getElementById('modal-overall-wer-container');
    const overallWerValue = document.getElementById('modal-overall-wer-value');
    const overallAccValue = document.getElementById('modal-overall-acc-value');
    if (overallWerContainer) {
        overallWerContainer.style.display = 'none';
    }
    
    try {
        const response = await fetch(`${apiBaseUrl}/benchmark/status/${runId}`);
        const data = await response.json();
        
        tbody.innerHTML = '';
        let totalWerErrors = 0;
        let totalWerWords = 0;
        
        data.results.forEach(res => {
            const tr = document.createElement('tr');
            
            const tdFile = document.createElement('td');
            tdFile.textContent = res.file_path;
            tdFile.style.fontFamily = "'Satoshi', monospace";
            tdFile.style.fontSize = "0.8rem";
            tdFile.style.color = "var(--text-secondary)";
            tdFile.style.padding = '0.5rem';
            tdFile.style.borderBottom = '1px solid var(--border-subtle)';
            
            const tdStatus = document.createElement('td');
            tdStatus.style.padding = '0.5rem';
            tdStatus.style.borderBottom = '1px solid var(--border-subtle)';
            tdStatus.innerHTML = `<span class="status-badge status-${res.status}">${res.status}</span>`;
            
            const tdWer = document.createElement('td');
            tdWer.style.padding = '0.5rem';
            tdWer.style.borderBottom = '1px solid var(--border-subtle)';
            if (res.wer !== null && res.wer !== undefined) {
                // Cap displayed individual WER at 100% for better UI presentation
                const displayedWer = Math.min(1.0, res.wer);
                const werPct = (displayedWer * 100).toFixed(1);
                tdWer.innerHTML = `<span style="font-weight:600; color: ${res.wer > 0 ? 'var(--brand-danger)' : 'var(--brand-success)'}">${werPct}%</span>`;
                
                // Accumulate for overall Micro WER
                if (res.wer_errors !== null && res.wer_words !== null) {
                    totalWerErrors += res.wer_errors;
                    totalWerWords += res.wer_words;
                }
            } else {
                tdWer.innerHTML = '<span style="color:var(--text-tertiary)">-</span>';
            }
            
            const tdGroundTruth = document.createElement('td');
            tdGroundTruth.textContent = res.ground_truth || '-';
            tdGroundTruth.style.color = 'var(--text-secondary)';
            tdGroundTruth.style.fontSize = "0.9rem";
            tdGroundTruth.dir = "auto";
            tdGroundTruth.style.padding = '0.5rem';
            tdGroundTruth.style.borderBottom = '1px solid var(--border-subtle)';
            
            const tdTranscript = document.createElement('td');
            tdTranscript.style.padding = '0.5rem';
            tdTranscript.style.borderBottom = '1px solid var(--border-subtle)';
            if (res.status === 'error') {
                tdTranscript.textContent = res.error_message || 'Error';
                tdTranscript.style.color = 'var(--brand-danger)';
            } else {
                tdTranscript.textContent = res.final_transcript || '';
                tdTranscript.style.fontSize = "0.9rem";
                tdTranscript.dir = "auto";
            }
            
            tr.appendChild(tdFile);
            tr.appendChild(tdStatus);
            tr.appendChild(tdWer);
            tr.appendChild(tdGroundTruth);
            tr.appendChild(tdTranscript);
            tbody.appendChild(tr);
        });
        
        // Update overall WER macro inside modal
        if (overallWerContainer && overallWerValue && overallAccValue) {
            if (totalWerWords > 0) {
                const microWer = totalWerErrors / totalWerWords;
                const acc = Math.max(0, 1 - microWer);
                overallWerValue.textContent = (microWer * 100).toFixed(2) + '%';
                overallAccValue.textContent = (acc * 100).toFixed(2) + '%';
                overallWerContainer.style.display = 'flex';
                
                overallWerValue.style.color = microWer > 0 ? 'var(--brand-danger)' : 'var(--brand-success)';
                overallAccValue.style.color = acc === 1 ? 'var(--brand-success)' : (acc > 0.9 ? 'var(--text-primary)' : 'var(--brand-danger)');
            } else {
                overallWerContainer.style.display = 'none';
            }
        }
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:red;">Error loading results</td></tr>';
    }
}

let allHistoryRecords = [];

document.addEventListener("DOMContentLoaded", async () => {
    const tbody = document.getElementById('history-tbody');
    
    let apiUrl = `${apiBaseUrl}/history`;
    
    try {
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        if (data.records && data.records.length > 0) {
            allHistoryRecords = data.records;
            renderHistoryTable(allHistoryRecords);
        } else {
            allHistoryRecords = [];
            renderEmptyHistory();
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

    // Filter Elements
    const filterDate = document.getElementById('filter-date');
    const filterLanguage = document.getElementById('filter-language');
    const filterTranscript = document.getElementById('filter-transcript');
    const clearFiltersBtn = document.getElementById('clear-filters-btn');

    function applyFilters() {
        if (!allHistoryRecords.length) return;

        const dateVal = filterDate.value; // YYYY-MM-DD
        const langVal = filterLanguage.value.toLowerCase();
        const textVal = filterTranscript.value.toLowerCase();

        const filtered = allHistoryRecords.filter(record => {
            // Filter by language
            if (langVal && record.language.toLowerCase() !== langVal) {
                return false;
            }
            
            // Filter by transcript text
            if (textVal) {
                const text = (record.final_transcript || "").toLowerCase();
                if (!text.includes(textVal)) {
                    return false;
                }
            }
            
            // Filter by date
            if (dateVal) {
                const recordDate = new Date(record.created_at + "Z");
                // Local date string in YYYY-MM-DD format
                const year = recordDate.getFullYear();
                const month = String(recordDate.getMonth() + 1).padStart(2, '0');
                const day = String(recordDate.getDate()).padStart(2, '0');
                const localDateStr = `${year}-${month}-${day}`;
                
                if (localDateStr !== dateVal) {
                    return false;
                }
            }

            return true;
        });

        if (filtered.length > 0) {
            renderHistoryTable(filtered);
        } else {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; padding: 4rem; color: var(--text-tertiary);">
                        <i class="ph ph-funnel-x" style="font-size: 3rem; opacity: 0.5; margin-bottom: 1rem; display: block;"></i>
                        No records match your filters.
                    </td>
                </tr>
            `;
        }
        updateBulkActions();
    }

    [filterDate, filterLanguage, filterTranscript].forEach(el => {
        if (el) el.addEventListener('input', applyFilters);
    });

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            filterDate.value = '';
            filterLanguage.value = '';
            filterTranscript.value = '';
            renderHistoryTable(allHistoryRecords);
            updateBulkActions();
        });
    }

    function renderEmptyHistory() {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 4rem; color: var(--text-tertiary);">
                    <i class="ph ph-folder-open" style="font-size: 3rem; opacity: 0.5; margin-bottom: 1rem; display: block;"></i>
                    No transcription history found in the database.
                </td>
            </tr>
        `;
    }

    function renderHistoryTable(records) {
        tbody.innerHTML = '';
        records.forEach(record => {
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
    }

    const selectAll = document.getElementById('select-all-history');
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCount = document.getElementById('selected-count');
    const exportBtn = document.getElementById('export-benchmark-btn');
    const downloadZipBtn = document.getElementById('download-zip-btn');
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

    if (downloadZipBtn) {
        downloadZipBtn.addEventListener('click', async () => {
            const checked = Array.from(document.querySelectorAll('.history-checkbox:checked')).map(cb => cb.value);
            if (checked.length === 0) return;

            downloadZipBtn.disabled = true;
            downloadZipBtn.innerHTML = '<i class="ph ph-spinner-gap ph-spin"></i> Downloading...';

            try {
                const response = await fetch(`${apiBaseUrl}/history/download_zip`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_ids: checked,
                        target_folder: "" // Not used for ZIP
                    })
                });

                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = "transcriptions_history.zip";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    
                    document.querySelectorAll('.history-checkbox').forEach(cb => cb.checked = false);
                    updateBulkActions();
                } else {
                    alert('Download failed.');
                }
            } catch (error) {
                console.error(error);
                alert('Download error.');
            } finally {
                downloadZipBtn.disabled = false;
                downloadZipBtn.innerHTML = '<i class="ph ph-file-zip"></i> Download ZIP';
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
