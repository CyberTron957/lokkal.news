// Client-side notification helper for area pages
// Registers service worker, prompts user, subscribes to push, and posts subscription to server

const VAPID_PUBLIC_KEY = window.VAPID_PUBLIC_KEY || '{{ VAPID_PUBLIC_KEY }}'; // will be set in templates or window

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      const reg = await navigator.serviceWorker.register('/static/news_app/js/sw.js');
      console.log('Service worker registered', reg);
      return reg;
    } catch (err) {
      console.error('Service worker registration failed', err);
    }
  }
}

async function askToSubscribe(areaName, label) {
  console.log('askToSubscribe called for area:', areaName, 'VAPID_PUBLIC_KEY=', VAPID_PUBLIC_KEY);
  if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('Push notifications are not supported in this browser.');
    return;
  }

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    console.log('Notification permission denied');
    return;
  }

  const reg = await registerServiceWorker();
  console.log('service worker registration result:', reg);
    const existing = await reg.pushManager.getSubscription();
  console.log('existing subscription:', existing);
  if (existing) {
    // send to server to ensure saved
      await fetch('/api/subscribe/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ area: areaName, subscription: existing.toJSON(), label: label }),
      });
    return existing;
  }

  const convertedVapidKey = urlBase64ToUint8Array(VAPID_PUBLIC_KEY.replace(/\n/g, ''));
    try {
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: convertedVapidKey,
    });
      console.log('new subscription object:', sub);

    await fetch('/api/subscribe/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ area: areaName, subscription: sub.toJSON(), label: label }),
    });

    return sub;
  } catch (err) {
    console.error('Failed to subscribe', err);
  }
}

async function unsubscribe(areaName, endpoint) {
  const reg = await navigator.serviceWorker.getRegistration();
  if (!reg) return;
  const sub = await reg.pushManager.getSubscription();
    if (sub) {
    await fetch('/api/unsubscribe/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ area: areaName, endpoint: endpoint }),
    });
    try { await sub.unsubscribe(); } catch(e) { console.warn(e); }
  }
}

// Helper to get CSRF token from cookies (Django default)
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

// Expose for templates
window.NewsNotifications = {
  registerServiceWorker,
  askToSubscribe,
  unsubscribe,
};
