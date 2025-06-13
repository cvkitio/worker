#!/usr/bin/env python3
"""
Cleanup script to find and kill hanging Python processes from cvkitworker.

This script identifies Python processes that may have been spawned by cvkitworker
and provides options to kill them safely.
"""

import os
import sys
import signal
import psutil
import argparse
from datetime import datetime, timezone
import subprocess


def get_cvkit_processes():
    """Find all Python processes that might be related to cvkitworker."""
    cvkit_processes = []
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'ppid']):
        try:
            # Skip if not a Python process
            if 'python' not in proc.info['name'].lower():
                continue
                
            # Skip current process
            if proc.info['pid'] == current_pid:
                continue
                
            cmdline = proc.info['cmdline']
            if cmdline:
                # Join command line arguments
                cmd_str = ' '.join(cmdline).lower()
                
                # Check for cvkitworker related processes
                if any(keyword in cmd_str for keyword in ['cvkitworker', 'frame_worker', 'detect_worker', '__main__.py', ' multiprocessing.spawn']):
                    # Get process creation time
                    create_time = datetime.fromtimestamp(proc.info['create_time'], tz=timezone.utc)
                    runtime = datetime.now(timezone.utc) - create_time
                    
                    cvkit_processes.append({
                        'pid': proc.info['pid'],
                        'ppid': proc.info['ppid'],
                        'cmdline': ' '.join(cmdline),
                        'runtime': runtime,
                        'create_time': create_time
                    })
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    return cvkit_processes


def format_runtime(runtime):
    """Format runtime duration to human-readable string."""
    total_seconds = int(runtime.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def kill_process(pid, force=False):
    """Kill a process by PID."""
    try:
        proc = psutil.Process(pid)
        if force:
            proc.kill()  # SIGKILL
            print(f"Force killed process {pid}")
        else:
            proc.terminate()  # SIGTERM
            print(f"Terminated process {pid}")
        return True
    except psutil.NoSuchProcess:
        print(f"Process {pid} no longer exists")
        return False
    except psutil.AccessDenied:
        print(f"Access denied to kill process {pid}")
        return False
    except Exception as e:
        print(f"Error killing process {pid}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Cleanup hanging cvkitworker processes')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Show processes without killing them')
    parser.add_argument('--force', action='store_true',
                        help='Force kill processes (SIGKILL instead of SIGTERM)')
    parser.add_argument('--all', action='store_true',
                        help='Kill all found processes without prompting')
    parser.add_argument('--min-runtime', type=int, default=0,
                        help='Only show/kill processes running longer than N seconds')
    
    args = parser.parse_args()
    
    # Find cvkitworker related processes
    processes = get_cvkit_processes()
    
    # Filter by minimum runtime if specified
    if args.min_runtime > 0:
        processes = [p for p in processes if p['runtime'].total_seconds() >= args.min_runtime]
    
    if not processes:
        print("No hanging cvkitworker processes found.")
        return 0
    
    # Display found processes
    print(f"\nFound {len(processes)} cvkitworker related process(es):\n")
    print(f"{'PID':<8} {'PPID':<8} {'Runtime':<12} {'Command'}")
    print("-" * 80)
    
    for proc in processes:
        runtime_str = format_runtime(proc['runtime'])
        # Truncate command if too long
        cmd = proc['cmdline']
        if len(cmd) > 50:
            cmd = cmd[:47] + "..."
        print(f"{proc['pid']:<8} {proc['ppid']:<8} {runtime_str:<12} {cmd}")
    
    print()
    
    # If dry run, exit here
    if args.dry_run:
        print("Dry run mode - no processes killed.")
        return 0
    
    # Kill processes
    if args.all:
        # Kill all without prompting
        print(f"Killing all {len(processes)} processes...")
        killed = 0
        for proc in processes:
            if kill_process(proc['pid'], force=args.force):
                killed += 1
        print(f"\nKilled {killed} process(es).")
    else:
        # Interactive mode
        print("Enter process PIDs to kill (comma-separated), 'all' to kill all, or 'q' to quit:")
        response = input("> ").strip().lower()
        
        if response == 'q':
            print("Cancelled.")
            return 0
        elif response == 'all':
            killed = 0
            for proc in processes:
                if kill_process(proc['pid'], force=args.force):
                    killed += 1
            print(f"\nKilled {killed} process(es).")
        else:
            # Parse individual PIDs
            try:
                pids = [int(pid.strip()) for pid in response.split(',') if pid.strip()]
                valid_pids = {p['pid'] for p in processes}
                
                killed = 0
                for pid in pids:
                    if pid in valid_pids:
                        if kill_process(pid, force=args.force):
                            killed += 1
                    else:
                        print(f"PID {pid} not in the list of cvkitworker processes.")
                
                print(f"\nKilled {killed} process(es).")
            except ValueError:
                print("Invalid input. Please enter comma-separated PIDs.")
                return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())