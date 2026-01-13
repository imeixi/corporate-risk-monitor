#!/bin/bash

# Configuration
PROJECT_DIR="/Users/zhengaihua/WorkSpace/corporate-risk-monitor"
PID_FILE="$PROJECT_DIR/monitor.pid"
LOG_FILE="$PROJECT_DIR/monitor.log"
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

    monitor_loop)
        # Internal argument to run the loop logic
        monitor_loop
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac