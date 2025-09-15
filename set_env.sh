#!/bin/bash
# Set environment variables for push notifications
export VAPID_PRIVATE_KEY="9kwBheCLAcaF0wMzhasMQzktyTdHrEpB8zWjMmiwVYE"
export VAPID_PUBLIC_KEY="BI3XFj66F3ZiKJ566gXXl3KYZrvczjs3zvPxNGcp55ZjA9HVGflUdIU79BYObXxTVyy7b7bAhEwe4zFCQS8l2Nc"
export VAPID_EMAIL="test@example.com"

echo "Environment variables set for push notifications"
echo "You can now run: python3 manage.py runserver"