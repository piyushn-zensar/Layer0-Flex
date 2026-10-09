@echo off
rem Layer 0 one-time setup on Windows: Python environment, web build, demo data.
rem Needs Python 3.11+ and Node.js 20.9+. No OCR engine and no API key are needed for the demo.
setlocal
cd /d "%~dp0"
echo.
echo == Layer 0 setup ==

where node >nul 2>nul || (echo Node.js 20.9 or later is required: https://nodejs.org & exit /b 1)

set "PY="
py -3.12 --version >nul 2>nul && set "PY=py -3.12"
if not defined PY python --version >nul 2>nul && set "PY=python"
if not defined PY (echo Python 3.12 is required: https://www.python.org/downloads/ & exit /b 1)
%PY% -c "import sys; sys.exit(sys.version_info < (3, 11))" || (echo Python 3.11 or later is required. & exit /b 1)

echo [1/4] Python environment and packages (a few minutes the first time)
if not exist .venv\Scripts\python.exe %PY% -m venv .venv || exit /b 1
.venv\Scripts\python -m pip install --disable-pip-version-check -q -r requirements.txt || exit /b 1
if not exist .env copy .env.example .env >nul

echo [2/4] Web packages
pushd web
call npm ci --no-audit --no-fund --loglevel=error || (popd & exit /b 1)

echo [3/4] Web build
call npm run build >nul || (echo Web build failed; run "npm run build" in the web folder to see why. & popd & exit /b 1)
popd

echo [4/4] Demo data (Syracuse switchgear RFP)
.venv\Scripts\python -m scripts.seed_demo --reset || (echo If the database is in use, close the Layer 0 windows and run setup again. & exit /b 1)

echo.
echo Setup complete. Start Layer 0 with start.cmd
endlocal
