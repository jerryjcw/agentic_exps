#!/usr/bin/env python3
"""
Complete example that starts the server and runs the client.
This script demonstrates the full workflow.
"""

import subprocess
import time
import sys
from pathlib import Path

def start_server():
    """Start the FastAPI server."""
    print("🚀 Starting FastAPI server...")
    
    # Change to API directory
    api_dir = Path(__file__).parent
    
    # Start the server process
    try:
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=api_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Check if server is still running
        if process.poll() is None:
            print("✅ Server started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def check_server_health():
    """Check if the server is responding."""
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server health check passed")
            return True
        else:
            print(f"⚠️  Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server health check error: {e}")
        return False

def run_client():
    """Run the example client."""
    print("\n" + "="*60)
    print("🎯 Running example client...")
    print("="*60)
    
    api_dir = Path(__file__).parent
    
    try:
        result = subprocess.run(
            [sys.executable, "example_client.py"],
            cwd=api_dir,
            capture_output=False,  # Let output go to console
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Client completed successfully")
            return True
        else:
            print(f"❌ Client failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running client: {e}")
        return False

def main():
    """Main function to run the complete example."""
    print("🎯 Flexible Agent API Complete Example")
    print("=" * 60)
    print("This script will:")
    print("1. Start the FastAPI server")
    print("2. Run the example client")
    print("3. Clean up the server process")
    print("-" * 60)
    
    server_process = None
    
    try:
        # Start server
        server_process = start_server()
        if not server_process:
            return 1
        
        # Health check
        if not check_server_health():
            print("❌ Server health check failed")
            return 1
        
        # Run client
        client_success = run_client()
        
        if client_success:
            print("\n🎉 Example completed successfully!")
            print("📁 Check the following files for results:")
            print("   - api/example_response.json")
            print("   - api/execution_results.json")
            print("   - output/ directory (if workflow generated files)")
        else:
            print("\n❌ Example failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        
    finally:
        # Clean up server process
        if server_process and server_process.poll() is None:
            print("🧹 Stopping server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                print("✅ Server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Server didn't stop gracefully, killing...")
                server_process.kill()
                server_process.wait()
                print("✅ Server killed")
    
    return 0

if __name__ == "__main__":
    exit(main())