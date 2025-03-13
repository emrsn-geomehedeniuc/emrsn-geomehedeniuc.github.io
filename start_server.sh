#!/bin/bash

# Display banner
echo "======================================="
echo "  Starting QR Code Generator Server    "
echo "======================================="

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

# Start the server
echo "Starting the server on http://0.0.0.0:3000"
echo "Press CTRL+C to stop the server"
python server.py

# Deactivate virtual environment when done (will only run if server is stopped)
deactivate
