# 企业经营风险监控工具

该工具用于辅助监控 "北京中兵数字科技集团有限公司" 的经营风险信息。
它通过搜索引擎聚合查询关键风险词（如破产、跑路、欠薪等），并提供权威政府公示网站的直达链接。

## 环境要求

- Python 3
- 网络连接（访问百度及相关查询网站）

## 安装与设置

1. **激活虚拟环境** (如果尚未激活):
   ```bash
   source venv/bin/activate
   ```

2. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

## 使用方法

运行监控脚本：

```bash
python monitor.py
```

## 飞书通知设置

1. 在飞书群组中添加 "自定义机器人"。
2. 获取机器人的 Webhook URL。
3. 编辑 `run_monitor.sh` 文件，设置 `FEISHU_WEBHOOK_URL` 变量：
   ```bash
   export FEISHU_WEBHOOK_URL="你的飞书Webhook地址"
   ```
   或者在运行前设置环境变量：
   ```bash
   export FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxx"
   python monitor.py
   ```

## 定时任务设置 (Mac/Linux)

本项目包含 `run_monitor.sh` 脚本用于定时执行。

1. 确保脚本有执行权限：
   ```bash
   chmod +x run_monitor.sh
   ```

2. 编辑 crontab (`crontab -e`) 并添加以下行（每天 10:00 和 17:00 执行）：
   ```bash
   0 10,17 * * * /path/to/corporate-risk-monitor/run_monitor.sh >> /path/to/corporate-risk-monitor/monitor.log 2>&1
   ```

## 功能说明

1. **舆情监控**: 自动搜索百度新闻和网页，查找包含 "破产", "跑路", "欠薪", "被执行" 等关键词的最新信息。
2. **人工核查导航**: 程序运行结束后，会输出以下权威网站的直达链接或查询指引，建议**每周手动核查一次**：
   - **全国企业破产重整案件信息网**: 最权威的破产立案信息。
   - **中国执行信息公开网**: 查询公司是否被列为"失信被执行人"（老赖）。
   - **企查查/天眼查**: 查看企业的司法诉讼和经营异常更新。

## 启动程序
   - 启动 Web 服务: ./run_monitor.sh start-web
   - 访问报告: 打开浏览器访问 http://<你的服务器IP>:8000 (如果在本机则是 http://localhost:8000)
   - 停止 Web 服务: ./run_monitor.sh stop-web
   - 查看 Web 状态: ./run_monitor.sh status-web
   
## 免责声明

本工具仅作为信息聚合辅助，自动化搜索结果可能存在滞后或遗漏。**最准确的法律状态请务必以“全国企业破产重整案件信息网”及法院判决为准。**
