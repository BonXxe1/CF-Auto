import requests
import re
import random
from datetime import datetime

url = "https://api.urlce.com/cloudflare.html"
regions = ["US", "JP", "KR", "HK", "SG", "TW"]

try:
    text = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}).text
except Exception as e:
    print("請求失敗:", e)
    exit()

# 寬鬆正則：匹配 IP（數字.數字 或 IPv6:） + 速度數字 mb/s
# 忽略中間列的具體內容
pattern = r'\|\s*\d+\s*\|\s*[^\|]+\s*\|\s*([^\|\s]+)\s*\|\s*[^\|]*\s*\|\s*[^\|]*\s*\|\s*([\d\.]+)mb/s'

matches = re.findall(pattern, text, re.IGNORECASE)

ipv4 = []
ipv6 = []
seen = set()

random.seed(datetime.now().strftime("%Y%m%d"))

for ip, speed_str in matches:
    try:
        speed = float(speed_str)
        if speed < 20 or ip in seen:
            continue
        seen.add(ip)
        region = random.choice(regions)
        if ':' in ip:
            ipv6.append(f"[{ip}]#{region}")
        else:
            ipv4.append(f"{ip}#{region}")
    except:
        pass

content = f"""# CloudFlare 優選 IP（速度 ≥20mb/s）
# 更新時間：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} HKT
# 抓到 IPv4: {len(ipv4)} 條 / IPv6: {len(ipv6)} 條

IPv4:
""" + "\n".join(ipv4[:30]) + """

IPv6:
""" + "\n".join(ipv6[:10]) + """
"""

with open("cf-ips.txt", "w", encoding="utf-8") as f:
    f.write(content)

print("IPv4 數量:", len(ipv4))
if ipv4:
    print("前3:", ipv4[:3])
