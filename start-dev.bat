@echo off
REM ========== AgentForge Deployment Helper for Windows ==========

echo.
echo 🚀 AgentForge Deployment Helper
echo ================================

REM Check Python version
echo.
echo Checking Python version...
python --version

REM Check dependencies
echo.
echo Checking dependencies...
pip list | findstr fastapi > nul
if errorlevel 1 (
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
) else (
    echo ✅ Dependencies already installed
)

REM Check for .env file
echo.
echo Checking environment configuration...
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env and add your API keys
    echo    Then run this script again
    pause
    exit /b 1
) else (
    echo ✅ .env file exists
)

REM Create storage directory
if not exist storage\chroma (
    mkdir storage\chroma
)

REM Start services
echo.
echo Starting services...

REM FastAPI
echo ⚡ Starting FastAPI...
start "" python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

REM Wait for services to start
timeout /t 3 /nobreak

echo.
echo ✅ All services running!
echo.
echo 📍 Frontend: http://localhost:8000
echo 📍 API Docs: http://localhost:8000/docs
echo 📍 API Health: http://localhost:8000/api/v1/health
echo.
echo Press Ctrl+C in any terminal to stop services
echo.
pause
