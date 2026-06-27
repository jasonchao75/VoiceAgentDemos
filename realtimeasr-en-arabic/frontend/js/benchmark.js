let API_BASE = '/api';
// In production (https://demo.dyna.ai), use relative paths to route through Nginx
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
let targetUploadFolder = '';
let currentLibraryData = [];

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
        let path = files[i].webkitRelativePath || files[i].name;
        if (targetUploadFolder && !files[i].webkitRelativePath) {
            path = targetUploadFolder + '/' + files[i].name;
        } else if (targetUploadFolder && files[i].webkitRelativePath) {
            path = targetUploadFolder + '/' + files[i].webkitRelativePath;
        }
        
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
        targetUploadFolder = ''; // Reset target folder after upload
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
        
        currentLibraryData = data.library;
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
        
        let labelText = node.name;
        if (node.type === 'file' && node.sample_rate) {
            labelText = `<span style="color: var(--text-tertiary); font-size: 0.75rem; margin-right: 0.25rem;">[${node.sample_rate}]</span>${node.name}`;
        }
        label.innerHTML = labelText;
        
        const actions = document.createElement('div');
        actions.className = 'tree-actions';
        
        if (node.type === 'directory') {
            // Upload to this folder
            const btnUpload = document.createElement('button');
            btnUpload.className = 'tree-action-btn';
            btnUpload.innerHTML = '<i class="ph ph-upload"></i>';
            btnUpload.title = 'Upload files here';
            btnUpload.onclick = (e) => {
                targetUploadFolder = node.path;
                document.getElementById('file-upload').click();
            };
            
            // New folder
            const btnNewFolder = document.createElement('button');
            btnNewFolder.className = 'tree-action-btn';
            btnNewFolder.innerHTML = '<i class="ph ph-folder-plus"></i>';
            btnNewFolder.title = 'New folder';
            btnNewFolder.onclick = async (e) => {
                const name = prompt('Enter new folder name:');
                if (name) {
                    await createFolder(node.path + '/' + name);
                }
            };
            
            actions.appendChild(btnUpload);
            actions.appendChild(btnNewFolder);
        }
        
        // Delete (for both)
        const btnDelete = document.createElement('button');
        btnDelete.className = 'tree-action-btn';
        btnDelete.innerHTML = '<i class="ph ph-trash"></i>';
        btnDelete.title = node.type === 'directory' ? 'Delete folder (if empty)' : 'Delete file';
        btnDelete.onclick = async (e) => {
            if (confirm(`Delete ${node.type === 'directory' ? 'folder' : 'file'} ${node.name}?`)) {
                await deleteItem(node.path);
            }
        };
        
        // Rename (for both)
        const btnRename = document.createElement('button');
        btnRename.className = 'tree-action-btn';
        btnRename.innerHTML = '<i class="ph ph-pencil-simple"></i>';
        btnRename.title = 'Rename';
        btnRename.onclick = async (e) => {
            const newName = prompt('Enter new name:', node.name);
            if (newName && newName !== node.name) {
                const parentPath = node.path.substring(0, node.path.lastIndexOf('/'));
                const newPath = parentPath ? `${parentPath}/${newName}` : newName;
                await moveItem(node.path, newPath);
            }
        };
        
        // Move (for both)
        const btnMove = document.createElement('button');
        btnMove.className = 'tree-action-btn';
        btnMove.innerHTML = '<i class="ph ph-arrows-out-line-horizontal"></i>';
        btnMove.title = 'Move';
        btnMove.onclick = (e) => {
            openMoveModal(node.path, node.type);
        };
        
        actions.appendChild(btnRename);
        actions.appendChild(btnMove);
        actions.appendChild(btnDelete);
        
        div.appendChild(checkbox);
        div.appendChild(icon);
        div.appendChild(label);
        div.appendChild(actions);
        
        container.appendChild(div);
        
        // Handle directory checking
        checkbox.addEventListener('change', (e) => {
            const isChecked = e.target.checked;
            if (node.type === 'directory') {
                if (childrenContainer) {
                    const childCheckboxes = childrenContainer.querySelectorAll('input[type="checkbox"]');
                    childCheckboxes.forEach(cb => cb.checked = isChecked);
                }
            }
        });
        
        let childrenContainer = null;
        if (node.type === 'directory' && node.children) {
            childrenContainer = document.createElement('div');
            childrenContainer.className = 'tree-children';
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

// --- Folder & File Management ---

async function createFolder(path) {
    try {
        const response = await fetch(`${API_BASE}/benchmark/folder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        if (response.ok) {
            showToast('Folder created');
            await loadLibrary();
        } else {
            const err = await response.json();
            showToast('Error: ' + (err.detail || 'Unknown'));
        }
    } catch (error) {
        showToast('Error: ' + error.message);
    }
}

async function deleteItem(path) {
    try {
        const response = await fetch(`${API_BASE}/benchmark/item?path=${encodeURIComponent(path)}`, {
            method: 'DELETE'
        });
        if (response.ok) {
            showToast('Deleted successfully');
            await loadLibrary();
        } else {
            const err = await response.json();
            showToast('Error: ' + (err.detail || 'Unknown'));
        }
    } catch (error) {
        showToast('Error: ' + error.message);
    }
}

async function moveItem(sourcePath, targetPath) {
    try {
        const response = await fetch(`${API_BASE}/benchmark/move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: sourcePath, target: targetPath })
        });
        if (response.ok) {
            showToast('Moved/Renamed successfully');
            await loadLibrary();
        } else {
            const err = await response.json();
            showToast('Error: ' + (err.detail || 'Unknown'));
        }
    } catch (error) {
        showToast('Error: ' + error.message);
    }
}

// Move Modal Logic
const moveModal = document.getElementById('move-modal');
const moveTargetSelect = document.getElementById('move-target-select');
const moveCancelBtn = document.getElementById('move-cancel-btn');
const moveConfirmBtn = document.getElementById('move-confirm-btn');
let currentMoveSource = '';

function getAllDirectories(nodes, prefix = '') {
    let dirs = [];
    nodes.forEach(node => {
        if (node.type === 'directory') {
            dirs.push(node.path);
            if (node.children) {
                dirs = dirs.concat(getAllDirectories(node.children));
            }
        }
    });
    return dirs;
}

function openMoveModal(sourcePath, type) {
    currentMoveSource = sourcePath;
    const itemName = sourcePath.substring(sourcePath.lastIndexOf('/') + 1);
    document.getElementById('move-modal-title').textContent = `Move ${itemName}`;
    
    // Populate select
    const allDirs = getAllDirectories(currentLibraryData);
    moveTargetSelect.innerHTML = '<option value="">(Root)</option>';
    allDirs.forEach(dir => {
        // Prevent moving a folder into itself or its own subfolders
        if (type === 'directory' && (dir === sourcePath || dir.startsWith(sourcePath + '/'))) {
            return; 
        }
        const option = document.createElement('option');
        option.value = dir;
        option.textContent = dir;
        moveTargetSelect.appendChild(option);
    });
    
    moveModal.style.display = 'flex';
}

moveCancelBtn.addEventListener('click', () => {
    moveModal.style.display = 'none';
    currentMoveSource = '';
});

moveConfirmBtn.addEventListener('click', async () => {
    if (!currentMoveSource) return;
    const targetDir = moveTargetSelect.value;
    const itemName = currentMoveSource.substring(currentMoveSource.lastIndexOf('/') + 1);
    const targetPath = targetDir ? `${targetDir}/${itemName}` : itemName;
    
    if (targetPath === currentMoveSource) {
        showToast('Source and target are the same.');
        moveModal.style.display = 'none';
        return;
    }
    
    moveModal.style.display = 'none';
    await moveItem(currentMoveSource, targetPath);
});
