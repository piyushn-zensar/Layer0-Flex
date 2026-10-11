@echo off
rem Starts Layer 0 (API on port 8000, web on port 3000) and opens the demo in the browser.
rem Stop it by closing the two "Layer 0" windows.
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run setup.cmd first. & exit /b 1)
if not exist web\.next\BUILD_ID (echo Run setup.cmd first. & exit /b 1)

rem --timeout-keep-alive 75: the web app's proxy reuses idle connections; uvicorn's default closes them after 5 s,
rem which now and then made a page load fail with "socket hang up"
start "Layer 0 API" /min .venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 75
start "Layer 0 web" /min cmd /c "cd /d web && npm start -- -p 3000"

echo Starting Layer 0...
set /a tries=0
:wait
curl -s -o nul http://127.0.0.1:8000/docs && curl -s -o nul http://127.0.0.1:3000/portfolio && goto ready
set /a tries+=1
if %tries% geq 60 (echo Layer 0 did not start within a minute. Check the two "Layer 0" windows; ports 3000 and 8000 must be free. & exit /b 1)
timeout /t 1 /nobreak >nul
goto wait

:ready
echo Layer 0 is running at http://localhost:3000
if not "%NO_BROWSER%"=="1" start "" http://localhost:3000/opportunities/OPP-0001/trace
endlocal
