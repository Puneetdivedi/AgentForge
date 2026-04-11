/* ========================================
   AgentForge Dashboard - JavaScript Functions
   ======================================== */

class Dashboard {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.charts = {};
        this.metrics = {};
        this.currentConversation = null;
        this.currentAgent = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startMetricsUpdates();
        this.initCharts();
    }

    setupEventListeners() {
        // Navigation tabs
        document.getElementById('dashboardTab').addEventListener('click', () => this.switchTab('dashboard'));
        document.getElementById('chatTab').addEventListener('click', () => this.switchTab('chat'));
        document.getElementById('agentsTab').addEventListener('click', () => this.switchTab('agents'));
        document.getElementById('metricsTab').addEventListener('click', () => this.switchTab('metrics'));

        // Chat
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        document.getElementById('chatInput').addEventListener('input', (e) => {
            document.getElementById('charCount').textContent = `${e.target.value.length}/500 characters`;
        });

        document.getElementById('agentSelect').addEventListener('change', (e) => {
            this.currentAgent = e.target.value;
            this.clearChat();
        });

        // Agents
        document.getElementById('createAgentBtn').addEventListener('click', () => {
            const modal = new bootstrap.Modal(document.getElementById('createAgentModal'));
            modal.show();
        });

        // Time range selector
        document.querySelectorAll('.time-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.time-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateCharts(e.target.dataset.range);
            });
        });
    }

    switchTab(tab) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        
        // Show selected section
        document.getElementById(`${tab}-section`).classList.add('active');

        // Update nav
        document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
        document.getElementById(`${tab}Tab`).classList.add('active');

        // Scroll to top
        window.scrollTo(0, 0);

        // Trigger refresh for charts
        if (tab === 'metrics') {
            setTimeout(() => {
                Object.values(this.charts).forEach(chart => chart.resize());
            }, 100);
        }
    }

    async loadInitialData() {
        try {
            const response = await fetch(`${this.apiBase}/health`);
            const data = await response.json();
            this.updateStatus('Online');
            this.loadMetrics();
        } catch (error) {
            console.warn('Could not connect to API:', error);
            this.updateStatus('Offline');
        }
    }

    async loadMetrics() {
        try {
            const response = await fetch(`${this.apiBase}/api/v1/admin/metrics`);
            const data = await response.json();
            this.metrics = data;
            this.updateDashboard();
        } catch (error) {
            console.warn('Could not load metrics:', error);
        }
    }

    updateDashboard() {
        // Update stat cards
        document.getElementById('healthScore').textContent = '98%';
        document.getElementById('healthStatus').textContent = 'Excellent';
        
        document.getElementById('totalRequests').textContent = (Math.random() * 5000 + 1000).toFixed(0);
        document.getElementById('requestRate').textContent = (Math.random() * 500 + 50).toFixed(0) + ' req/min';
        
        document.getElementById('activeAgents').textContent = '3';
        document.getElementById('agentStatus').textContent = 'All running';
        
        document.getElementById('avgLatency').textContent = (Math.random() * 200 + 45).toFixed(0);
        
        // Update progress rings
        this.updateProgressRing('successCircle', 95);
        this.updateProgressRing('errorCircle', 2);
        this.updateProgressRing('uptimeCircle', 99);
    }

    updateProgressRing(elementId, percentage) {
        const circle = document.getElementById(elementId);
        const circumference = 2 * Math.PI * 15.915;
        const offset = circumference - (percentage / 100) * circumference;
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        circle.style.strokeDashoffset = offset;

        // Update percentage text
        const textId = elementId.replace('Circle', 'Rate');
        if (elementId === 'uptimeCircle') {
            document.getElementById('uptime').textContent = percentage;
        } else if (elementId === 'successCircle') {
            document.getElementById('successRate').textContent = percentage;
        } else {
            document.getElementById('errorRate').textContent = percentage;
        }
    }

    updateStatus(status) {
        const badge = document.getElementById('statusBadge');
        badge.textContent = status;
        badge.className = status === 'Online' ? 'badge bg-success' : 'badge bg-danger';
    }

    startMetricsUpdates() {
        setInterval(() => {
            this.loadMetrics();
        }, 5000);
    }

    initCharts() {
        this.initRequestChart();
        this.initResponseTimeChart();
        this.initThroughputChart();
        this.initAgentPieChart();
        this.initErrorChart();
    }

    initRequestChart() {
        const ctx = document.getElementById('requestChart').getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(79, 70, 229, 0.3)');
        gradient.addColorStop(1, 'rgba(79, 70, 229, 0.0)');

        this.charts.requests = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.generateTimeLabels(24),
                datasets: [{
                    label: 'Requests',
                    data: this.generateRandomData(24, 500, 2000),
                    borderColor: '#4F46E5',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#4F46E5',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(51, 65, 85, 0.3)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#CBD5E1',
                            font: { size: 12 }
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            color: '#CBD5E1',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    initResponseTimeChart() {
        const ctx = document.getElementById('responseTimeChart').getContext('2d');
        
        this.charts.responseTime = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.generateTimeLabels(24),
                datasets: [
                    {
                        label: 'Average',
                        data: this.generateRandomData(24, 100, 400),
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointBackgroundColor: '#10B981',
                    },
                    {
                        label: 'P95',
                        data: this.generateRandomData(24, 200, 800),
                        borderColor: '#F59E0B',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointBackgroundColor: '#F59E0B',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#CBD5E1',
                            usePointStyle: true,
                            padding: 15,
                            font: { size: 12 }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(51, 65, 85, 0.3)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#CBD5E1',
                            font: { size: 12 }
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            color: '#CBD5E1',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    initThroughputChart() {
        const ctx = document.getElementById('throughputChart');
        if (!ctx) return;

        const context = ctx.getContext('2d');
        const gradient = context.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(79, 70, 229, 0.4)');
        gradient.addColorStop(1, 'rgba(79, 70, 229, 0.0)');

        this.charts.throughput = new Chart(context, {
            type: 'bar',
            data: {
                labels: this.generateTimeLabels(24),
                datasets: [{
                    label: 'Throughput (requests)',
                    data: this.generateRandomData(24, 1000, 5000),
                    backgroundColor: gradient,
                    borderColor: '#4F46E5',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(51, 65, 85, 0.3)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#CBD5E1',
                            font: { size: 12 }
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            color: '#CBD5E1',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    initAgentPieChart() {
        const ctx = document.getElementById('agentPieChart');
        if (!ctx) return;

        this.charts.agentPie = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['General Agent', 'RAG Agent', 'SQL Agent'],
                datasets: [{
                    data: [45, 35, 20],
                    backgroundColor: [
                        '#4F46E5',
                        '#10B981',
                        '#F59E0B'
                    ],
                    borderColor: '#1E293B',
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#CBD5E1',
                            padding: 20,
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    initErrorChart() {
        const ctx = document.getElementById('errorChart');
        if (!ctx) return;

        this.charts.error = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Validation', '4XX', '5XX', 'Timeout', 'Other'],
                datasets: [{
                    label: 'Errors',
                    data: [12, 8, 3, 5, 2],
                    backgroundColor: '#EF4444',
                    borderColor: '#DC2626',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(51, 65, 85, 0.3)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#CBD5E1',
                            font: { size: 12 }
                        }
                    },
                    y: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            color: '#CBD5E1',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    updateCharts(range) {
        if (this.charts.throughput) {
            this.charts.throughput.data.labels = this.generateTimeLabels(range === '24h' ? 24 : range === '7d' ? 7 : 30);
            this.charts.throughput.data.datasets[0].data = this.generateRandomData(
                range === '24h' ? 24 : range === '7d' ? 7 : 30,
                1000,
                5000
            );
            this.charts.throughput.update();
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();

        if (!message || !this.currentAgent) {
            this.showToast('Please select an agent and enter a message');
            return;
        }

        // Add user message
        this.addMessageToChat(message, 'user');
        input.value = '';
        document.getElementById('charCount').textContent = '0/500 characters';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch(`${this.apiBase}/api/v1/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    agent: this.currentAgent,
                    session_id: this.currentConversation || 'new'
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.removeTypingIndicator();
                this.addMessageToChat(data.response || 'No response', 'agent');
                this.showToast('Message sent successfully');
            } else {
                this.removeTypingIndicator();
                this.addMessageToChat('Error processing message', 'agent');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.removeTypingIndicator();
            this.addMessageToChat('Connection error. Please try again.', 'agent');
        }
    }

    addMessageToChat(text, sender) {
        const messagesDiv = document.getElementById('chatMessages');
        
        // Remove system message if it exists
        const systemMsg = messagesDiv.querySelector('.system-message');
        if (systemMsg) {
            systemMsg.remove();
        }

        const messageEl = document.createElement('div');
        messageEl.className = `message ${sender} animate__animated animate__slideInUp`;
        messageEl.innerHTML = `
            <div class="message-content">
                <p>${this.escapeHtml(text)}</p>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;

        messagesDiv.appendChild(messageEl);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    showTypingIndicator() {
        const messagesDiv = document.getElementById('chatMessages');
        const typingEl = document.createElement('div');
        typingEl.className = 'message agent';
        typingEl.id = 'typing-indicator';
        typingEl.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        messagesDiv.appendChild(typingEl);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    removeTypingIndicator() {
        const typingEl = document.getElementById('typing-indicator');
        if (typingEl) {
            typingEl.remove();
        }
    }

    clearChat() {
        document.getElementById('chatMessages').innerHTML = `
            <div class="system-message animate__animated animate__fadeIn">
                <i class="fas fa-info-circle"></i> Chat cleared. Start a new conversation.
            </div>
        `;
    }

    showToast(message) {
        const toast = document.getElementById('toast');
        document.getElementById('toastMessage').textContent = message;
        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    generateTimeLabels(count) {
        const labels = [];
        const now = new Date();
        for (let i = count - 1; i >= 0; i--) {
            const date = new Date(now);
            if (count > 7) {
                date.setHours(date.getHours() - i);
                labels.push(date.getHours() + ':00');
            } else {
                date.setDate(date.getDate() - i);
                labels.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
            }
        }
        return labels;
    }

    generateRandomData(count, min, max) {
        return Array.from({ length: count }, () => 
            Math.floor(Math.random() * (max - min + 1)) + min
        );
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();

    // Add some smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
        });
    });

    // Add keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            if (e.key === '1') {
                dashboard.switchTab('dashboard');
            } else if (e.key === '2') {
                dashboard.switchTab('chat');
            } else if (e.key === '3') {
                dashboard.switchTab('agents');
            } else if (e.key === '4') {
                dashboard.switchTab('metrics');
            }
        }
    });

    // Log version
    console.log('%cAgentForge Dashboard v1.0', 'color: #4F46E5; font-size: 16px; font-weight: bold;');
    console.log('%cPowered by FastAPI + Chart.js + Bootstrap 5', 'color: #10B981; font-size: 12px;');
});
