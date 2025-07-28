/**
 * WebSocket client for real-time notifications
 */
class AutoFormsWebSocket {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnected = false;
        this.userId = null;
        this.token = null;
        this.subscribedRooms = new Set();
        this.messageHandlers = new Map();
        this.connectionHandlers = [];
        
        // Get user info from page
        this.initializeUserInfo();
    }
    
    initializeUserInfo() {
        // Try to get user info from various sources
        const userDataElement = document.getElementById('user-data');
        if (userDataElement) {
            const userData = JSON.parse(userDataElement.textContent);
            this.userId = userData.id;
            this.token = userData.token;
        }
        
        // Try to get from cookies
        if (!this.token) {
            this.token = this.getCookie('token');
        }
    }
    
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    
    connect(userId = null, roomId = null) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }
        
        if (userId) this.userId = userId;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        // Build query parameters
        const params = new URLSearchParams();
        if (this.userId) params.append('user_id', this.userId);
        if (roomId) params.append('room_id', roomId);
        if (this.token) params.append('token', this.token);
        
        const fullUrl = `${wsUrl}?${params.toString()}`;
        
        console.log('🔌 Connecting to WebSocket:', fullUrl);
        
        this.ws = new WebSocket(fullUrl);
        
        this.ws.onopen = (event) => {
            console.log('✅ WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            // Notify connection handlers
            this.connectionHandlers.forEach(handler => handler(true));
            
            // Resubscribe to rooms
            this.subscribedRooms.forEach(roomId => {
                this.subscribeToRoom(roomId);
            });
            
            // Start ping/pong
            this.startPingPong();
        };
        
        this.ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('🔌 WebSocket disconnected:', event.code, event.reason);
            this.isConnected = false;
            
            // Notify connection handlers
            this.connectionHandlers.forEach(handler => handler(false));
            
            // Attempt to reconnect
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                setTimeout(() => {
                    this.reconnectAttempts++;
                    console.log(`🔄 Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                    this.connect();
                }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
    }
    
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    }
    
    subscribeToRoom(roomId) {
        this.subscribedRooms.add(roomId);
        this.send({
            type: 'subscribe_room',
            room_id: roomId
        });
    }
    
    unsubscribeFromRoom(roomId) {
        this.subscribedRooms.delete(roomId);
        this.send({
            type: 'unsubscribe_room',
            room_id: roomId
        });
    }
    
    handleMessage(message) {
        console.log('📨 WebSocket message:', message);
        
        // Handle built-in message types
        switch (message.type) {
            case 'pong':
                // Handle pong response
                break;
                
            case 'room_subscribed':
                console.log(`✅ Subscribed to room: ${message.room_id}`);
                break;
                
            case 'room_unsubscribed':
                console.log(`❌ Unsubscribed from room: ${message.room_id}`);
                break;
                
            case 'form_generated':
                this.handleFormGenerated(message);
                break;
                
            case 'form_updated':
                this.handleFormUpdated(message);
                break;
                
            case 'form_submitted':
                this.handleFormSubmitted(message);
                break;
                
            case 'generation_progress':
                this.handleGenerationProgress(message);
                break;
                
            case 'chat_message':
                this.handleChatMessage(message);
                break;
                
            case 'error':
                this.handleError(message);
                break;
                
            case 'success':
                this.handleSuccess(message);
                break;
                
            case 'system_message':
                this.handleSystemMessage(message);
                break;
        }
        
        // Call registered handlers
        const handlers = this.messageHandlers.get(message.type) || [];
        handlers.forEach(handler => handler(message));
    }
    
    handleFormGenerated(message) {
        // Show notification
        this.showNotification('Form Generated', message.message, 'success');
        
        // Update UI if on dashboard
        if (window.location.pathname === '/dashboard' || window.location.pathname === '/home') {
            this.refreshDashboard();
        }
    }
    
    handleFormUpdated(message) {
        this.showNotification('Form Updated', message.message, 'success');
        
        // Update form if currently viewing it
        if (window.location.pathname.includes(`/forms/${message.form_id}`)) {
            this.refreshCurrentForm();
        }
    }
    
    handleFormSubmitted(message) {
        this.showNotification('New Submission', message.message, 'info');
        
        // Update form statistics
        this.updateFormStats(message.form_id, message.data);
    }
    
    handleGenerationProgress(message) {
        // Update progress bar or indicator
        this.updateGenerationProgress(message.data);
    }
    
    handleChatMessage(message) {
        // Update chat interface
        this.updateChatInterface(message.form_id, message.data);
    }
    
    handleError(message) {
        this.showNotification('Error', message.message, 'error');
    }
    
    handleSuccess(message) {
        this.showNotification('Success', message.message, 'success');
    }
    
    handleSystemMessage(message) {
        console.log('📢 System message:', message.message);
    }
    
    showNotification(title, message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <strong>${title}</strong>
                <p>${message}</p>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add to notification container
        let container = document.getElementById('notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notifications-container';
            container.className = 'notifications-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    refreshDashboard() {
        // Refresh dashboard content
        if (window.htmx) {
            window.htmx.trigger('#dashboard-content', 'refresh');
        } else {
            window.location.reload();
        }
    }
    
    refreshCurrentForm() {
        // Refresh current form content
        if (window.htmx) {
            window.htmx.trigger('#form-content', 'refresh');
        }
    }
    
    updateFormStats(formId, data) {
        // Update form statistics display
        const statsElement = document.getElementById(`form-stats-${formId}`);
        if (statsElement) {
            // Update submission count, etc.
            const submissionCount = statsElement.querySelector('.submission-count');
            if (submissionCount) {
                const current = parseInt(submissionCount.textContent) || 0;
                submissionCount.textContent = current + 1;
            }
        }
    }
    
    updateGenerationProgress(data) {
        // Update progress indicators
        const progressBar = document.getElementById('generation-progress');
        if (progressBar) {
            progressBar.style.width = `${data.percentage}%`;
            progressBar.setAttribute('aria-valuenow', data.percentage);
        }
        
        const progressText = document.getElementById('generation-progress-text');
        if (progressText) {
            progressText.textContent = data.message || `${data.percentage}%`;
        }
    }
    
    updateChatInterface(formId, data) {
        // Update chat interface with new message
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            const messageElement = document.createElement('div');
            messageElement.className = 'chat-message';
            messageElement.innerHTML = `
                <div class="message-content">
                    <strong>${data.sender}:</strong>
                    <p>${data.message}</p>
                    <small>${new Date(data.timestamp).toLocaleTimeString()}</small>
                </div>
            `;
            chatContainer.appendChild(messageElement);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    startPingPong() {
        setInterval(() => {
            if (this.isConnected) {
                this.send({
                    type: 'ping',
                    timestamp: Date.now()
                });
            }
        }, 30000); // Ping every 30 seconds
    }
    
    // Event handlers
    onMessage(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }
    
    onConnection(handler) {
        this.connectionHandlers.push(handler);
    }
    
    requestStats() {
        this.send({ type: 'request_stats' });
    }
}

// Initialize WebSocket client
const wsClient = new AutoFormsWebSocket();

// Auto-connect when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Connect to WebSocket
    wsClient.connect();
    
    // Add connection indicator
    const indicator = document.createElement('div');
    indicator.id = 'ws-connection-indicator';
    indicator.className = 'ws-indicator disconnected';
    indicator.innerHTML = '🔴 Disconnected';
    document.body.appendChild(indicator);
    
    // Update connection indicator
    wsClient.onConnection(function(connected) {
        if (connected) {
            indicator.className = 'ws-indicator connected';
            indicator.innerHTML = '🟢 Connected';
        } else {
            indicator.className = 'ws-indicator disconnected';
            indicator.innerHTML = '🔴 Disconnected';
        }
    });
});

// Export for global use
window.wsClient = wsClient;