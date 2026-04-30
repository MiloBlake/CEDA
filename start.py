#!/usr/bin/env python3
"""
Start script for Data Analysis Chatbot.
Installs dependencies and starts both backend and frontend servers.
"""

import os
import sys
import subprocess
import time
import platform

def print_ceda_logo():
    logo = """
    ****  ****  ***     *
    *     *     *  *   * *
    *     ***   *   * *   *
    *     *     *  *  * * *
    ****  ****  ***   *   *
    """
    print(logo)

def run_command(cmd, cwd=None, shell=False):
    """Run a command and return the process."""
    try:
        return subprocess.Popen(cmd, cwd=cwd, shell=shell)
    except Exception as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def install_backend_dependencies():
    """Install Python dependencies from requirements file."""
    print("\nChecking backend dependencies...")
    requirements_file = os.path.join(os.path.dirname(__file__), "project_dependencies", "dependencies-backend.txt")
    
    if not os.path.exists(requirements_file):
        print(f"Requirements file not found: {requirements_file}")
        sys.exit(1)
    
    # Check if dependencies are already installed
    cmd = [sys.executable, "-m", "pip", "check"]
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0:
        print("Backend dependencies already installed")
        return
    
    print("Installing backend dependencies...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    
    if result.returncode != 0:
        print("Failed to install backend dependencies")
        sys.exit(1)
    
    print("Backend dependencies installed")

def install_frontend_dependencies():
    """Install frontend dependencies using npm."""
    print("\nChecking frontend dependencies...")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    
    # Check if node_modules exists
    node_modules = os.path.join(frontend_dir, "node_modules")
    if os.path.exists(node_modules):
        print("Frontend dependencies already installed")
        return
    
    print("Installing frontend dependencies...")
    cmd = ["npm", "install"]
    result = subprocess.run(cmd, cwd=frontend_dir)
    
    if result.returncode != 0:
        print("Failed to install frontend dependencies")
        print("Make sure Node.js and npm are installed and accessible from your PATH")
        sys.exit(1)
    
    print("Frontend dependencies installed")

def start_backend():
    """Start the Flask backend server."""
    print("\nStarting backend server...")
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    
    # Set environment variables
    env = os.environ.copy()
    env["FLASK_APP"] = "app.py"
    env["FLASK_ENV"] = "development"
    env["LOG_LEVEL"] = "INFO"
    
    cmd = [sys.executable, "app.py"]
    process = run_command(cmd, cwd=backend_dir)
    print("Backend server started on http://localhost:5000")
    return process

def start_frontend():
    """Start the React frontend server."""
    print("\nStarting frontend server...")
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    
    # Set environment variable for backend API URL
    env = os.environ.copy()
    env["REACT_APP_API_URL"] = "http://localhost:5000"
    
    # Use npm start
    cmd = "npm start" if platform.system() == "Windows" else ["npm", "start"]
    shell = platform.system() == "Windows"
    
    process = run_command(cmd, cwd=frontend_dir, shell=shell)
    print("Frontend server started on http://localhost:3000")
    return process

def main():
    """Main entry point."""
    print_ceda_logo()
    print("=" * 50)
    
    root_dir = os.path.dirname(__file__)
    os.chdir(root_dir)
    
    # Install dependencies
    install_backend_dependencies()
    install_frontend_dependencies()
    
    print("\n" + "=" * 50)
    print("All dependencies installed!")
    print("=" * 50)
    
    # Start servers
    backend_process = start_backend()
    time.sleep(2)  # Give backend time to start
    frontend_process = start_frontend()
    
    print("\n" + "=" * 50)
    print("Services running:")
    print("   Backend:  http://localhost:5000")
    print("   Frontend: http://localhost:3000")
    print("=" * 50)
    print("\nPress Ctrl+C to stop all services...\n")
    
    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down services...")
        backend_process.terminate()
        frontend_process.terminate()
        
        # Wait for processes to terminate
        try:
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
            frontend_process.kill()
        
        print("Services stopped")
        sys.exit(0)

if __name__ == "__main__":
    main()