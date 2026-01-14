import requests
from bs4 import BeautifulSoup
import time
import urllib.parse
import sys
import datetime
import os
from playwright.sync_api import sync_playwright

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

def get_bankruptcy_info(company_name):
    print(f"正在查询全国企业破产重整案件信息网: {company_name}...")
    bankruptcy_data = []
    try:
        with sync_playwright() as p:
            # 启动浏览器
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            )
            page = context.new_page()
            
            # 访问目标网站
            url = "https://pccz.court.gov.cn/pcajxxw/index/xxwsy"
            try:
                page.goto(url, timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # 定位输入框：由于没有确切ID，尝试通过 placeholder 或通用属性
                # 常见 placeholder: "请输入债务人名称", "请输入案号" 等
                # 尝试找到页面上主要的搜索输入框
                search_input = page.locator("input[placeholder*='名称'], input[placeholder*='案号']").first
                if not search_input.is_visible():
                     # 如果找不到特定placeholder，尝试找所有文本输入框的第一个
                     search_input = page.locator("input[type='text']").first

                if search_input.is_visible():
                    search_input.fill(company_name)
                    
                    # 点击查询按钮 (通常包含 "查询" 或 "搜索" 文本)
                    search_btn = page.locator("text=查询").first
                    if not search_btn.is_visible():
                         search_btn = page.locator("button").filter(has_text="查询").first
                    
                    if search_btn.is_visible():
                        search_btn.click()
                        # 等待数据加载
                        page.wait_for_timeout(3000)
                        
                        # 尝试抓取结果
                        # 假设结果会在表格中显示
                        # 寻找包含公司名称的行
                        rows = page.locator("tr").filter(has_text=company_name).all()
                        if rows:
                            for row in rows:
                                text = row.inner_text().strip().replace("\n", " ")
                                if text:
                                    bankruptcy_data.append(text)
                        else:
                            # 检查是否有明确的 "无记录" 提示
                            if page.locator("text=没有找到").is_visible() or page.locator("text=无记录").is_visible():
                                pass # 确认为空
                            else:
                                # 也许是布局不同，尝试获取页面主要文本作为快照
                                pass 
                    else:
                        bankruptcy_data.append("未找到查询按钮，无法自动提交。")
                else:
                    bankruptcy_data.append("未找到搜索框，无法自动输入。")

            except Exception as e:
                print(f"页面操作异常: {e}")
                bankruptcy_data.append(f"查询过程出错: {str(e)[:100]}")

            browser.close()
            
    except Exception as e:
        print(f"Playwright 运行失败 (请确保已运行 'playwright install'): {e}")
        bankruptcy_data.append("自动化浏览器启动失败，请检查环境。")

    return bankruptcy_data

def get_shixin_info(name, code):
    print(f"正在查询中国执行信息公开网: {name} / {code}...")
    shixin_data = []
    
    # 浏览器启动参数优化
    browser_args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-accelerated-2d-canvas",
        "--disable-gpu",
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=browser_args
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
            )
            
            # 注入反爬脚本: 隐藏 webdriver 属性
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            page = context.new_page()
            page.set_default_timeout(60000)
            
            # 访问失信被执行人查询页
            url = "https://zxgk.court.gov.cn/shixin/"
            try:
                page.goto(url)
                page.wait_for_load_state("networkidle")
                
                # 检查是否被拦截/验证码页面
                if "验证" in page.title():
                     print("警告: 可能遇到了验证码拦截页面")

                # 等待输入框出现
                name_input = page.locator("#pName, input[name='pName']").first
                name_input.wait_for(state="visible", timeout=60000)
                name_input.fill(name)

                # 填写身份证号码/组织机构代码
                code_input = page.locator("#pCardNum, #pCode, input[name='pCardNum'], input[name='cardNum']").first
                if code_input.is_visible():
                    code_input.fill(code)
                else:
                    print("未找到代码输入框，尝试直接搜索...")

                # 尝试选择省份: 北京
                try:
                    province_select = page.locator("select").first
                    if province_select.is_visible():
                        options = province_select.locator("option").all_inner_texts()
                        target_option = None
                        for opt in options:
                            if "北京" in opt:
                                target_option = opt
                                break
                        
                        if target_option:
                            province_select.select_option(label=target_option)
                            print(f"已选择省份: {target_option}")
                except Exception as e:
                    print(f"选择省份失败 (非致命错误): {e}")
                
                # 处理验证码
                yzm_input = page.locator("#pYzm")
                if yzm_input.is_visible():
                    captcha_img = page.locator("img[src*='captcha'], img[src*='yzm'], #yzmImg").first
                    if captcha_img.is_visible():
                        print("点击验证码图片以刷新...")
                        captcha_img.click()
                        page.wait_for_timeout(3000)
                    shixin_data.append("检测到图形验证码，程序尝试刷新但无法自动识别。请点击报告中的链接手动核实。")
                else:
                    # 点击查询
                    search_btn = page.locator("button:has-text('查询'), input[value='查询'], .search_btn").first
                    if search_btn.is_visible():
                        search_btn.click()
                        page.wait_for_timeout(3000)
                    else:
                         page.locator("text=查询").first.click()
                    
                    # 检查结果
                    if page.locator("text=验证码错误").first.is_visible():
                         shixin_data.append("验证码校验失败（此网站有强制验证码）。")
                    elif page.locator("text=没有找到").first.is_visible():
                         pass # 无记录
                    else:
                         rows = page.locator("tr").all()
                         for row in rows:
                             text = row.inner_text().strip().replace("\n", " ")
                             if name in text:
                                 shixin_data.append(text)
            except Exception as e:
                print(f"查询异常详情: {e}")
                shixin_data.append(f"查询异常: {str(e)[:100]}")
            
            browser.close()
    except Exception as e:
        shixin_data.append(f"驱动异常: {e}")
    return shixin_data

def send_feishu_notification(risks, bankruptcy_data, shixin_data):
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        print("\n[!] 未配置 FEISHU_WEBHOOK_URL 环境变量，跳过发送飞书通知。")
        return

    risk_count = len(risks)
    bankruptcy_count = len(bankruptcy_data)
    shixin_count = len(shixin_data)
    total_risks = risk_count + bankruptcy_count + shixin_count

    if total_risks == 0:
        title = "✅ 企业风险监控日报 - 一切正常"
        color = "green"
    else:
        title = f"⚠️ 企业风险警告 - 发现 {total_risks} 条风险"
        color = "red"

    # 构建卡片内容
    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": f"**监控对象:** {COMPANY_NAME}\n**查询时间:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}},
        {"tag": "hr"}
    ]

    if bankruptcy_data:
        text = "**【破产重整】:**\n" + "\n".join([f"- {item}" for item in bankruptcy_data])
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": text}})

    if shixin_data:
        text = "**【失信被执行】:**\n" + "\n".join([f"- {item}" for item in shixin_data])
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": text}})

    if risks:
        text = "**【舆情风险】:**\n" + "\n".join([f"- [{r['title']}]({r['link']})" for r in risks[:5]])
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": text}})

    if total_risks == 0:
         elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "暂未发现破产、失信或明显负面舆情。"}})

    card = {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": title}, "template": color},
        "elements": elements
    }

    try:
        response = requests.post(webhook_url, json={"msg_type": "interactive", "card": card})
        if response.status_code == 200:
            print("\n[√] 飞书通知发送成功")
        else:
            print(f"\n[x] 飞书通知发送失败: {response.text}")
    except Exception as e:
        print(f"\n[x] 发送飞书异常: {e}")

def generate_html(risks, bankruptcy_data, shixin_data):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    qcc_url = f"https://www.qcc.com/web/search?key={urllib.parse.quote(COMPANY_NAME)}"
    tyc_url = f"https://www.tianyancha.com/search?key={urllib.parse.quote(COMPANY_NAME)}"
    
    bankruptcy_html = ""
    if bankruptcy_data:
        list_items = "".join([f"<li class='risk-item'>⚠️ {item}</li>" for item in bankruptcy_data])
        bankruptcy_html = f"""
        <div class="card" style="border-left: 5px solid #e74c3c;">
            <h2>⚠️ 破产重整信息 (自动查询结果)</h2>
            <ul class="risk-list">
                {list_items}
            </ul>
        </div>
        """
    else:
        bankruptcy_html = f"""
        <div class="card">
            <h2>⚖️ 破产重整信息 (自动查询结果)</h2>
            <p class='status-ok'>✅ 暂未在“全国企业破产重整案件信息网”自动检索到相关记录。</p>
        </div>
        """

    shixin_html = ""
    if shixin_data:
        list_items = "".join([f"<li class='risk-item'>❌ {item}</li>" for item in shixin_data])
        shixin_html = f"""
        <div class="card" style="border-left: 5px solid #c0392b;">
            <h2>❌ 失信被执行人信息 (自动查询结果)</h2>
            <ul class="risk-list">
                {list_items}
            </ul>
        </div>
        """
    else:
        shixin_html = f"""
        <div class="card">
            <h2>👤 失信被执行人信息 (自动查询结果)</h2>
            <p class='status-ok'>✅ 暂未在中国执行信息公开网发现该姓名/代码的失信记录。</p>
        </div>
        """

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

    {bankruptcy_html}
    {shixin_html}

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
            <a href="https://zxgk.court.gov.cn/" target="_blank" class="link-item">
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
    bankruptcy_data = get_bankruptcy_info(COMPANY_NAME)
    shixin_data = get_shixin_info("刘斌", "MA0044Y57")
    generate_html(risks, bankruptcy_data, shixin_data)
    send_feishu_notification(risks, bankruptcy_data, shixin_data)

if __name__ == "__main__":
    main()

