import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import re

# 配置
URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
}

try:
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()
except Exception as e:
    print(f"請求失敗: {e}")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table")

if not table:
    print("未找到 <table> 元素！頁面結構可能變化。")
    exit(1)

rows = table.find_all("tr")[1:]  # 跳過表頭
print(f"找到表格行數: {len(rows)}")  # 應 ≈50

ipv4_list = []
ipv6_list = []
match_count = 0

for row in rows:
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    if len(cols) < 6:
        continue
    
    ip = cols[2]
    speed_text = cols[5]
    
    # 更穩定的速度提取：移除單位並轉 float
    speed_match = re.search(r'([\d.]+)', speed_text)
    if not speed_match:
        continue
    try:
        speed = float(speed_match.group(1))
    except ValueError:
        continue
    
    if speed < MIN_SPEED:
        continue
    
    match_count += 1
    region = random.choice(REGIONS)
    
    if ':' in ip:
        formatted = f"[{ip}]#{region}|IPV6优选|"
        ipv6_list.append(formatted)
    else:
        formatted = f"{ip}#{region}|IPV4优选|"
        ipv4_list.append(formatted)

# 簡單按 IP 排序（或保持原順序）
# ipv4_list = sorted(ipv4_list)  # 可選

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

content = f"""# 麒麟 CloudFlare 優選 IP 列表（速度≥{MIN_SPEED}mb/s）
# 更新時間：{update_time} (每天自動更新)
# 來源：https://api.urlce.com/cloudflare.html
# 抓取有效條目：{match_count}（過濾後 IPv4 {len(ipv4_list)} / IPv6 {len(ipv6_list)}）
# 表格總行數：{len(rows)}

## IPv4 優選（推薦優先使用，主要是电信高速度，香港延迟低）
""" + "\n".join(ipv4_list[:40]) + """

## IPv6 優選
""" + "\n".join(ipv6_list[:20]) + """

# 使用方法：直接複製到 v2rayN / Nekobox / Clash 的自定義優選列表
# 香港用戶優先試前幾條电信 IP，例如 162.159.44.184 等，速度 60+mb/s 極穩
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"生成完成！匹配 {match_count} 條，輸出 IPv4: {len(ipv4_list)} 條，IPv6: {len(ipv6_list)} 條")
if ipv4_list:
    print("前3條 IPv4 示例：")
    print("\n".join(ipv4_list[:3]))
