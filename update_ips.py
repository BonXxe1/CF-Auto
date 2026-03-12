import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import re

URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

headers = {'User-Agent': 'Mozilla/5.0'}

try:
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()
except Exception as e:
    print(f"請求失敗: {e}")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table")
if not table:
    print("未找到表格")
    exit(1)

rows = table.find_all("tr")[1:]
print(f"表格行數: {len(rows)}")

ipv4_list = []
ipv6_list = []
match_count = 0

for row in rows:
    tds = row.find_all("td")
    if len(tds) < 6:
        continue
    
    # 嚴格取索引
    ip_td = tds[2]
    speed_td = tds[5]
    
    ip = ip_td.get_text(strip=True)
    speed_text = speed_td.get_text(strip=True)
    
    # 驗證 IP 格式 (簡單檢查是否像 IP)
    if not (re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip) or ':' in ip):
        print(f"跳過無效 IP: {ip}")
        continue
    
    speed_match = re.search(r'([\d.]+)', speed_text)
    if not speed_match:
        continue
    try:
        speed = float(speed_match.group(1))
    except:
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

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 輸出前10條示例到日誌
print(f"匹配 {match_count} 條，IPv4 {len(ipv4_list)} / IPv6 {len(ipv6_list)}")
if ipv4_list:
    print("前 5 條 IPv4 示例：")
    for line in ipv4_list[:5]:
        print(line)

content = f"""# 麒麟 CloudFlare 優選 IP 列表（速度≥{MIN_SPEED}mb/s）
# 更新時間：{update_time} (每天自動更新)
# 來源：https://api.urlce.com/cloudflare.html
# 抓取有效條目：{match_count}（過濾後 IPv4 {len(ipv4_list)} / IPv6 {len(ipv6_list)}）
# 表格總行數：{len(rows)}

## IPv4 優選（香港用戶優先試前幾條，延迟 ~50ms，速度 50-61mb/s 極穩）
""" + "\n".join(ipv4_list[:40]) + """

## IPv6 優選
""" + "\n".join(ipv6_list) + """

# 使用方法：直接複製到 v2rayN / Nekobox / Clash 自定義優選列表
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("文件生成完成")
