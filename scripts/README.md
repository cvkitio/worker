# Scripts

This directory contains utility scripts for managing the cvkitworker system.

## cleanup_processes.py / cleanup.sh

A utility script to find and kill hanging Python processes that may have been spawned by cvkitworker.

### Usage

Using the bash wrapper (recommended):
```bash
./scripts/cleanup.sh [options]
```

Or directly with Python:
```bash
source .venv/bin/activate
python scripts/cleanup_processes.py [options]
```

### Options

- `--dry-run`: Show processes without killing them
- `--force`: Force kill processes using SIGKILL instead of SIGTERM
- `--all`: Kill all found processes without prompting
- `--min-runtime N`: Only show/kill processes running longer than N seconds

### Examples

```bash
# Show hanging processes without killing them
./scripts/cleanup.sh --dry-run

# Kill all hanging processes without prompting
./scripts/cleanup.sh --all

# Force kill processes running longer than 60 seconds
./scripts/cleanup.sh --force --min-runtime 60

# Interactive mode (default)
./scripts/cleanup.sh
```

### What it does

The script identifies Python processes by looking for:
- Processes with 'cvkitworker' in the command line
- Processes running frame_worker or detect_worker modules
- Processes running __main__.py (likely cvkitworker entry point)

It then displays:
- Process ID (PID)
- Parent Process ID (PPID)
- Runtime duration
- Command line

In interactive mode, you can:
- Enter specific PIDs to kill (comma-separated)
- Type 'all' to kill all processes
- Type 'q' to quit without killing anything