:: filepath: /Users/mehedeniucgheorghe/qrcode generator/start_server.bat
@echo off
cls

echo =======================================
echo   Starting QR Code Generator Server    
echo =======================================

:: Set the path to the virtual environment
set VENV_PATH=D:\PythonEnvironments\QrGeneratorServices

:: Check if virtual environment exists, create if not
if not exist "%VENV_PATH%" (
    echo Virtual environment not found. Creating one at %VENV_PATH%...
    python -m venv "%VENV_PATH%"
)

:: Activate virtual environment
echo Activating virtual environment...
call "%VENV_PATH%\Scripts\activate"

:: Change to the project directory
cd /d %~dp0

:: Install required packages
echo Installing required packages...
pip install -r requirements.txt

:: Start the server
echo Starting the server on http://0.0.0.0:3000
echo Press CTRL+C to stop the server
python server.py

:: Deactivate virtual environment when done (will only run if server is stopped)
call deactivate