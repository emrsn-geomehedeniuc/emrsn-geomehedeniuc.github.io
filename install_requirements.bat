@echo off
cls

echo =======================================
echo   Installing QR Code Generator Requirements
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

:: Install required packages with binary preference to avoid build issues
echo Installing dependencies from requirements.txt...
pip install --prefer-binary -r requirements.txt

:: Check if installation succeeded
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️ Some dependencies failed to install. Trying alternative approach...
    
    :: Try installing problematic packages separately
    echo Installing fastapi and uvicorn...
    pip install fastapi==0.104.1 uvicorn==0.24.0
    
    echo Installing qrcode...
    pip install qrcode==7.4.2
    
    echo Installing pillow with binary preference...
    pip install --prefer-binary pillow==10.4.0
    
    echo Installing python-multipart...
    pip install python-multipart==0.0.6
    
    echo Installing pandas ecosystem...
    pip install --prefer-binary pandas==2.2.3 openpyxl==3.1.2 xlrd==2.0.1
)

:: Create static directory if it doesn't exist
if not exist static (
    echo Creating static directory...
    mkdir static
)

echo.
echo ✅ Requirements installed successfully!
echo.

:: Start the server automatically
cls
echo =======================================
echo   Starting QR Code Generator Server    
echo =======================================
echo.
echo Starting the server on http://0.0.0.0:3000
echo Press CTRL+C to stop the server
echo.

:: Run the server using the activated virtual environment
python server.py

:: This will only run if the server is stopped
call "%VENV_PATH%\Scripts\deactivate"
echo.
echo Starting the server on http://0.0.0.0:3000
echo Press CTRL+C to stop the server
echo.
python server.py

:: This will only run if the server is stopped
call venv\Scripts\deactivate.bat
goto :end

:end
echo.
echo You can start the server later by:
echo 1. Activating the virtual environment: call venv\Scripts\activate
echo 2. Running: python server.py
echo.
pause
