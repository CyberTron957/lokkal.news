#!/bin/bash

echo "🚀 Starting Django server with push notifications..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your VAPID keys"
fi

# Load environment variables and start server
echo "📡 Loading environment variables..."
export $(cat .env | xargs)

echo "🔧 Running migrations..."
python3 manage.py migrate

echo "🌐 Starting Django development server..."
echo "📱 Test notifications at: http://localhost:8000/test-notifications/"
echo ""
python3 manage.py runserver