@echo off
setlocal
cd /d "%~dp0"

echo.
echo  School Program Intelligence
echo  Starting local UI...
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found on PATH. Install Python 3.11+ and try again.
  pause
  exit /b 1
)

python -c "import school_program_intelligence" 1>nul 2>&1
if errorlevel 1 (
  echo Installing package ^(editable, with web extras^)...
  python -m pip install -e ".[dev,web]"
  if errorlevel 1 (
    echo Install failed.
    pause
    exit /b 1
  )
)

set HOST=127.0.0.1
set PORT=8000
set URL=http://%HOST%:%PORT%/

echo.
echo  Open: %URL%
echo  Fixture: toy_elementary
echo  Press Ctrl+C to stop the server.
echo.

start "" "%URL%"
python -m school_program_intelligence.cli serve --host %HOST% --port %PORT%
if errorlevel 1 (
  echo.
  echo Server exited with an error.
  pause
  exit /b 1
)

endlocal
