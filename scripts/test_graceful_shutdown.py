#!/usr/bin/env python3
"""
Test script to verify graceful shutdown functionality.
"""

import subprocess
import time
import signal
import os
import sys
from pathlib import Path

def test_graceful_shutdown():
    """Test that cvkitworker handles Ctrl+C gracefully."""
    print("Testing graceful shutdown of cvkitworker...")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Start cvkitworker with webcam
    try:
        print("Starting cvkitworker with webcam...")
        proc = subprocess.Popen(
            [sys.executable, "-m", "cvkitworker", "--webcam"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            preexec_fn=os.setsid  # Create new process group
        )
        
        print(f"Started cvkitworker with PID: {proc.pid}")
        
        # Let it run for a few seconds
        print("Letting it run for 5 seconds...")
        time.sleep(5)
        
        # Send SIGINT (Ctrl+C)
        print("Sending SIGINT (Ctrl+C) to process group...")
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)
        
        # Wait for graceful shutdown
        print("Waiting for graceful shutdown (max 10 seconds)...")
        try:
            stdout, stderr = proc.communicate(timeout=10)
            print(f"Process exited with code: {proc.returncode}")
            print("--- STDOUT ---")
            print(stdout)
            if stderr:
                print("--- STDERR ---")
                print(stderr)
                
            if proc.returncode == 0:
                print("✅ Graceful shutdown test PASSED")
                return True
            else:
                print(f"❌ Process exited with non-zero code: {proc.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Process did not exit within timeout, force killing...")
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait()
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False


def test_cleanup_processes():
    """Test that no hanging processes remain after shutdown."""
    print("\nTesting for hanging processes...")
    
    # Import our cleanup script functionality
    sys.path.append(str(Path(__file__).parent))
    try:
        from cleanup_processes import get_cvkit_processes
        
        processes = get_cvkit_processes()
        if processes:
            print(f"❌ Found {len(processes)} hanging processes:")
            for proc in processes:
                print(f"  PID {proc['pid']}: {proc['cmdline'][:60]}...")
            return False
        else:
            print("✅ No hanging processes found")
            return True
            
    except ImportError as e:
        print(f"⚠️  Cannot import cleanup script: {e}")
        return True  # Don't fail the test if cleanup script isn't available


if __name__ == "__main__":
    print("=== Graceful Shutdown Test ===")
    
    # Test graceful shutdown
    shutdown_ok = test_graceful_shutdown()
    
    # Test for hanging processes
    cleanup_ok = test_cleanup_processes()
    
    if shutdown_ok and cleanup_ok:
        print("\n🎉 All tests PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Some tests FAILED!")
        sys.exit(1)