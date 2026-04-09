// ========== CONFIGURATION ==========
const API_URL = 'http://localhost:8000/api/v1';
let sessionId = generateUUID();

// ========== UTILITY FUNCTIONS ==========
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function scrollToChat() {
    const chatSection = document.getElementById('chat');
    chatSection.scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => {
        document.getElementById('messageInput').focus();
    }, 500);
}

// ========== MESSAGE HANDLING ==========
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
                agent_type: 'general',
                use_rag: true,
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
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content ${isError ? 'error' : ''}">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    
    if (isError) {
        messageDiv.querySelector('.message-content').style.background = 'rgba(239, 68, 68, 0.2)';
        messageDiv.querySelector('.message-content').style.borderColor = 'rgba(239, 68, 68, 0.3)';
        messageDiv.querySelector('.message-content').style.color = '#fca5a5';
    }
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== COUNTER ANIMATION ==========
function animateCounter(element) {
    const target = parseInt(element.dataset.target);
    const duration = 2000;
    const step = target / (duration / 16);
    
    let current = 0;

    const interval = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(interval);
        }
        element.textContent = Math.floor(current).toLocaleString();
    }, 16);
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

// ========== SMOOTH SCROLL FOR ANCHOR LINKS ==========
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// ========== PARTICLE ANIMATION ==========
function createParticles() {
    const container = document.querySelector('.orbiting-particles');
    if (!container) return;

    const count = 3;
    for (let i = 0; i < count; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.cos((i * 2 * Math.PI) / count) * 150 + 150 + 'px';
        particle.style.top = Math.sin((i * 2 * Math.PI) / count) * 150 + 150 + 'px';
    }
}

// ========== INITIALIZATION ==========
document.addEventListener('DOMContentLoaded', () => {
    setupSmoothScroll();
    setupIntersectionObserver();
    createParticles();

    // Check if API is available
    checkAPIStatus();
});

async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_URL}/health`, {
            method: 'GET',
        });
        
        if (response.ok) {
            console.log('✅ API is running');
        }
    } catch (error) {
        console.warn('⚠️ API is not available at', API_URL);
    }
}

// ========== MOUSE TRACKING FOR HERO ANIMATION ==========
document.addEventListener('mousemove', (e) => {
    const orb = document.querySelector('.rotating-orb');
    if (!orb) return;

    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;

    orb.style.setProperty('--mouse-x', x);
    orb.style.setProperty('--mouse-y', y);
});

// ========== DARK MODE TOGGLE ==========
function toggleDarkMode() {
    document.body.classList.toggle('light-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('light-mode'));
}

// Check saved preference
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('light-mode');
}

// ========== ANALYTICS (Optional) ==========
function trackEvent(eventName, eventData = {}) {
    console.log('📊 Event:', eventName, eventData);
    // Could send to analytics service here
}

// Track when users interact with chat
document.getElementById('messageInput')?.addEventListener('focus', () => {
    trackEvent('chat_focused');
});

// ========== FEATURE CARDS HOVER EFFECT ==========
document.querySelectorAll('.feature-card').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transform = 'translateY(-5px) scale(1.02)';
    });
    
    card.addEventListener('mouseleave', function() {
        this.style.transform = 'translateY(0) scale(1)';
    });
});

// ========== SERVICE WORKER REGISTRATION (Optional) ==========
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {
        // Service worker registration failed - not critical
    });
}
