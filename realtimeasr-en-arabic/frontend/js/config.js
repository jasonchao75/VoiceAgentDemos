document.addEventListener("DOMContentLoaded", () => {
    let profiles = [];
    let currentProfile = null;

    let hotwordsData = [];
    let replacementsData = [];

    // DOM Elements
    const profileListEl = document.getElementById('profile-list');
    const profileNameInput = document.getElementById('profile-name');
    const editorTitle = document.getElementById('editor-title');
    const saveBtn = document.getElementById('save-profile-btn');

    const hwWordInput = document.getElementById('hw-word');
    const hwSoundsInput = document.getElementById('hw-sounds');
    const hwAddBtn = document.getElementById('hw-add-btn');
    const hwListContainer = document.getElementById('hotwords-list');

    const repFindInput = document.getElementById('rep-find');
    const repReplaceInput = document.getElementById('rep-replace');
    const repAddBtn = document.getElementById('rep-add-btn');
    const repListContainer = document.getElementById('replacements-list');

    const toastNotification = document.getElementById('toast-notification');
    const toastMessage = document.getElementById('toast-message');

    // Init
    loadProfiles();

    // Events
    hwAddBtn.addEventListener('click', addHotword);
    hwWordInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') addHotword(); });
    hwSoundsInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') addHotword(); });

    repAddBtn.addEventListener('click', addReplacement);
    repFindInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') addReplacement(); });
    repReplaceInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') addReplacement(); });

    saveBtn.addEventListener('click', saveProfile);

    // API URL Helper
    function getApiUrl(path) {
        if (window.location.protocol === 'file:') return `http://127.0.0.1:8010${path}`;
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') return `http://${window.location.hostname}:8010${path}`;
        return path;
    }

    function showNotification(message, type = 'info') {
        toastMessage.textContent = message;
        toastNotification.className = `toast-notification show ${type}`;
        setTimeout(() => { toastNotification.className = 'toast-notification'; }, 3000);
    }

    async function loadProfiles() {
        try {
            const res = await fetch(getApiUrl('/api/profiles'));
            const data = await res.json();
            profiles = data.profiles || [];
            renderProfileList();
        } catch (e) {
            console.error(e);
            showNotification('Failed to load profiles', 'error');
        }
    }

    function renderProfileList() {
        profileListEl.innerHTML = '';
        
        // Add "New Profile" button
        const newBtn = document.createElement('div');
        newBtn.className = `profile-item ${currentProfile === null ? 'active' : ''}`;
        newBtn.innerHTML = `<span class="profile-name"><i class="ph ph-plus"></i> Create New Profile</span>`;
        newBtn.onclick = () => selectProfile(null);
        profileListEl.appendChild(newBtn);

        profiles.forEach(p => {
            const el = document.createElement('div');
            el.className = `profile-item ${currentProfile && currentProfile.id === p.id ? 'active' : ''}`;
            el.innerHTML = `
                <span class="profile-name">${p.name}</span>
                <div class="profile-actions">
                    <button class="icon-btn delete-btn" title="Delete"><i class="ph ph-trash"></i></button>
                </div>
            `;
            
            el.onclick = (e) => {
                if(e.target.closest('.delete-btn')) {
                    e.stopPropagation();
                    deleteProfile(p.id);
                } else {
                    selectProfile(p);
                }
            };
            
            profileListEl.appendChild(el);
        });
    }

    function selectProfile(p) {
        currentProfile = p;
        if (p) {
            editorTitle.textContent = 'Edit Profile';
            profileNameInput.value = p.name;
            hotwordsData = JSON.parse(JSON.stringify(p.hotwords));
            replacementsData = JSON.parse(JSON.stringify(p.replacements));
        } else {
            editorTitle.textContent = 'Create New Profile';
            profileNameInput.value = '';
            hotwordsData = [];
            replacementsData = [];
        }
        renderHotwords();
        renderReplacements();
        renderProfileList();
    }

    async function saveProfile() {
        const name = profileNameInput.value.trim();
        if (!name) {
            showNotification('Please enter a profile name', 'error');
            return;
        }

        // Auto-add pending inputs
        if (hwWordInput.value.trim() !== '') addHotword();
        if (repFindInput.value.trim() !== '' && repReplaceInput.value.trim() !== '') addReplacement();

        const payload = {
            name: name,
            hotwords: hotwordsData,
            replacements: replacementsData
        };

        try {
            const res = await fetch(getApiUrl('/api/profiles'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error('Save failed');
            
            showNotification('Profile saved successfully');
            await loadProfiles();
            // Reselect the saved profile
            const saved = profiles.find(x => x.name === name);
            if (saved) selectProfile(saved);
            
        } catch (e) {
            console.error(e);
            showNotification('Failed to save profile', 'error');
        }
    }

    async function deleteProfile(id) {
        if (!confirm('Are you sure you want to delete this profile?')) return;
        
        try {
            const res = await fetch(getApiUrl(`/api/profiles/${id}`), { method: 'DELETE' });
            if (!res.ok) throw new Error('Delete failed');
            
            showNotification('Profile deleted');
            if (currentProfile && currentProfile.id === id) selectProfile(null);
            loadProfiles();
        } catch (e) {
            console.error(e);
            showNotification('Failed to delete profile', 'error');
        }
    }

    // --- Hotwords Logic ---
    function addHotword() {
        const word = hwWordInput.value.trim();
        const sounds = hwSoundsInput.value.trim();
        if (!word) return;

        let hwObj = { content: word };
        if (sounds) {
            hwObj.sounds_like = sounds.split(',').map(s => s.trim()).filter(s => s);
        }
        hotwordsData.push(hwObj);
        renderHotwords();
        hwWordInput.value = '';
        hwSoundsInput.value = '';
        hwWordInput.focus();
    }

    window.removeHotword = function(index) {
        hotwordsData.splice(index, 1);
        renderHotwords();
    }

    function renderHotwords() {
        hwListContainer.innerHTML = '';
        hotwordsData.forEach((hw, i) => {
            const tag = document.createElement('div');
            tag.className = `hw-tag ${hw.sounds_like && hw.sounds_like.length > 0 ? 'has-sounds-like' : ''}`;
            
            let html = `<span>${hw.content}</span>`;
            html += `<button class="remove-btn" onclick="removeHotword(${i})"><i class="ph ph-x"></i></button>`;
            
            if (hw.sounds_like && hw.sounds_like.length > 0) {
                html += `<div class="hw-tooltip">Sounds like: ${hw.sounds_like.join(', ')}</div>`;
            }
            
            tag.innerHTML = html;
            hwListContainer.appendChild(tag);
        });
    }

    // --- Replacements Logic ---
    function addReplacement() {
        const findWord = repFindInput.value.trim();
        const replaceWord = repReplaceInput.value.trim();
        if (!findWord || !replaceWord) return;

        replacementsData.push({ "from": findWord, "to": replaceWord });
        renderReplacements();
        repFindInput.value = '';
        repReplaceInput.value = '';
        repFindInput.focus();
    }

    window.removeReplacement = function(index) {
        replacementsData.splice(index, 1);
        renderReplacements();
    }

    function renderReplacements() {
        repListContainer.innerHTML = '';
        replacementsData.forEach((rep, i) => {
            const tag = document.createElement('div');
            tag.className = 'hw-tag';
            
            let html = `<span>${rep.from} &rarr; ${rep.to}</span>`;
            html += `<button class="remove-btn" onclick="removeReplacement(${i})"><i class="ph ph-x"></i></button>`;
            
            tag.innerHTML = html;
            repListContainer.appendChild(tag);
        });
    }
});