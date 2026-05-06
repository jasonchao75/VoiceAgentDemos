// History Dashboard Logic

document.addEventListener("DOMContentLoaded", async () => {
    const tbody = document.getElementById('history-tbody');
    
    // Construct API URL
    let apiUrl = '/api/history';
    if (window.location.protocol === 'file:') {
        apiUrl = 'http://127.0.0.1:8010/api/history';
    } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        apiUrl = `http://${window.location.hostname}:8010/api/history`;
    }

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
                }

                // Truncate text for snippet
                const snippet = record.final_transcript || "<span style='color: var(--text-tertiary); font-style: italic;'>No speech detected</span>";

                tr.innerHTML = `
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
                    <td colspan="5" style="text-align: center; padding: 4rem; color: var(--text-tertiary);">
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
                <td colspan="5" style="text-align: center; padding: 3rem; color: var(--brand-danger);">
                    <i class="ph ph-warning-circle" style="font-size: 2rem; margin-bottom: 1rem; display: block;"></i>
                    Failed to connect to the backend server. Please ensure it is running.
                </td>
            </tr>
        `;
    }
});
