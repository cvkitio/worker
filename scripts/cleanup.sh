#!/bin/bash
# Wrapper script to run cleanup_processes.py with the correct environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Error: Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Please create a virtual environment first."
    exit 1
fi

# Activate virtual environment and run the cleanup script
source "$PROJECT_ROOT/.venv/bin/activate"
python "$SCRIPT_DIR/cleanup_processes.py" "$@"