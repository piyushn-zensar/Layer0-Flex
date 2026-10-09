@echo off
rem Puts the demo data back to its starting state. Close the two "Layer 0" windows first.
cd /d "%~dp0"
.venv\Scripts\python -m scripts.seed_demo --reset || (echo Close the "Layer 0" windows first, then run this again. & exit /b 1)
echo Demo data reset. Start Layer 0 with start.cmd
