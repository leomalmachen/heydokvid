#!/usr/bin/env python3

import subprocess
import time
import requests
import webbrowser
import os

def test_backend():
    """Test the backend locally"""
    print("🚀 Starting Video Meeting App locally...")
    
    # Change to backend directory
    os.chdir('backend')
    
    # Start the backend
    print("📦 Starting backend server...")
    process = subprocess.Popen(['python', 'main.py'])
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(3)
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:8000/health')
        if response.status_code == 200:
            print("✅ Backend is running!")
            print("🌐 Opening browser...")
            webbrowser.open('http://localhost:8000')
            print("📱 App is ready at: http://localhost:8000")
            print("🛑 Press Ctrl+C to stop the server")
            
            # Keep running
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
                process.terminate()
                print("✅ Server stopped")
        else:
            print("❌ Backend health check failed")
            process.terminate()
    except Exception as e:
        print(f"❌ Error testing backend: {e}")
        process.terminate()

if __name__ == "__main__":
    test_backend() 