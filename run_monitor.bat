@echo off
setlocal EnableDelayedExpansion

REM Configuration
set "PROJECT_DIR=%~dp0"
set "PID_FILE=%PROJECT_DIR%monitor.pid"
set "LOG_FILE=%PROJECT_DIR%monitor.log"
set "LOG_ERR_FILE=%PROJECT_DIR%monitor.err"
set "WEB_PID_FILE=%PROJECT_DIR%web.pid"
set "WEB_LOG_FILE=%PROJECT_DIR%web.log"
set "WEB_LOG_ERR_FILE=%PROJECT_DIR%web.err"
set "WEB_PORT=8000"

REM Ensure we are in the project directory
cd /d "%PROJECT_DIR%"

REM Activate Virtual Environment (Assumes venv exists)
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

REM Command handling
if "%1"=="start" goto start_monitor
if "%1"=="stop" goto stop_monitor
if "%1"=="status" goto status_monitor
if "%1"=="start-web" goto start_web
if "%1"=="stop-web" goto stop_web
if "%1"=="status-web" goto status_web
if "%1"=="start-all" goto start_all
if "%1"=="stop-all" goto stop_all
if "%1"=="status-all" goto status_all
if "%1"=="monitor_loop" goto monitor_loop

echo Usage: %~nx0 {start|stop|status|start-web|stop-web|status-web|start-all|stop-all|status-all}
goto :eof

:start_monitor
    if exist "%PID_FILE%" (
        goto check_monitor_pid
    )
    goto launch_monitor

:check_monitor_pid
    set /p PID= < "%PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "!PID!" >NUL
    if !ERRORLEVEL! EQU 0 (
        echo Monitor is already running (PID: !PID!).
        goto :eof
    )
    echo Found stale PID file. Removing...
    del "%PID_FILE%"

:launch_monitor
    echo Starting monitor in background...
    REM Using PowerShell to start process in a new window and tee output to log file
    powershell -Command "$p = Start-Process powershell -ArgumentList '-NoExit', '-Command', \"& { cmd /c '\"\"%~f0\"\"' monitor_loop 2>&1 | Tee-Object -FilePath '%LOG_FILE%' }\" -PassThru; $p.Id | Out-File '%PID_FILE%' -Encoding ASCII"
    
    timeout /t 2 /nobreak >nul
    if not exist "%PID_FILE%" goto :eof
    
    set /p NEW_PID= < "%PID_FILE%"
    echo Monitor started with PID: !NEW_PID!
    echo Logs are being displayed in a new window and written to %LOG_FILE%
    goto :eof

:stop_monitor
    if not exist "%PID_FILE%" (
        echo Monitor is not running.
        goto :eof
    )
    set /p PID= < "%PID_FILE%"
    echo Stopping monitor (PID: !PID!)...
    taskkill /T /F /PID !PID! >NUL 2>&1
    del "%PID_FILE%"
    echo Monitor stopped.
    goto :eof

:status_monitor
    if not exist "%PID_FILE%" (
        echo Monitor is NOT running.
        goto :eof
    )
    set /p PID= < "%PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "!PID!" >NUL
    if !ERRORLEVEL! EQU 0 (
        echo Monitor is running. PID: !PID!
    ) else (
        echo Monitor is NOT running (Stale PID file found).
    )
    goto :eof

:monitor_loop
    echo [%DATE% %TIME%] Starting monitor service...
    echo [%DATE% %TIME%] Performing immediate run...
    python -u monitor.py
    
    echo Starting monitor scheduler... Daily at 10:00 and 17:00.
    
    :loop
    for /f "tokens=1-2 delims=:" %%a in ("%TIME%") do (
        set "H=%%a"
        set "M=%%b"
    )
    REM Handle leading space in hour (e.g., " 9")
    set "H=!H: =0!"
    set "CURRENT_TIME=!H!:!M!"
    
    echo [%DATE% %TIME%] Heartbeat: Monitor is alive. Checking schedule (Current: !CURRENT_TIME!)...
    
    if "!CURRENT_TIME!"=="10:00" call :run_task
    if "!CURRENT_TIME!"=="17:00" call :run_task
    
    timeout /t 30 /nobreak >nul
    goto loop

:run_task
    echo [%DATE% %TIME%] Starting scheduled monitoring task...
    python -u monitor.py
    echo [%DATE% %TIME%] Task completed.
    timeout /t 61 /nobreak >nul
    goto :eof

:start_web
    if exist "%WEB_PID_FILE%" (
        goto check_web_pid
    )
    goto launch_web

:check_web_pid
    set /p PID= < "%WEB_PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "!PID!" >NUL
    if !ERRORLEVEL! EQU 0 (
        echo Web server is already running (PID: !PID!).
        goto :eof
    )
    del "%WEB_PID_FILE%"

:launch_web
    echo Starting Web server on port %WEB_PORT%...
    set PORT=%WEB_PORT%
    REM Using PowerShell to start process in a new window and tee output to log file
    powershell -Command "$p = Start-Process powershell -ArgumentList '-NoExit', '-Command', \"& { python -u server.py 2>&1 | Tee-Object -FilePath '%WEB_LOG_FILE%' }\" -PassThru; $p.Id | Out-File '%WEB_PID_FILE%' -Encoding ASCII"
    
    timeout /t 2 /nobreak >nul
    if not exist "%WEB_PID_FILE%" goto :eof
    
    set /p NEW_PID= < "%WEB_PID_FILE%"
    echo Web server started with PID: !NEW_PID!
    echo Access at http://localhost:%WEB_PORT%
    echo Logs are being displayed in a new window and written to %WEB_LOG_FILE%
    goto :eof

:stop_web
    if not exist "%WEB_PID_FILE%" (
        echo Web server is not running.
        goto :eof
    )
    set /p PID= < "%WEB_PID_FILE%"
    echo Stopping Web server (PID: !PID!)...
    taskkill /T /F /PID !PID! >NUL 2>&1
    del "%WEB_PID_FILE%"
    echo Web server stopped.
    goto :eof

:status_web
    if not exist "%WEB_PID_FILE%" (
        echo Web server is NOT running.
        goto :eof
    )
    set /p PID= < "%WEB_PID_FILE%"
    tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "!PID!" >NUL
    if !ERRORLEVEL! EQU 0 (
        echo Web server is running. PID: !PID!
        echo URL: http://localhost:%WEB_PORT%
    ) else (
        echo Web server is NOT running.
    )
    goto :eof

:start_all
    call :start_monitor
    call :start_web
    goto :eof

:stop_all
    call :stop_monitor
    call :stop_web
    goto :eof

:status_all
    call :status_monitor
    echo ----------------------------------------
    call :status_web
    goto :eof