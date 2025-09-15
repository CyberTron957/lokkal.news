self.addEventListener('push', function(event) {
  let payload = {};
  try {
    payload = event.data.json();
  } catch (e) {
    payload = { title: 'New update', body: event.data ? event.data.text() : '' };
  }

  const title = payload.title || 'New article';
  const options = {
    body: payload.body || '',
    icon: payload.icon || '/static/admin/img/icon.png',
    data: payload.data || {},
    badge: payload.badge || '/static/admin/img/badge.png',
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data && event.notification.data.url;
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then( windowClients => {
      for (let i = 0; i < windowClients.length; i++) {
        const client = windowClients[i];
        if (client.url === url && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(url || '/');
    })
  );
});
