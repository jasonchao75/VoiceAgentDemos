// WebCall Arabic - main frontend application logic
// Contract v2.0: SQLite DB, Hotwords (additional_vocab), Bento Grid UI

let ws = null;
let audioContext = null;
let audioWorkletNode = null;
let mediaStream = null;
let isRecording = false;
let recordingStartTime = null;
let timerInterval = null;
let transcriptCounter = 0;
let currentLanguage = 'ar';
let profiles = [];
let currentProfile = null;

let partialBuffer = null;
let rafScheduled = false;

const MAX_DURATION_MS = 120000; // 2 minutes
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_HOST = window.location.hostname || 'localhost';

function normalizeWsOrigin(value) {
    const t = (value || '').trim().replace(/\/+$/, '');
    if (!t) return '';
    if (!/^wss?:\/\//i.test(t)) return '';
    return t;
}

function getTranscribeWebSocketBaseUrl() {
    if (window.location.protocol === 'file:') return 'ws://127.0.0.1:8010';
    const port = window.location.port;
    const isHttps = window.location.protocol === 'https:';
    if (!port || (isHttps && port === '443') || (!isHttps && port === '80')) {
        return `${WS_PROTOCOL}//${WS_HOST}`;
    }
    if (!isHttps) return `${WS_PROTOCOL}//${WS_HOST}:8010`;
    return `${WS_PROTOCOL}//${WS_HOST}:${port}`;
}

const languageDirectionMap = {
    'ar': 'rtl',
    'en': 'ltr',
    'ar_en': 'auto'
};

// DOM references
const languageSelect = document.getElementById('language-select');
const profileSelect = document.getElementById('profile-select');
const controlButton = document.getElementById('control-button');
const buttonText = controlButton.querySelector('.button-text');
const buttonIcon = controlButton.querySelector('.button-icon');
const recordingIndicator = document.getElementById('recording-indicator');
const timerText = document.getElementById('timer-text');
const transcriptArea = document.getElementById('transcript-area');
const transcriptContent = document.getElementById('transcript-content');
const clearHistoryButton = document.getElementById('clear-history-button');

// Toast & Modal
const toastNotification = document.getElementById('toast-notification');
const toastMessage = document.getElementById('toast-message');
const downloadModal = document.getElementById('download-modal');
const modalDownloadBtn = document.getElementById('modal-download-btn');
const modalCloseBtn = document.getElementById('modal-close-btn');

// Events
languageSelect.addEventListener('change', (e) => {
    currentLanguage = e.target.value;
    transcriptArea.setAttribute('dir', languageDirectionMap[currentLanguage]);
});
profileSelect.addEventListener('change', (e) => {
    const profileId = parseInt(e.target.value, 10);
    currentProfile = profiles.find(p => p.id === profileId) || null;
});
controlButton.addEventListener('click', handleControlButtonClick);
clearHistoryButton.addEventListener('click', handleClearHistory);

modalCloseBtn.addEventListener('click', () => {
    downloadModal.style.display = 'none';
});

// Load Profiles
async function loadProfiles() {
    try {
        let apiUrl = '/api/profiles';
        if (window.location.protocol === 'file:') {
            apiUrl = 'http://127.0.0.1:8010/api/profiles';
        } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            apiUrl = `http://${window.location.hostname}:8010/api/profiles`;
        }

        const res = await fetch(apiUrl);
        const data = await res.json();
        profiles = data.profiles || [];
        
        // Populate select
        profileSelect.innerHTML = '<option value="">None</option>';
        profiles.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            profileSelect.appendChild(opt);
        });
    } catch (e) {
        console.error('Failed to load profiles:', e);
    }
}

// Call load on init
document.addEventListener("DOMContentLoaded", loadProfiles);

async function handleControlButtonClick() {
    if (!isRecording) await startRecording();
    else stopRecording();
}

async function startRecording() {
    try {
        let activeHotwords = [];
        let activeReplacements = [];

        if (currentProfile) {
            activeHotwords = currentProfile.hotwords || [];
            activeReplacements = currentProfile.replacements || [];
        }

        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
        });

        audioContext = new AudioContext({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(mediaStream);

        await audioContext.audioWorklet.addModule('js/audio-worklet-processor.js');
        audioWorkletNode = new AudioWorkletNode(audioContext, 'pcm-processor');

        audioWorkletNode.port.onmessage = (event) => {
            if (ws && ws.readyState === WebSocket.OPEN && event.data) {
                ws.send(event.data);
            }
        };

        source.connect(audioWorkletNode);
        audioWorkletNode.connect(audioContext.destination);

        const wsUrl = `${getTranscribeWebSocketBaseUrl()}/ws/transcribe?language=${currentLanguage}`;
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            // Send start action with hotwords array and replacements
            ws.send(JSON.stringify({ 
                action: 'start',
                hotwords: activeHotwords,
                replacements: activeReplacements
            }));
            
            isRecording = true;
            updateUIState();
            startTimer();
            removeEmptyState();
        };

        ws.onmessage = (event) => handleWebSocketMessage(event);
        ws.onerror = () => {
            showNotification('Connection failed. Check network or API Key.', 'error');
            stopRecording();
        };
        ws.onclose = (e) => {
            if (e.code !== 1000 && isRecording) showNotification('Connection lost.', 'error');
            stopRecording();
        };

    } catch (error) {
        console.error(error);
        showNotification('Failed to start recording. Please check microphone permissions.', 'error');
    }
}

function stopRecording() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'end' }));
        // Note: Do not ws.close() immediately, let the server send "saved" event
    }
    if (audioWorkletNode) { audioWorkletNode.disconnect(); audioWorkletNode = null; }
    if (audioContext) { audioContext.close(); audioContext = null; }
    if (mediaStream) { mediaStream.getTracks().forEach(track => track.stop()); mediaStream = null; }

    const partialItem = document.getElementById('partial-transcript');
    if (partialItem) partialItem.remove();

    const items = transcriptContent.querySelectorAll('.transcript-item:not(#partial-transcript)');
    items.forEach(item => {
        const textDiv = item.querySelector('.transcript-text');
        if (textDiv && item.dataset.finalText) {
            textDiv.textContent = item.dataset.finalText;
            delete item.dataset.finalText;
        }
    });

    isRecording = false;
    updateUIState();
    stopTimer();
}

function handleWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);
        switch (data.type) {
            case 'session_started': break;
            case 'partial': handlePartialTranscript(data); break;
            case 'final': handleFinalTranscript(data); break;
            case 'saved': 
                showDownloadModal(data.download_url); 
                if (ws) { ws.close(); ws = null; }
                break;
            case 'error':
                showNotification(data.message || 'An error occurred', 'error');
                if (ws) { ws.close(); ws = null; }
                break;
        }
    } catch (error) {}
}

function handlePartialTranscript(data) {
    partialBuffer = data;
    if (!rafScheduled) {
        rafScheduled = true;
        requestAnimationFrame(() => {
            if (partialBuffer) { updatePartialDisplay(partialBuffer); partialBuffer = null; }
            rafScheduled = false;
        });
    }
}

function updatePartialDisplay(data) {
    const { text, speaker } = data;
    if (!text.trim()) return;

    const items = transcriptContent.querySelectorAll('.transcript-item:not(#partial-transcript)');
    const lastItem = items.length > 0 ? items[items.length - 1] : null;

    if (lastItem && !lastItem.classList.contains('empty-state')) {
        const lastSpeakerBadge = lastItem.querySelector('.speaker-badge');
        const lastSpeaker = lastSpeakerBadge ? lastSpeakerBadge.textContent : null;

        if (lastSpeaker === `Speaker ${speaker.replace('S', '')}`) {
            const textDiv = lastItem.querySelector('.transcript-text');
            if (textDiv) {
                if (!lastItem.dataset.finalText) lastItem.dataset.finalText = textDiv.textContent;
                textDiv.innerHTML = `${lastItem.dataset.finalText} <span class="interim">${text}</span>`;
                transcriptArea.scrollTop = transcriptArea.scrollHeight;
                return;
            }
        }
    }

    let partialItem = document.getElementById('partial-transcript');
    if (!partialItem) {
        partialItem = document.createElement('div');
        partialItem.id = 'partial-transcript';
        partialItem.className = 'transcript-item';
        transcriptContent.appendChild(partialItem);
    }

    let html = '';
    if (speaker) html += `<div class="speaker-badge">Speaker ${speaker.replace('S', '')}</div>`;
    html += `<div class="transcript-text interim" dir="${languageDirectionMap[currentLanguage]}">${text}</div>`;
    partialItem.innerHTML = html;
    transcriptArea.scrollTop = transcriptArea.scrollHeight;
}

function handleFinalTranscript(data) {
    const { text, speaker } = data;
    if (!text.trim()) return;

    const partialItem = document.getElementById('partial-transcript');
    if (partialItem) partialItem.remove();

    const items = transcriptContent.querySelectorAll('.transcript-item:not(#partial-transcript)');
    const lastItem = items.length > 0 ? items[items.length - 1] : null;

    if (lastItem && !lastItem.classList.contains('empty-state')) {
        const lastSpeakerBadge = lastItem.querySelector('.speaker-badge');
        const lastSpeaker = lastSpeakerBadge ? lastSpeakerBadge.textContent : null;

        if (lastSpeaker === `Speaker ${speaker.replace('S', '')}`) {
            const textDiv = lastItem.querySelector('.transcript-text');
            if (textDiv) {
                const currentText = lastItem.dataset.finalText || textDiv.textContent.trim();
                delete lastItem.dataset.finalText;
                textDiv.textContent = currentText + ' ' + text;
                transcriptArea.scrollTop = transcriptArea.scrollHeight;
                return;
            }
        }
    }

    transcriptCounter++;
    const finalItem = document.createElement('div');
    finalItem.id = `transcript-${transcriptCounter}`;
    finalItem.className = 'transcript-item';

    let html = '';
    if (speaker) html += `<div class="speaker-badge">Speaker ${speaker.replace('S', '')}</div>`;
    html += `<div class="transcript-text" dir="${languageDirectionMap[currentLanguage]}">${text}</div>`;

    finalItem.innerHTML = html;
    transcriptContent.appendChild(finalItem);
    transcriptArea.scrollTop = transcriptArea.scrollHeight;
}

function updateUIState() {
    if (isRecording) {
        controlButton.classList.add('recording');
        buttonText.textContent = 'Stop Session';
        buttonIcon.classList.remove('ph-microphone');
        buttonIcon.classList.add('ph-stop-circle');
        languageSelect.disabled = true;
        recordingIndicator.style.display = 'flex';
    } else {
        controlButton.classList.remove('recording');
        buttonText.textContent = 'Start Session';
        buttonIcon.classList.add('ph-microphone');
        buttonIcon.classList.remove('ph-stop-circle');
        languageSelect.disabled = false;
        recordingIndicator.style.display = 'none';
    }
}

function startTimer() {
    recordingStartTime = Date.now();
    timerInterval = setInterval(() => {
        const elapsed = Date.now() - recordingStartTime;
        if (elapsed >= MAX_DURATION_MS) {
            clearInterval(timerInterval);
            stopRecording();
            showNotification('Max duration reached.', 'info');
            return;
        }
        const seconds = Math.floor(elapsed / 1000);
        timerText.textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
    }, 1000);
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
    timerText.textContent = '00:00';
}

function removeEmptyState() {
    const emptyState = transcriptContent.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
}

function handleClearHistory() {
    if (isRecording) {
        showNotification('Cannot clear while recording', 'error');
        return;
    }
    transcriptContent.innerHTML = '<div class="empty-state"><i class="ph ph-waveform empty-icon"></i><p>Ready to transcribe. Click "Start Session" to begin.</p></div>';
    transcriptCounter = 0;
}

function showNotification(message, type = 'info') {
    toastMessage.textContent = message;
    toastNotification.className = 'toast-notification show';
    setTimeout(() => { toastNotification.className = 'toast-notification'; }, 3000);
}

function showDownloadModal(url) {
    // Only show if backend sends a valid download URL
    if (url) {
        // Construct absolute URL for local file:// access safety
        let fullUrl = url;
        if (window.location.protocol === 'file:') {
            fullUrl = `http://127.0.0.1:8010${url}`;
        } else if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            fullUrl = `http://${window.location.hostname}:8010${url}`;
        }
        modalDownloadBtn.href = fullUrl;
        downloadModal.style.display = 'flex';
    }
}
