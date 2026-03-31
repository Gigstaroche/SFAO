#!/usr/bin/env python3
"""
SFAO Startup Manager
Launches both the main SFAO API and the Database Studio interface
"""

import subprocess
import threading
import time
import sys
import os

def run_main_api():
    """Run the main SFAO API server on port 8000"""
    print("🚀 Starting SFAO Main API on http://localhost:8000")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ], cwd=os.path.join(os.path.dirname(__file__), "backend"))

def run_database_studio():
    """Run the Database Studio on port 8001"""
    print("📊 Starting SFAO Database Studio on http://localhost:8001")
    time.sleep(2)  # Give main API time to start
    subprocess.run([
        sys.executable, "db_studio.py"
    ], cwd=os.path.join(os.path.dirname(__file__), "backend"))

def main():
    """Main startup function"""
    print("=" * 60)
    print("🎯 SFAO - Smart Feedback Analyzer for Organization")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found!")
        sys.exit(1)
    
    print("📍 Backend directory:", os.path.abspath(backend_dir))
    print()
    
    try:
        # Start both servers in parallel
        print("🔄 Starting SFAO services...")
        
        # Create threads for both servers
        main_api_thread = threading.Thread(target=run_main_api, daemon=True)
        db_studio_thread = threading.Thread(target=run_database_studio, daemon=True)
        
        # Start threads
        main_api_thread.start()
        db_studio_thread.start()
        
        print("\n✅ Both services are starting...")
        print("📋 Available endpoints:")
        print("   • Main API: http://localhost:8000")
        print("   • API Docs: http://localhost:8000/docs")  
        print("   • Dashboard: http://localhost:8000/portal")
        print("   • Database Studio: http://localhost:8001")
        print("   • Analytics: http://localhost:8001/analytics")
        print("   • Query Interface: http://localhost:8001/query")
        print("\n💡 Press Ctrl+C to stop all services")
        print("-" * 60)
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down SFAO services...")
            print("✅ Services stopped successfully!")
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()