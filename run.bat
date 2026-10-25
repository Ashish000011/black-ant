@echo off
rem Black Ant: set up and run everything from one place on Windows.
rem Double-click for the menu, or give a choice: run.bat setup ^| bench ^| benchmarks ^| tests ^| pdf ^| data ^| journey
setlocal
cd /d "%~dp0"
title Black Ant

where uv >nul 2>nul
if errorlevel 1 goto :no_uv

set "action=%~1"
if "%action%"=="" goto :menu
for %%a in (setup bench benchmarks tests pdf data journey) do if /i "%action%"=="%%a" goto :one
goto :usage

:one
call :%action%
exit /b %errorlevel%

:menu
cls
echo.
echo   Black Ant: towing Earth to 2.7 AU
echo   ---------------------------------
echo   1  Set up, the first time: Python 3.12, the model and the test bench
echo   2  Open the 3D test bench in your browser
echo   3  Run the ten official benchmarks, about 12 seconds
echo   4  Run the quick tests, about a minute
echo   5  Build the report PDF: docs\black-ant-report.pdf
echo   6  Turn results\ into the test bench's data
echo   7  Run the full journey, about an hour and a half
echo   0  Quit
echo.
set "pick="
set /p "pick=  Choose 0-7: "
if "%pick%"=="0" exit /b 0
if "%pick%"=="1" call :setup
if "%pick%"=="2" call :bench
if "%pick%"=="3" call :benchmarks
if "%pick%"=="4" call :tests
if "%pick%"=="5" call :pdf
if "%pick%"=="6" call :data
if "%pick%"=="7" call :journey
echo.
pause
goto :menu

:setup
echo Installing the model's packages; uv fetches Python 3.12 itself if it is missing...
uv sync || exit /b 1
call :viewer_packages
exit /b %errorlevel%

:viewer_packages
where npm >nul 2>nul
if errorlevel 1 goto :no_node
echo Installing the test bench's packages...
call npm --prefix viewer ci --no-audit --no-fund
exit /b %errorlevel%

:bench
if not exist "viewer\node_modules" call :viewer_packages || exit /b 1
echo Starting the test bench; your browser opens on it. Press Ctrl+C here to stop it.
call npm --prefix viewer run dev -- --open
exit /b 0

:benchmarks
uv run python -m sim.benchmarks
exit /b %errorlevel%

:tests
uv run pytest -m "not slow"
exit /b %errorlevel%

:pdf
uv run --with markdown==3.7 --with pypdf==5.1.0 python scripts\report_pdf.py
exit /b %errorlevel%

:data
uv run python -m sim.viewer_data
exit /b %errorlevel%

:journey
echo The full journey takes about an hour and a half and rewrites results\.
set "sure="
set /p "sure=  Run it now? y or n: "
if /i not "%sure%"=="y" exit /b 0
uv run python -m sim.scenarios.tow --out results
exit /b %errorlevel%

:no_uv
echo uv is needed first. Install it from https://docs.astral.sh/uv/ and run this again.
pause
exit /b 1

:no_node
echo Node.js is needed for the test bench. Install it from https://nodejs.org and run this again.
exit /b 1

:usage
echo Usage: run.bat [setup ^| bench ^| benchmarks ^| tests ^| pdf ^| data ^| journey]
exit /b 1
