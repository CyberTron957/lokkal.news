#!/usr/bin/env python3
"""
Setup script for push notifications
"""
import os
import sys
import subprocess

def run_command(command):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔔 Setting up Push Notifications for Dynamic AI Websites")
    print("=" * 60)
    
    # Check if pywebpush is installed
    print("1. Checking dependencies...")
    success, _, _ = run_command("python3 -c 'import pywebpush'")
    if not success:
        print("   Installing pywebpush...")
        success, _, error = run_command("pip install pywebpush ecdsa")
        if not success:
            print(f"   ❌ Failed to install dependencies: {error}")
            return
        print("   ✅ Dependencies installed successfully")
    else:
        print("   ✅ Dependencies already installed")
    
    # Run migrations
    print("\n2. Running database migrations...")
    success, output, error = run_command("python3 manage.py migrate")
    if success:
        print("   ✅ Migrations completed successfully")
    else:
        print(f"   ❌ Migration failed: {error}")
        return
    
    # Generate VAPID keys
    print("\n3. Generating VAPID keys...")
    success, output, error = run_command("python3 manage.py generate_vapid_keys")
    if success:
        print("   ✅ VAPID keys generated successfully")
        print("\n" + output)
    else:
        print(f"   ❌ Failed to generate VAPID keys: {error}")
        return
    
    # Create static directories
    print("\n4. Setting up static files...")
    os.makedirs("static/images", exist_ok=True)
    print("   ✅ Static directories created")
    
    print("\n🎉 Push notification setup completed!")
    print("\nNext steps:")
    print("1. Add the VAPID keys to your environment variables")
    print("2. Update the vapidPublicKey in static/js/notifications.js")
    print("3. Add notification icons to static/images/ (icon-192x192.png, badge-72x72.png)")
    print("4. Update the email in the vapid_claims in views.py")
    print("5. Restart your Django server")

if __name__ == "__main__":
    main()