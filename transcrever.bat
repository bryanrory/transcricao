@echo off
rem Atalho: arraste videos/pastas em cima deste arquivo, ou use: transcrever.bat <entrada> [opcoes]
chcp 65001 >nul
"%~dp0.venv\Scripts\python.exe" "%~dp0transcrever.py" %*
echo.
pause
