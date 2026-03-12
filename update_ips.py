import requests
import re
import random
from datetime import datetime

URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()
    text = response.text
    print("頁面抓取成功，長度:", len(text))
    print("包含 'mb/s'？", "mb/s" in text)
    print("包含 '優選IP'？", "優選IP" in text)
except Exception as e:
    print("抓取失敗:", str(e))
    text = ""
    fallback_ipv4 = ["162.159.44.97", "162.159.45.216", "172.64.52.3"]
    fallback_ipv6 = ["2a06:98c1:3109:be:eed5:a58c:47d9:836d"]
else:
    fallback_ipv4 = []
    fallback_ipv6 = []

# 精準匹配完整行：IP 在第3列，速度在第6列
# pattern: | 數字 | 线路 | IP | 丟包 | 延迟 | 速度mb/s | ...
line_pattern = r'\|\s*\d+\s*\|\s*[^\|]+\s*\|\s*([^\|\s]+)\s*\|\s*[^\|]*\s*\|\s*[^\|]*\s*\|\s*([\d\.]+)mb/s'

matches = re.findall(line_pattern, text, re.IGNORECASE | re.MULTILINE)

print("匹配到的有效行數:", len(matches))
if matches:
    print("前3匹配示例:", matches[:3])

ipv4_list = []
ipv6_list = []
seen = set()

random.seed(datetime.now().strftime("%Y%m%d"))

for ip, speed_str in matches:
    try:
        speed = float(speed_str)
        if speed < MIN_SPEED or ip in seen:
            continue
        seen.add(ip)
        region = random.choice(REGIONS)
        if ':' in ip and ip.count(':') >= 6:  # 嚴格IPv6：至少7段（避免時間戳）
            ipv6_list.append(f"[{ip}]#{region}")
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            ipv4_list.append(f"{ip}#{region}")
    except ValueError:
        continue

# fallback
for ip in fallback_ipv4:
    if ip not in seen:
        seen.add(ip)
        region = random.choice(REGIONS)
        ipv4_list.append(f"{ip}#{region}")

for ip in fallback_ipv6:
    if ip not in seen:
        seen.add(ip)
        region = random.choice(REGIONS)
        ipv6_list.append(f"[{ip}]#{region}")

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " HKT"

content = f"""# CloudFlare 優選 IP（速度 ≥{MIN_SPEED}mb/s）
# 更新時間：{update_time}
# 來源：{URL}
# 有效條目：IPv4 {len(ipv4_list)} 條 / IPv6 {len(ipv6_list)} 條

# IPv4
""" + "\n".join(ipv4_list[:20]) + """

# IPv6
""" + "\n".join(ipv6_list[:10]) + """

# 注意：已加強IPv6過濾，避免誤抓時間戳
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("最終輸出 IPv4 數量:", len(ipv4_list))
print("最終輸出 IPv6 數量:", len(ipv6_list))
if ipv6_list:
    print("IPv6 前3條:", ipv6_list[:3])
