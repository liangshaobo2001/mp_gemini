document.addEventListener('DOMContentLoaded', init);

const PROJECT_NAME = "autoweb_demo";
const API_BASE = ""; // Relative path since we serve from same origin

function init() {
    // Chat Elements
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send');
    
    // Wireframe Elements
    const wireframeInput = document.getElementById('wireframe-input');
    const wireframeSendBtn = document.getElementById('wireframe-send');
    
    // Preview Elements
    const previewRefreshBtn = document.getElementById('preview-refresh');

    // Event Listeners
    chatSendBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });

    wireframeSendBtn.addEventListener('click', sendWireframe);
    previewRefreshBtn.addEventListener('click', refreshPreview);
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    const errorDiv = document.getElementById('chat-error');
    const sendBtn = document.getElementById('chat-send');

    if (!message) return;

    // UI Updates
    appendMessage('user', message);
    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;
    errorDiv.classList.add('hidden');

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project: PROJECT_NAME,
                message: message,
                history: [] // Server handles history internally
            })
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const data = await response.json();
        
        if (data.reply) {
            appendMessage('assistant', data.reply);
        } else {
            appendMessage('system', 'No reply received from agent.');
        }

        // Auto-refresh preview if files changed
        if (data.files && Object.keys(data.files).length > 0) {
            refreshPreview();
        }

    } catch (err) {
        console.error(err);
        errorDiv.textContent = "Error connecting to agent. Check console.";
        errorDiv.classList.remove('hidden');
        appendMessage('system', 'Error: Failed to send message.');
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }
}

async function sendWireframe() {
    const input = document.getElementById('wireframe-input');
    const statusDiv = document.getElementById('wireframe-status');
    const sendBtn = document.getElementById('wireframe-send');
    
    statusDiv.textContent = "Generating...";
    statusDiv.className = "status-message";
    sendBtn.disabled = true;

    try {
        const jsonContent = JSON.parse(input.value);
        
        const response = await fetch(`${API_BASE}/wireframe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jsonContent)
        });

        if (!response.ok) throw new Error(`Server error: ${response.status}`);

        const data = await response.json();
        
        statusDiv.textContent = "Success! Layout generated.";
        statusDiv.classList.add('success');
        
        if (data.reply) {
            appendMessage('assistant', `[Wireframe]: ${data.reply}`);
        }

        refreshPreview();

    } catch (err) {
        console.error(err);
        statusDiv.textContent = err instanceof SyntaxError 
            ? "Invalid JSON format." 
            : "Generation failed. Check console.";
        statusDiv.classList.add('error');
    } finally {
        sendBtn.disabled = false;
    }
}

function refreshPreview() {
    const iframe = document.getElementById('preview-frame');
    // Add timestamp to force reload and bypass cache
    iframe.src = `/preview?t=${new Date().getTime()}`;
}

function appendMessage(role, text) {
    const historyDiv = document.getElementById('chat-history');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;
    
    // Simple markdown-like formatting for code blocks could go here, 
    // but for now we just set textContent to be safe against XSS
    msgDiv.textContent = text;
    
    historyDiv.appendChild(msgDiv);
    historyDiv.scrollTop = historyDiv.scrollHeight;
}
