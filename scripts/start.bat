@echo off
REM ============================================================
REM  📄 RFP/RFQ Analyzer — Local Startup Script
REM  Usage: Double-click or run from Command Prompt
REM ============================================================
setlocal enabledelayedexpansion

cd /d "%~dp0.."
set PROJECT_DIR=%CD%

echo ==========================================
echo  📄 RFP / RFQ Analyzer
echo ==========================================
echo.

REM --- Create virtual environment if missing ---
if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. Is Python installed?
        pause
        exit /b 1
    )
    echo   Done.
) else (
    echo [1/4] Virtual environment found.
)

REM --- Activate virtual environment ---
echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

REM --- Install dependencies ---
echo [3/4] Installing dependencies...
pip install -e . --quiet
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)
echo   Done.

REM --- Ensure .env exists ---
if not exist ".env" (
    echo.
    echo  ⚠️  No .env file found. Copying from .env.example...
    copy .env.example .env >nul
    echo  ⚠️  Edit .env to add your OPENAI_API_KEY before using the analyzer.
    echo.
)

REM --- Launch dashboard ---
echo [4/4] Launching RFP Analyzer...
echo.
echo Opening browser to http://localhost:8501
echo Press Ctrl+C in this window to stop.
echo.
start "" http://localhost:8501
streamlit run src/app.py

pause
