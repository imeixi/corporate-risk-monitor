#!/bin/bash

# Navigate to project directory
cd /Users/zhengaihua/WorkSpace/corporate-risk-monitor

# Activate virtual environment
source venv/bin/activate

# Set Feishu Webhook URL (Replace with your actual URL)
# export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/..."

# Run the monitor script
python monitor.py
