#!/bin/bash

# Configuration
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$PROJECT_DIR/monitor.pid"
LOG_FILE="$PROJECT_DIR/monitor.log"
WEB_PID_FILE="$PROJECT_DIR/web.pid"
WEB_LOG_FILE="$PROJECT_DIR/web.log"
WEB_PORT=8000
SCRIPT_NAME="$0"

# Navigate to project directory
cd "$PROJECT_DIR" || { echo "Failed to cd to $PROJECT_DIR"; exit 1; }

# Activate virtual environment
source venv/bin/activate

# Set Feishu Webhook URL (Replace with your actual URL)
# export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/..."

# Function: The actual monitoring logic
monitor_loop() {
    echo "[$(date)] Starting monitor service..."

    # Execute immediately on startup
    echo "[$(date)] Performing immediate run..."
    python monitor.py

    # Run the monitor script continuously at scheduled times
    echo "Starting monitor scheduler... The script will run at 10:00 and 17:00 daily."

    while true; do
        current_time=$(date +%H:%M)
        
        if [[ "$current_time" == "10:00" ]] || [[ "$current_time" == "17:00" ]]; then
            echo "[$(date)] Starting scheduled monitoring task..."
            python monitor.py
            echo "[$(date)] Task completed."
            # Sleep for 61 seconds to prevent multiple runs within the same minute
            sleep 61
        else
            # Check time every 30 seconds
            sleep 30
        fi
    done
}

# Control Logic
case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Monitor is already running (PID: $PID)."
                exit 1
            else
                echo "Found stale PID file. Removing..."
                rm "$PID_FILE"
            fi
        fi

        echo "Starting monitor in background..."
        # Launch the loop in background using nohup and this script's 'monitor_loop' argument
        nohup "$SCRIPT_NAME" monitor_loop >> "$LOG_FILE" 2>&1 &
        
        NEW_PID=$!
        echo "$NEW_PID" > "$PID_FILE"
        echo "Monitor started with PID: $NEW_PID"
        echo "Logs are being written to $LOG_FILE"
        ;;

    stop)
        if [ ! -f "$PID_FILE" ]; then
            echo "Monitor is not running (PID file not found)."
            exit 1
        fi

        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Stopping monitor (PID: $PID)..."
            kill "$PID"
            rm "$PID_FILE"
            echo "Monitor stopped."
        else
            echo "Monitor process $PID not found. Cleaning up stale PID file."
            rm "$PID_FILE"
        fi
        ;;

    restart)
        "$0" stop
        sleep 1
        "$0" start
        ;;

    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Monitor is running. PID: $PID"
            else
                echo "Monitor is NOT running (Stale PID file found)."
            fi
        else
            echo "Monitor is NOT running."
        fi
        ;;
    
    start-web)
        if [ -f "$WEB_PID_FILE" ]; then
            PID=$(cat "$WEB_PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Web server is already running (PID: $PID)."
                echo "Access at http://localhost:$WEB_PORT"
                exit 1
            else
                echo "Found stale Web PID file. Removing..."
                rm "$WEB_PID_FILE"
            fi
        fi

        echo "Starting Web server on port $WEB_PORT..."
        export PORT=$WEB_PORT
        nohup python server.py >> "$WEB_LOG_FILE" 2>&1 &
        
        NEW_PID=$!
        echo "$NEW_PID" > "$WEB_PID_FILE"
        echo "Web server started with PID: $NEW_PID"
        echo "Access at http://localhost:$WEB_PORT"
        ;;

    stop-web)
        if [ ! -f "$WEB_PID_FILE" ]; then
            echo "Web server is not running."
            exit 1
        fi

        PID=$(cat "$WEB_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Stopping Web server (PID: $PID)..."
            kill "$PID"
            rm "$WEB_PID_FILE"
            echo "Web server stopped."
        else
            echo "Web process $PID not found. Cleaning up stale PID file."
            rm "$WEB_PID_FILE"
        fi
        ;;

    status-web)
        if [ -f "$WEB_PID_FILE" ]; then
            PID=$(cat "$WEB_PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Web server is running. PID: $PID"
                echo "URL: http://localhost:$WEB_PORT"
            else
                echo "Web server is NOT running (Stale PID file found)."
            fi
        else
            echo "Web server is NOT running."
        fi
        ;;

    start-all)
        echo "Starting ALL services..."
        "$0" start
        "$0" start-web
        ;;

    stop-all)
        echo "Stopping ALL services..."
        "$0" stop
        "$0" stop-web
        ;;

    status-all)
        "$0" status
        echo "----------------------------------------"
        "$0" status-web
        ;;

    monitor_loop)
        # Internal argument to run the loop logic
        monitor_loop
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|start-web|stop-web|status-web|start-all|stop-all|status-all}"
        exit 1
        ;;
esac