/**
 * PWA Installation and Management
 */
class PWAInstaller {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.swRegistration = null;
        
        this.init();
    }
    
    async init() {
        // Check if already installed
        this.checkInstallationStatus();
        
        // Register service worker
        await this.registerServiceWorker();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Check for updates
        this.checkForUpdates();
        
        // Show install prompt if appropriate
        this.showInstallPrompt();
    }
    
    checkInstallationStatus() {
        // Check if running as PWA
        this.isInstalled = window.matchMedia('(display-mode: standalone)').matches ||
                          window.navigator.standalone === true;
        
        if (this.isInstalled) {
            console.log('📱 Running as PWA');
            document.body.classList.add('pwa-installed');
        }
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                this.swRegistration = await navigator.serviceWorker.register('/static/sw.js');
                console.log('✅ Service Worker registered:', this.swRegistration);
                
                // Handle service worker updates
                this.swRegistration.addEventListener('updatefound', () => {
                    this.handleServiceWorkerUpdate();
                });
                
            } catch (error) {
                console.error('❌ Service Worker registration failed:', error);
            }
        }
    }
    
    setupEventListeners() {
        // Before install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('📱 Before install prompt triggered');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });
        
        // App installed
        window.addEventListener('appinstalled', () => {
            console.log('📱 PWA installed');
            this.isInstalled = true;
            this.hideInstallButton();
            this.showInstallSuccess();
        });
        
        // Online/offline status
        window.addEventListener('online', () => {
            console.log('🌐 Back online');
            this.handleOnlineStatus(true);
        });
        
        window.addEventListener('offline', () => {
            console.log('📴 Gone offline');
            this.handleOnlineStatus(false);
        });
    }
    
    showInstallButton() {
        // Create install button if it doesn't exist
        let installButton = document.getElementById('pwa-install-button');
        if (!installButton) {
            installButton = document.createElement('button');
            installButton.id = 'pwa-install-button';
            installButton.className = 'pwa-install-btn';
            installButton.innerHTML = `
                <span class="install-icon">📱</span>
                <span>Install App</span>
            `;
            installButton.onclick = () => this.installPWA();
            
            // Add to page
            const targetContainer = document.querySelector('.pwa-install-container') || document.body;
            targetContainer.appendChild(installButton);
        }
        
        installButton.style.display = 'block';
    }
    
    hideInstallButton() {
        const installButton = document.getElementById('pwa-install-button');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }
    
    async installPWA() {
        if (!this.deferredPrompt) {
            console.log('No install prompt available');
            return;
        }
        
        try {
            // Show install prompt
            this.deferredPrompt.prompt();
            
            // Wait for user choice
            const { outcome } = await this.deferredPrompt.userChoice;
            console.log('📱 Install outcome:', outcome);
            
            if (outcome === 'accepted') {
                console.log('✅ User accepted install');
            } else {
                console.log('❌ User declined install');
            }
            
            // Clear the prompt
            this.deferredPrompt = null;
            this.hideInstallButton();
            
        } catch (error) {
            console.error('❌ Install error:', error);
        }
    }
    
    showInstallSuccess() {
        // Show success message
        const successMessage = document.createElement('div');
        successMessage.className = 'pwa-install-success';
        successMessage.innerHTML = `
            <div class="success-content">
                <span class="success-icon">✅</span>
                <span>App installed successfully!</span>
            </div>
        `;
        
        document.body.appendChild(successMessage);
        
        // Remove after 3 seconds
        setTimeout(() => {
            successMessage.remove();
        }, 3000);
    }
    
    handleServiceWorkerUpdate() {
        const installingWorker = this.swRegistration.installing;
        if (!installingWorker) return;
        
        installingWorker.addEventListener('statechange', () => {
            if (installingWorker.state === 'installed') {
                if (navigator.serviceWorker.controller) {
                    // New content available
                    this.showUpdateAvailable();
                } else {
                    // Content cached for first time
                    this.showCachedContent();
                }
            }
        });
    }
    
    showUpdateAvailable() {
        // Show update notification
        const updateNotification = document.createElement('div');
        updateNotification.className = 'pwa-update-notification';
        updateNotification.innerHTML = `
            <div class="update-content">
                <span class="update-icon">🔄</span>
                <span>New version available!</span>
                <button onclick="pwaInstaller.applyUpdate()">Update</button>
                <button onclick="this.parentElement.parentElement.remove()">Later</button>
            </div>
        `;
        
        document.body.appendChild(updateNotification);
    }
    
    showCachedContent() {
        console.log('📱 Content cached for offline use');
        
        // Show cached notification
        const cachedNotification = document.createElement('div');
        cachedNotification.className = 'pwa-cached-notification';
        cachedNotification.innerHTML = `
            <div class="cached-content">
                <span class="cached-icon">💾</span>
                <span>App ready for offline use!</span>
            </div>
        `;
        
        document.body.appendChild(cachedNotification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            cachedNotification.remove();
        }, 5000);
    }
    
    applyUpdate() {
        if (this.swRegistration && this.swRegistration.waiting) {
            this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
        }
        
        // Reload page
        window.location.reload();
    }
    
    handleOnlineStatus(online) {
        const statusIndicator = document.getElementById('network-status');
        if (statusIndicator) {
            statusIndicator.className = `network-status ${online ? 'online' : 'offline'}`;
            statusIndicator.textContent = online ? '🌐 Online' : '📴 Offline';
        }
        
        // Sync data when back online
        if (online && this.swRegistration) {
            this.swRegistration.sync.register('form-submission');
            this.swRegistration.sync.register('form-generation');
        }
    }
    
    checkForUpdates() {
        if (this.swRegistration) {
            this.swRegistration.update();
        }
    }
    
    // Public methods
    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            console.log('📱 Notification permission:', permission);
            return permission === 'granted';
        }
        return false;
    }
    
    async subscribeToPushNotifications() {
        if (!this.swRegistration) return null;
        
        try {
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(
                    'YOUR_VAPID_PUBLIC_KEY_HERE' // Replace with your VAPID key
                )
            });
            
            console.log('📱 Push subscription:', subscription);
            return subscription;
        } catch (error) {
            console.error('❌ Push subscription failed:', error);
            return null;
        }
    }
    
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
    
    // Cache management
    async clearCache() {
        if (this.swRegistration) {
            this.swRegistration.postMessage({ type: 'CACHE_CLEAR' });
        }
    }
    
    async getCacheStats() {
        if (!this.swRegistration) return null;
        
        return new Promise((resolve) => {
            const messageChannel = new MessageChannel();
            messageChannel.port1.onmessage = (event) => {
                resolve(event.data);
            };
            
            this.swRegistration.postMessage(
                { type: 'CACHE_STATS' },
                [messageChannel.port2]
            );
        });
    }
}

// Initialize PWA installer
const pwaInstaller = new PWAInstaller();

// Export for global use
window.pwaInstaller = pwaInstaller;

// Add PWA styles
const pwaStyles = document.createElement('style');
pwaStyles.textContent = `
    .pwa-install-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 50px;
        padding: 12px 20px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        z-index: 1000;
        display: none;
        align-items: center;
        gap: 8px;
        transition: all 0.3s ease;
    }
    
    .pwa-install-btn:hover {
        background: #1d4ed8;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
    }
    
    .pwa-install-success,
    .pwa-update-notification,
    .pwa-cached-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        z-index: 1001;
        max-width: 300px;
    }
    
    .pwa-install-success {
        border-left: 4px solid #10b981;
    }
    
    .pwa-update-notification {
        border-left: 4px solid #f59e0b;
    }
    
    .pwa-cached-notification {
        border-left: 4px solid #3b82f6;
    }
    
    .success-content,
    .update-content,
    .cached-content {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
    }
    
    .update-content button {
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        cursor: pointer;
        margin-left: 8px;
    }
    
    .network-status {
        position: fixed;
        top: 10px;
        left: 10px;
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 4px;
        z-index: 1000;
    }
    
    .network-status.online {
        background: #dcfce7;
        color: #166534;
    }
    
    .network-status.offline {
        background: #fef2f2;
        color: #991b1b;
    }
    
    .pwa-installed .pwa-install-btn {
        display: none !important;
    }
    
    @media (max-width: 768px) {
        .pwa-install-btn {
            bottom: 10px;
            right: 10px;
            padding: 10px 16px;
        }
        
        .pwa-install-success,
        .pwa-update-notification,
        .pwa-cached-notification {
            top: 10px;
            right: 10px;
            left: 10px;
            max-width: none;
        }
    }
`;

document.head.appendChild(pwaStyles);

// Add network status indicator
const networkStatus = document.createElement('div');
networkStatus.id = 'network-status';
networkStatus.className = `network-status ${navigator.onLine ? 'online' : 'offline'}`;
networkStatus.textContent = navigator.onLine ? '🌐 Online' : '📴 Offline';
document.body.appendChild(networkStatus);