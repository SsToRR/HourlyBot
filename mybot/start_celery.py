#!/usr/bin/env python3
"""
Start Celery worker and beat scheduler for the Teams Bot
"""

import os
import sys
import subprocess
import time
import signal
import threading

def start_celery_worker():
    """Start the Celery worker"""
    print("Starting Celery worker...")
    cmd = [
        sys.executable, "-m", "celery", "-A", "bot1", "worker",
        "--loglevel=info",
        "--concurrency=1"
    ]
    return subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

def start_celery_beat():
    """Start the Celery beat scheduler"""
    print("Starting Celery beat scheduler...")
    cmd = [
        sys.executable, "-m", "celery", "-A", "bot1", "beat",
        "--loglevel=info",
        "--scheduler=django_celery_beat.schedulers:DatabaseScheduler"
    ]
    return subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to start both Celery processes"""
    print("Starting Teams Bot Celery Services...")
    print("=" * 50)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bot1.settings')
    
    # Start processes
    worker_process = start_celery_worker()
    beat_process = start_celery_beat()
    
    print(f"Celery worker PID: {worker_process.pid}")
    print(f"Celery beat PID: {beat_process.pid}")
    print("\nBoth processes started. Press Ctrl+C to stop.")
    
    try:
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if worker_process.poll() is not None:
                print("Celery worker stopped unexpectedly!")
                break
                
            if beat_process.poll() is not None:
                print("Celery beat stopped unexpectedly!")
                break
                
    except KeyboardInterrupt:
        print("\nStopping Celery processes...")
        
        # Stop processes gracefully
        worker_process.terminate()
        beat_process.terminate()
        
        # Wait for processes to stop
        try:
            worker_process.wait(timeout=5)
            beat_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Forcing process termination...")
            worker_process.kill()
            beat_process.kill()
        
        print("Celery processes stopped.")

if __name__ == "__main__":
    main() 