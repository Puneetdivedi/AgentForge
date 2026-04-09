// ========== CONFIGURATION ==========
const API_URL = 'http://localhost:8000/api/v1';
let sessionId = generateUUID();
let currentAgent = 'general';

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', function() {
    setupTimeDisplay();
    setupCounterAnimation();
    setupIntersectionObserver();
});

// ========== UTILITY FUNCTIONS ==========
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAlert(message) {
    alert(message);
}

// ========== TIME DISPLAY ==========
function setupTimeDisplay() {
    function updateTime() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        document.getElementById('timeDisplay').textContent = `${hours}:${minutes}`;
    }
    
    updateTime();
    setInterval(updateTime, 1000);
}

// ========== VIEW SWITCHING ==========
function switchView(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    
    // Show selected view
    const selectedView = document.getElementById(viewName);
    if (selectedView) {
        selectedView.classList.add('active');
    }
    
    // Update active nav button
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    event.target.closest('.nav-btn').classList.add('active');
    
    // Trigger animations if needed
    if (viewName === 'dashboard' || viewName === 'analytics') {
        setupCounterAnimation();
    }
}

// ========== AGENT SELECTION ==========
function selectAgent(agentType, buttonElement) {
    currentAgent = agentType;
    
    // Update button styling
    document.querySelectorAll('.agent-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    buttonElement.classList.add('active');
    
    // Update agent info
    const agentNames = {
        'general': 'General AI Agent',
        'rag': 'Knowledge Base Agent',
        'sql': 'Data Analytics Agent'
    };
    
    document.getElementById('selectedAgentInfo').textContent = `Using: ${agentNames[agentType]}`;
    
    // Clear chat messages when switching agents
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="message bot-message">
            <div class="message-avatar">🤖</div>
            <div class="message-bubble">
                <p>${agentNames[agentType]} is ready. How can I help?</p>
                <span class="timestamp">just now</span>
            </div>
        </div>
    `;
}

// ========== CHAT FUNCTIONALITY ==========
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;

    // Add user message to chat
    addMessage(message, 'user');
    input.value = '';

    // Show loading indicator
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'flex';

    try {
        // Send message to API
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: 'demo_user',
                session_id: sessionId,
                message: message,
                agent_type: currentAgent,
                use_rag: currentAgent === 'rag',
                stream: false
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        
        // Add bot response
        addMessage(data.message, 'bot');
    } catch (error) {
        console.error('Error:', error);
        let errorMessage = 'Unable to get response. ';
        
        if (error.message.includes('Failed to fetch')) {
            errorMessage += 'Please ensure the API server is running on http://localhost:8000';
        } else {
            errorMessage += error.message;
        }
        
        addMessage(errorMessage, 'bot', true);
    } finally {
        loadingIndicator.style.display = 'none';
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function addMessage(text, sender, isError = false) {
    const chatMessages = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = sender === 'user' ? '👤' : '🤖';
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { 
        hour: '2-digit',
        minute: '2-digit',
        hour12: true 
    });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-bubble ${isError ? 'error' : ''}">
            <p>${escapeHtml(text)}</p>
            <span class="timestamp">${timeStr}</span>
        </div>
    `;
    
    if (isError) {
        messageDiv.querySelector('.message-bubble').style.background = 'rgba(239, 68, 68, 0.2)';
        messageDiv.querySelector('.message-bubble').style.borderColor = 'rgba(239, 68, 68, 0.3)';
        messageDiv.querySelector('.message-bubble').style.color = '#fca5a5';
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ========== COUNTER ANIMATION ==========
function animateCounter(element) {
    if (element.dataset.animated === 'true') return;
    
    const target = parseInt(element.dataset.target);
    const duration = 2000;
    const step = target / (duration / 16);
    
    let current = 0;

    const interval = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(interval);
            element.dataset.animated = 'true';
        }
        element.textContent = Math.floor(current).toLocaleString();
    }, 16);
}

function setupCounterAnimation() {
    const counters = document.querySelectorAll('.counter');
    
    if (counters.length === 0) {
        // If no counters visible, set up intersection observer
        setupIntersectionObserver();
        return;
    }
    
    counters.forEach(counter => {
        if (counter.dataset.animated !== 'true') {
            animateCounter(counter);
        }
    });
}

// ========== INTERSECTION OBSERVER ==========
function setupIntersectionObserver() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                if (entry.target.classList.contains('counter')) {
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('.counter').forEach(el => {
        observer.observe(el);
    });
}
