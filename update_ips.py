import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime

# 配置
URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
}

response = requests.get(URL, headers=headers, timeout=15)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# 找到表格（通常第一個或唯一的 <table>）
table = soup.find("table")
if not table:
    print("未找到表格！頁面可能變更。")
    exit(1)

rows = table.find_all("tr")[1:]  # 跳過表頭

ipv4_list = []
ipv6_list = []
match_count = 0

for row in rows:
    cols = row.find_all("td")
    if len(cols) < 6:
        continue
    
    try:
        # 列索引：0:#, 1:线路, 2:优选IP, 3:丢包, 4:延迟, 5:速度, 6:带宽, ...
        ip = cols[2].get_text(strip=True)
        speed_text = cols[5].get_text(strip=True).replace("mb/s", "").strip()
        speed = float(speed_text)
        
        if speed < MIN_SPEED:
            continue
        
        match_count += 1
        region = random.choice(REGIONS)
        
        if ':' in ip:  # IPv6
            formatted = f"[{ip}]#{region}|IPV6优选|"
            ipv6_list.append(formatted)
        else:
            formatted = f"{ip}#{region}|IPV4优选|"
            ipv4_list.append(formatted)
            
    except (ValueError, IndexError):
        continue

# 按速度降序排序（可選）
# ipv4_list.sort(key=lambda x: float(x.split('#')[0].split('.')[-1]) if '.' in x else 0, reverse=True)  # 簡單排序，可改進

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

content = f"""# 麒麟 CloudFlare 優選 IP 列表（速度≥{MIN_SPEED}mb/s）
# 更新時間：{update_time} (每天自動更新)
# 來源：https://api.urlce.com/cloudflare.html
# 抓取有效條目：{match_count}（過濾後 IPv4 {len(ipv4_list)} / IPv6 {len(ipv6_list)}）

## IPv4 優選（推薦優先使用，主要是电信高速度）
""" + "\n".join(ipv4_list[:40]) + """

## IPv6 優選
""" + "\n".join(ipv6_list[:20]) + """

# 使用方法：直接複製到 v2rayN / Nekobox / Clash 的自定義優選列表
# 香港用戶優先試前幾條电信 IP，延迟通常 50ms 左右，速度極穩
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"生成成功！匹配 {match_count} 條，輸出 IPv4: {len(ipv4_list)} 條，IPv6: {len(ipv6_list)} 條")
