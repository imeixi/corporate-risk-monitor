import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import sys
import datetime
import os

# Company Information
COMPANY_NAME = "北京中兵数字科技集团有限公司"
CREDIT_CODE = "91110102MA0044Y57L"

# Risk Keywords to monitor
KEYWORDS = ["破产", "跑路", "欠薪", "被执行", "失信", "清算", "裁判", "仲裁", "停业"]

def get_baidu_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }
    risks = []
    query = f'"{COMPANY_NAME}" (破产 | 跑路 | 欠薪 | 失信 | 被执行)'
    url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('div', class_='result') or soup.find_all('div', class_='c-container')
            for res in results:
                title_tag = res.find('h3')
                if title_tag:
                    title_text = title_tag.get_text().strip()
                    for kw in KEYWORDS:
                        if kw in title_text:
                            link = title_tag.find('a')['href'] if title_tag.find('a') else "#"
                            risks.append({"title": title_text, "link": link})
                            break
    except Exception as e:
        print(f"Error fetching news: {e}")
    return risks

def generate_html(risks):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    qcc_url = f"https://www.qcc.com/web/search?key={urllib.parse.quote(COMPANY_NAME)}"
    tyc_url = f"https://www.tianyancha.com/search?key={urllib.parse.quote(COMPANY_NAME)}"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>企业风险监控报告 - {COMPANY_NAME}</title>
    <style>
        body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f4f7f9; }}
        .card {{ background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ font-size: 1.2em; color: #2980b9; margin-top: 0; }}
        .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px; }}
        .timestamp {{ color: #7f8c8d; font-size: 0.9em; text-align: right; }}
        .status-ok {{ color: #27ae60; font-weight: bold; }}
        .status-warn {{ color: #e74c3c; font-weight: bold; }}
        .link-group {{ margin-bottom: 15px; }}
        .link-item {{ display: block; padding: 10px; margin: 5px 0; background: #ebf5fb; border-left: 4px solid #3498db; text-decoration: none; color: #2c3e50; transition: 0.2s; }}
        .link-item:hover {{ background: #d6eaf8; transform: translateX(5px); }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 8px; }}
        .badge-gov {{ background: #e74c3c; color: #fff; }} /* 官方权威 */
        .badge-third {{ background: #3498db; color: #fff; }} /* 第三方平台 */
        .risk-list {{ list-style: none; padding: 0; }}
        .risk-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
        .risk-item a {{ color: #e67e22; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>企业风险监控报告</h1>
        <div class="info-grid">
            <div><strong>公司名称:</strong> {COMPANY_NAME}</div>
            <div class="timestamp">查询时间: {now}</div>
            <div><strong>信用代码:</strong> {CREDIT_CODE}</div>
        </div>
    </div>

    <div class="card">
        <h2>🔍 实时舆情检测 (Baidu)</h2>
        {"<ul class='risk-list'>" + "".join([f"<li class='risk-item'>⚠️ <a href='{r['link']}' target='_blank'>{r['title']}</a></li>" for r in risks]) + "</ul>" if risks else "<p class='status-ok'>✅ 当前未在搜索首页发现明显破产/跑路相关新闻。</p>"}
    </div>

    <div class="card">
        <h2>🏛️ 官方权威渠道 (最高优先级)</h2>
        <div class="link-group">
            <a href="https://pccz.court.gov.cn/pcajxxw/index/xxwsy" target="_blank" class="link-item">
                <span class="badge badge-gov">政府</span> 全国企业破产重整案件信息网
                <br><small style="color:#666">核心关注：在此搜索公司全名，查看是否有破产立案。</small>
            </a>
            <a href="http://zxgk.court.gov.cn/" target="_blank" class="link-item">
                <span class="badge badge-gov">政府</span> 中国执行信息公开网
                <br><small style="color:#666">核心关注：查询是否被列为“失信被执行人”。组织机构代码: {CREDIT_CODE[8:17]}</small>
            </a>
        </div>

        <h2>📊 第三方企业信用平台</h2>
        <div class="link-group">
            <a href="{qcc_url}" target="_blank" class="link-item">
                <span class="badge badge-third">平台</span> 企查查 - 司法风险监控
            </a>
            <a href="{tyc_url}" target="_blank" class="link-item">
                <span class="badge badge-third">平台</span> 天眼查 - 经营异常监控
            </a>
        </div>
    </div>

    <div class="card" style="background: #fff3cd; border-left: 5px solid #ffc107;">
        <p><strong>💡 提示：</strong> 2月15日是第一个支付节点。若当天未到账，请于次日携带仲裁裁决书前往法院申请<strong>强制执行</strong>。</p>
    </div>
</body>
</html>
"""
    with open("risk_report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n[√] 报告已生成: {os.path.abspath('risk_report.html')}")

def main():
    print(f"正在监控: {COMPANY_NAME}...")
    risks = get_baidu_news()
    generate_html(risks)

if __name__ == "__main__":
    main()

