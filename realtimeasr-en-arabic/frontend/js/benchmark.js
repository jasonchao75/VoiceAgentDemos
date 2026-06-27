let API_BASE = '/api';
if (window.location.protocol === 'file:') {
    API_BASE = 'http://127.0.0.1:8010/api';
} else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    API_BASE = `http://${window.location.hostname}:8010/api`;
} else if (window.location.port && window.location.port !== '80' && window.location.port !== '443') {
    API_BASE = `http://${window.location.hostname}:8010/api`;
} else {
    API_BASE = '/api';
}

let activeRunId = null;
let pollInterval = null;

// UI Elements
const folderUpload = document.getElementById('folder-upload');
const fileUpload = document.getElementById('file-upload');
const uploadProgress = document.getElementById('upload-progress');
const libraryTree = document.getElementById('library-tree');
const profileSelect = document.getElementById('profile-select');
const runNameInput = document.getElementById('run-name');
const startBtn = document.getElementById('start-benchmark-btn');
const resultsBody = document.getElementById('results-body');
const currentRunStatus = document.getElementById('current-run-status');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadLibrary();
    loadProfiles();
    
    // Auto-generate run name
    const now = new Date();
    runNameInput.value = `Run ${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')} ${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
});

// Toast notification
function showToast(message) {
    const toast = document.getElementById('toast-notification');
    const msgEl = document.getElementById('toast-message');
    msgEl.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Load profiles
async function loadProfiles() {
    try {
        const response = await fetch(`${API_BASE}/profiles`);
        const data = await response.json();
        
        profileSelect.innerHTML = '<option value="">None</option>';
        data.profiles.forEach(profile => {
            const option = document.createElement('option');
            option.value = profile.id;
            option.textContent = profile.name;
            profileSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load profiles:', error);
    }
}

// Upload handler for both files and folders
async function handleUpload(files) {
    if (!files || files.length === 0) return;

    uploadProgress.style.display = 'block';
    uploadProgress.textContent = `Preparing ${files.length} files...`;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        // webkitRelativePath contains the full relative path
        const path = files[i].webkitRelativePath || files[i].name;
        formData.append('files', files[i]);
        formData.append('paths', path);
    }

    try {
        uploadProgress.textContent = 'Uploading...';
        const response = await fetch(`${API_BASE}/benchmark/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showToast('Uploaded successfully!');
            await loadLibrary();
        } else {
            const error = await response.json();
            showToast('Upload failed: ' + (error.detail || 'Unknown error'));
        }
    } catch (error) {
        showToast('Upload error: ' + error.message);
    } finally {
        uploadProgress.style.display = 'none';
        folderUpload.value = '';
        if (fileUpload) fileUpload.value = '';
    }
}

folderUpload.addEventListener('change', (e) => handleUpload(e.target.files));
if (fileUpload) {
    fileUpload.addEventListener('change', (e) => handleUpload(e.target.files));
}

// Load Library
async function loadLibrary() {
    try {
        const response = await fetch(`${API_BASE}/benchmark/library`);
        const data = await response.json();
        
        libraryTree.innerHTML = '';
        if (data.library.length === 0) {
            libraryTree.innerHTML = '<div style="color: var(--text-secondary); text-align: center; padding: 1rem;">No files uploaded yet.</div>';
            return;
        }
        
        renderTree(data.library, libraryTree);
    } catch (error) {
        console.error('Failed to load library:', error);
    }
}

function renderTree(nodes, container, isRoot = true) {
    nodes.forEach(node => {
        const div = document.createElement('div');
        div.className = `tree-node ${isRoot ? 'root' : ''}`;
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = node.path;
        checkbox.dataset.type = node.type;
        
        const icon = document.createElement('i');
        icon.className = node.type === 'directory' ? 'ph ph-folder' : 'ph ph-file-audio';
        
        const label = document.createElement('span');
        label.className = 'tree-label';
        label.textContent = node.name;
        
        div.appendChild(checkbox);
        div.appendChild(icon);
        div.appendChild(label);
        
        container.appendChild(div);
        
        // Handle directory checking
        checkbox.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            if (node.type === 'directory') {
                const childCheckboxes = childrenContainer.querySelectorAll('input[type="checkbox"]');
                childCheckboxes.forEach(cb => cb.checked = isChecked);
            }
        });
        
        let childrenContainer = null;
        if (node.type === 'directory' && node.children) {
            childrenContainer = document.createElement('div');
            // By default, open roots, collapse deep folders. For simplicity, just render all
            renderTree(node.children, childrenContainer, false);
            container.appendChild(childrenContainer);
        }
    });
}

// Start Benchmark
startBtn.addEventListener('click', async () => {
    // Gather files
    const allCheckboxes = libraryTree.querySelectorAll('input[type="checkbox"][data-type="file"]');
    const selectedFiles = Array.from(allCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.value);

    if (selectedFiles.length === 0) {
        showToast('Please select at least one file to benchmark.');
        return;
    }

    const runName = runNameInput.value.trim() || 'Untitled Run';
    const language = document.getElementById('language-select').value;
    const profileId = profileSelect.value ? parseInt(profileSelect.value) : null;

    try {
        startBtn.disabled = true;
        startBtn.innerHTML = '<i class="ph ph-spinner ph-spin button-icon"></i><span class="button-text">Starting...</span>';

        const response = await fetch(`${API_BASE}/benchmark/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                run_name: runName,
                language: language,
                profile_id: profileId,
                files: selectedFiles
            })
        });

        if (response.ok) {
            const data = await response.json();
            activeRunId = data.run_id;
            showToast('Benchmark started!');
            startPolling();
        } else {
            showToast('Failed to start benchmark.');
        }
    } catch (error) {
        showToast('Error: ' + error.message);
    } finally {
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="ph ph-play button-icon"></i><span class="button-text">Start Benchmark</span>';
    }
});

// Polling status
function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(fetchStatus, 1000);
    fetchStatus();
}

async function fetchStatus() {
    if (!activeRunId) return;

    try {
        const response = await fetch(`${API_BASE}/benchmark/status/${activeRunId}`);
        const data = await response.json();

        // Update run status badge
        currentRunStatus.style.display = 'inline-flex';
        currentRunStatus.textContent = data.run.status;
        currentRunStatus.className = `status-badge status-${data.run.status}`;

        // Stop polling if done
        if (data.run.status === 'completed' || data.run.status === 'failed') {
            clearInterval(pollInterval);
            pollInterval = null;
        }

        // Update results table
        resultsBody.innerHTML = '';
        data.results.forEach(res => {
            const tr = document.createElement('tr');
            
            const tdFile = document.createElement('td');
            tdFile.textContent = res.file_path;
            
            const tdStatus = document.createElement('td');
            const statusBadge = document.createElement('span');
            statusBadge.className = `status-badge status-${res.status}`;
            statusBadge.textContent = res.status;
            tdStatus.appendChild(statusBadge);
            
            const tdTranscript = document.createElement('td');
            if (res.status === 'error') {
                tdTranscript.textContent = res.error_message || 'Error';
                tdTranscript.style.color = 'var(--brand-danger)';
            } else {
                tdTranscript.textContent = res.final_transcript || '';
            }
            
            tr.appendChild(tdFile);
            tr.appendChild(tdStatus);
            tr.appendChild(tdTranscript);
            resultsBody.appendChild(tr);
        });

    } catch (error) {
        console.error('Failed to fetch status:', error);
    }
}
