// Service Worker for Push Notifications

self.addEventListener('push', function(event) {
    if (event.data) {
        const data = event.data.json();
        
        const options = {
            body: data.body,
            icon: data.icon || '/static/icon-192x192.png',
            badge: data.badge || '/static/badge-72x72.png',
            data: data.data,
            actions: data.actions || [],
            requireInteraction: true,
            tag: 'news-notification'
        };

        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    if (event.action === 'view' || !event.action) {
        // Open the article URL
        const url = event.notification.data.url;
        event.waitUntil(
            clients.openWindow(url)
        );
    }
});

self.addEventListener('notificationclose', function(event) {
    // Handle notification close if needed
    console.log('Notification closed:', event.notification.tag);
});