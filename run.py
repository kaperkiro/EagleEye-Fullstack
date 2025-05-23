#!/usr/bin/env python3
"""
Script to start both the backend (py) and frontend (React/Vite) with one command.
Usage:
    python run_servers.py
"""
import subprocess
import sys
import os


def main():
    root = os.path.dirname(__file__)
    backend_dir = os.path.join(root, "Backend-Code", "app")
    frontend_dir = os.path.join(root, "frontend-code", "react-frontend")

    # Start backend server
    backend_proc = subprocess.Popen([sys.executable, "main.py"], cwd=backend_dir)
    print(f"Started backend (Flask) with PID {backend_proc.pid}")

    # Start frontend server (Vite)
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"], cwd=frontend_dir, shell=True
    )
    print(f"Started frontend (Vite) with PID {frontend_proc.pid}")

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("Shutting down servers...")
        backend_proc.terminate()
        frontend_proc.terminate()


if __name__ == "__main__":
    main()
