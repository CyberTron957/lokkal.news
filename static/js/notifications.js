// Push Notifications Manager

class NotificationManager {
    constructor() {
        this.vapidPublicKey = 'BI3XFj66F3ZiKJ566gXXl3KYZrvczjs3zvPxNGcp55ZjA9HVGflUdIU79BYObXxTVyy7b7bAhEwe4zFCQS8l2Nc';
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.registration = null;
    }

    async init() {
        if (!this.isSupported) {
            console.log('Push notifications not supported');
            return false;
        }

        try {
            // Register service worker
            this.registration = await navigator.serviceWorker.register('/static/sw.js');
            console.log('Service Worker registered');
            return true;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            return false;
        }
    }

    async requestPermission() {
        if (!this.isSupported) return false;

        const permission = await Notification.requestPermission();
        return permission === 'granted';
    }

    async subscribe(areaName) {
        if (!this.registration) {
            await this.init();
        }

        try {
            const subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            // Send subscription to server
            const response = await fetch('/api/notifications/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    area_name: areaName,
                    subscription: subscription.toJSON()
                })
            });

            const result = await response.json();
            if (result.success) {
                console.log('Successfully subscribed to notifications');
                this.setSubscriptionStatus(areaName, true);
                return true;
            } else {
                console.error('Failed to subscribe:', result.error);
                return false;
            }
        } catch (error) {
            console.error('Error subscribing to notifications:', error);
            return false;
        }
    }

    async unsubscribe(areaName) {
        if (!this.registration) return false;

        try {
            const subscription = await this.registration.pushManager.getSubscription();
            if (subscription) {
                await subscription.unsubscribe();

                // Notify server
                await fetch('/api/notifications/unsubscribe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        area_name: areaName,
                        endpoint: subscription.endpoint
                    })
                });
            }

            this.setSubscriptionStatus(areaName, false);
            console.log('Successfully unsubscribed from notifications');
            return true;
        } catch (error) {
            console.error('Error unsubscribing from notifications:', error);
            return false;
        }
    }

    async isSubscribed(areaName) {
        if (!this.registration) return false;

        try {
            const subscription = await this.registration.pushManager.getSubscription();
            const localStatus = this.getSubscriptionStatus(areaName);
            return subscription && localStatus;
        } catch (error) {
            return false;
        }
    }

    setSubscriptionStatus(areaName, status) {
        localStorage.setItem(`notifications_${areaName}`, status.toString());
    }

    getSubscriptionStatus(areaName) {
        return localStorage.getItem(`notifications_${areaName}`) === 'true';
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    showNotificationPopup(areaName) {
        // Check if user has already been asked or is subscribed
        const hasBeenAsked = localStorage.getItem(`notification_asked_${areaName}`);
        const isSubscribed = this.getSubscriptionStatus(areaName);

        if (hasBeenAsked || isSubscribed || !this.isSupported) {
            return;
        }

        // Create popup HTML
        const popup = document.createElement('div');
        popup.className = 'notification-popup';
        popup.innerHTML = `
            <div class="notification-popup-content">
                <div class="notification-popup-header">
                    <h3>Stay Updated!</h3>
                    <button class="notification-popup-close">&times;</button>
                </div>
                <div class="notification-popup-body">
                    <p>Get notified about the latest news from <strong>${areaName.charAt(0).toUpperCase() + areaName.slice(1)}</strong></p>
                    <div class="notification-popup-buttons">
                        <button class="btn-primary" id="allow-notifications">Yes, notify me</button>
                        <button class="btn-secondary" id="deny-notifications">No thanks</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(popup);

        // Add event listeners
        const allowBtn = popup.querySelector('#allow-notifications');
        const denyBtn = popup.querySelector('#deny-notifications');
        const closeBtn = popup.querySelector('.notification-popup-close');

        const closePopup = () => {
            popup.remove();
            localStorage.setItem(`notification_asked_${areaName}`, 'true');
        };

        allowBtn.addEventListener('click', async () => {
            const hasPermission = await this.requestPermission();
            if (hasPermission) {
                const success = await this.subscribe(areaName);
                if (success) {
                    this.showToast('Notifications enabled! You\'ll be notified of new articles.', 'success');
                } else {
                    this.showToast('Failed to enable notifications. Please try again.', 'error');
                }
            } else {
                this.showToast('Notification permission denied.', 'error');
            }
            closePopup();
        });

        denyBtn.addEventListener('click', closePopup);
        closeBtn.addEventListener('click', closePopup);

        // Auto-show popup after a short delay
        setTimeout(() => {
            popup.classList.add('show');
        }, 2000);
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize notification manager
const notificationManager = new NotificationManager();

// Export for global use immediately
window.notificationManager = notificationManager;

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    notificationManager.init();
});