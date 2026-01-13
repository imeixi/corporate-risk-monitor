@echo off
setlocal EnableDelayedExpansion

REM Configuration
set "PROJECT_DIR=%~dp0"
set "PID_FILE=%PROJECT_DIR%monitor.pid"
set "LOG_FILE=%PROJECT_DIR%monitor.log"
set "WEB_PID_FILE=%PROJECT_DIR%web.pid"
set "WEB_LOG_FILE=%PROJECT_DIR%web.log"
set "WEB_PORT=8000"

REM Activate Virtual Environment (Assumes venv exists)
if exist "%PROJECT_DIR%venv\Scripts\activate.bat" (
    call "%PROJECT_DIR%venv\Scripts\activate.bat"
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

echo Usage: %0 {start|stop|status|start-web|stop-web|status-web|start-all|stop-all|status-all}
goto :eof

:start_monitor
    if exist "%PID_FILE%" (
        set /p PID=<"%PID_FILE%"
        tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "!PID!" >NUL
        if !ERRORLEVEL! EQU 0 (
            echo Monitor is already running (PID: !PID!).
            goto :eof
        ) else (
            echo Found stale PID file. Removing...
            del "%PID_FILE%"
        )
    )
    echo Starting monitor in background...
    REM Using PowerShell to start process hidden and get PID
    powershell -Command "$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c %~nx0 monitor_loop' -RedirectStandardOutput '%LOG_FILE%' -RedirectStandardError '%LOG_FILE%' -PassThru -WindowStyle Hidden; $p.Id | Out-File '%PID_FILE%' -Encoding ASCII"
    
    if exist "%PID_FILE%" (
        set /p NEW_PID=<"%PID_FILE%"
        echo Monitor started with PID: !NEW_PID!
        echo Logs are being written to %LOG_FILE%
    )
    goto :eof

:stop_monitor
    if not exist "%PID_FILE%" (
        echo Monitor is not running.
        goto :eof
    )
    set /p PID=<"%PID_FILE%"
    echo Stopping monitor (PID: !PID!)...
    taskkill /F /PID !PID! >NUL 2>&1
    del "%PID_FILE%"
    echo Monitor stopped.
    goto :eof

:status_monitor
    if exist "%PID_FILE%" (
        set /p PID=<"%PID_FILE%"
        tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "!PID!" >NUL
        if !ERRORLEVEL! EQU 0 (
            echo Monitor is running. PID: !PID!
        ) else (
            echo Monitor is NOT running (Stale PID file found).
        )
    ) else (
        echo Monitor is NOT running.
    )
    goto :eof

:monitor_loop
    echo [%DATE% %TIME%] Starting monitor service...
    echo [%DATE% %TIME%] Performing immediate run...
    python monitor.py
    
    echo Starting monitor scheduler... Daily at 10:00 and 17:00.
    
    :loop
    for /f "tokens=1-2 delims=:" %%a in ("%TIME%") do (
        set "H=%%a"
        set "M=%%b"
    )
    REM Handle leading space in hour (e.g., " 9")
    set "H=!H: =0!"
    set "CURRENT_TIME=!H!:!M!"
    
    if "!CURRENT_TIME!"=="10:00" call :run_task
    if "!CURRENT_TIME!"=="17:00" call :run_task
    
    timeout /t 30 /nobreak >nul
    goto loop

:run_task
    echo [%DATE% %TIME%] Starting scheduled monitoring task...
    python monitor.py
    echo [%DATE% %TIME%] Task completed.
    timeout /t 61 /nobreak >nul
    goto :eof

:start_web
    if exist "%WEB_PID_FILE%" (
        set /p PID=<"%WEB_PID_FILE%"
        tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "!PID!" >NUL
        if !ERRORLEVEL! EQU 0 (
            echo Web server is already running (PID: !PID!).
            goto :eof
        ) else (
            del "%WEB_PID_FILE%"
        )
    )
    echo Starting Web server on port %WEB_PORT%...
    set PORT=%WEB_PORT%
    powershell -Command "$p = Start-Process -FilePath 'python' -ArgumentList 'server.py' -RedirectStandardOutput '%WEB_LOG_FILE%' -RedirectStandardError '%WEB_LOG_FILE%' -PassThru -WindowStyle Hidden; $p.Id | Out-File '%WEB_PID_FILE%' -Encoding ASCII"
    
    if exist "%WEB_PID_FILE%" (
        set /p NEW_PID=<"%WEB_PID_FILE%"
        echo Web server started with PID: !NEW_PID!
        echo Access at http://localhost:%WEB_PORT%
    )
    goto :eof

:stop_web
    if not exist "%WEB_PID_FILE%" (
        echo Web server is not running.
        goto :eof
    )
    set /p PID=<"%WEB_PID_FILE%"
    echo Stopping Web server (PID: !PID!)...
    taskkill /F /PID !PID! >NUL 2>&1
    del "%WEB_PID_FILE%"
    echo Web server stopped.
    goto :eof

:status_web
    if exist "%WEB_PID_FILE%" (
        set /p PID=<"%WEB_PID_FILE%"
        tasklist /FI "PID eq !PID!" 2>NUL | find /I /N "!PID!" >NUL
        if !ERRORLEVEL! EQU 0 (
            echo Web server is running. PID: !PID!
            echo URL: http://localhost:%WEB_PORT%
        ) else (
            echo Web server is NOT running.
        )
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
