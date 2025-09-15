# Push Notifications Setup Guide

This guide will help you set up push notifications for your Dynamic AI Websites project.

## Features

- **Area-specific notifications**: Users can subscribe to notifications for specific areas
- **Automatic popup**: When users visit an area page, they'll see a popup asking if they want notifications
- **Smart persistence**: The system remembers user preferences and won't show the popup again
- **Automatic notifications**: When new articles are posted, all subscribers get notified
- **Cross-browser support**: Works on Chrome, Firefox, Safari, and Edge

## Quick Setup

1. **Run the setup script**:
   ```bash
   python setup_notifications.py
   ```

2. **Set environment variables** (add to your `.env` file or system environment):
   ```bash
   VAPID_PRIVATE_KEY=your_private_key_here
   VAPID_PUBLIC_KEY=your_public_key_here
   ```

3. **Update the JavaScript configuration**:
   - Open `static/js/notifications.js`
   - Replace `YOUR_VAPID_PUBLIC_KEY` with your actual public key

4. **Update email in views.py**:
   - Open `news_app/views.py`
   - Find `vapid_claims = {"sub": "mailto:your-email@example.com"}`
   - Replace with your actual email address

5. **Add notification icons** (optional but recommended):
   - Add `icon-192x192.png` to `static/images/`
   - Add `badge-72x72.png` to `static/images/`

## Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Install Dependencies

```bash
pip install pywebpush
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Generate VAPID Keys

```bash
python manage.py generate_vapid_keys
```

### 4. Configure Environment Variables

Add the generated keys to your environment:

```bash
export VAPID_PRIVATE_KEY="your_private_key"
export VAPID_PUBLIC_KEY="your_public_key"
```

### 5. Update JavaScript Configuration

In `static/js/notifications.js`, update:

```javascript
this.vapidPublicKey = 'YOUR_ACTUAL_PUBLIC_KEY_HERE';
```

## How It Works

### User Experience

1. **First Visit**: When a user visits an area page for the first time, they see a popup asking if they want notifications
2. **Permission Request**: If they click "Yes", the browser asks for notification permission
3. **Subscription**: Once granted, the user is subscribed to notifications for that area
4. **Notifications**: When new articles are posted in that area, they receive a push notification
5. **Click Action**: Clicking the notification opens the article

### Technical Flow

1. **Frontend**: JavaScript handles permission requests and subscription management
2. **Service Worker**: Handles incoming push messages and displays notifications
3. **Backend**: Django stores subscriptions and sends notifications when articles are created
4. **VAPID**: Ensures secure communication between your server and push services

## API Endpoints

- `POST /api/notifications/subscribe/` - Subscribe to notifications for an area
- `POST /api/notifications/unsubscribe/` - Unsubscribe from notifications

## Database Models

### NotificationSubscription

- `area`: ForeignKey to Area model
- `endpoint`: Push service endpoint URL
- `p256dh_key`: Encryption key for push messages
- `auth_key`: Authentication key for push messages
- `user_agent`: Browser information (optional)
- `created_at`: Subscription creation time
- `is_active`: Whether the subscription is active

## Customization

### Notification Content

Edit the `send_push_notifications` function in `views.py` to customize:

- Notification title and body
- Icon and badge images
- Action buttons
- Click behavior

### Popup Appearance

Modify `static/css/notifications.css` to change:

- Popup styling
- Button colors
- Animation effects
- Mobile responsiveness

### Timing

Adjust when the popup appears by modifying the timeout in `news.html`:

```javascript
setTimeout(() => {
    window.notificationManager.showNotificationPopup('{{ area.name }}');
}, 1500); // Change this value (in milliseconds)
```

## Troubleshooting

### Common Issues

1. **Notifications not working**:
   - Check browser console for errors
   - Verify VAPID keys are set correctly
   - Ensure HTTPS is enabled (required for push notifications)

2. **Popup not showing**:
   - Check if user has already been asked (stored in localStorage)
   - Verify JavaScript is loading correctly
   - Check browser compatibility

3. **Service Worker errors**:
   - Ensure `static/sw.js` is accessible
   - Check for JavaScript syntax errors
   - Verify service worker registration

### Browser Requirements

- **Chrome**: Version 42+
- **Firefox**: Version 44+
- **Safari**: Version 16+ (macOS 13+, iOS 16.4+)
- **Edge**: Version 17+

### HTTPS Requirement

Push notifications require HTTPS in production. For local development, `localhost` is allowed.

## Security Considerations

- VAPID keys should be kept secure and not exposed in client-side code
- Only the public key should be used in JavaScript
- Private key should be stored as an environment variable
- Regularly rotate VAPID keys for enhanced security

## Performance Notes

- Notifications are sent asynchronously to avoid blocking article creation
- Failed subscriptions are automatically deactivated
- The system handles rate limiting and retry logic
- Subscriptions are cleaned up when they become invalid

## Testing

### Method 1: Using the Test Page (Recommended for Development)

1. Set environment variables:
   ```bash
   source set_env.sh
   ```

2. Start the Django server:
   ```bash
   python3 manage.py runserver
   ```

3. Visit the test page: `http://localhost:8000/test-notifications/`

4. Follow the instructions on the test page to:
   - Subscribe to notifications
   - Send a test notification
   - Verify you receive the notification

### Method 2: Real-world Testing

1. Visit an area page and subscribe to notifications
2. Create a new post for that area (this will trigger article generation)
3. Check that you receive a notification
4. Click the notification to verify it opens the correct article

### Method 3: Manual API Testing

You can also test the API endpoints directly:

```bash
# Subscribe to notifications (requires a valid push subscription)
curl -X POST http://localhost:8000/api/notifications/subscribe/ \
  -H "Content-Type: application/json" \
  -d '{"area_name": "test", "subscription": {...}}'

# Send test notification (debug mode only)
curl http://localhost:8000/api/test-notification/?area=test
```

## Support

If you encounter issues:

1. Check the Django logs for error messages
2. Verify browser console for JavaScript errors
3. Test with different browsers
4. Ensure all environment variables are set correctly