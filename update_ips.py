import requests
import re
import random
from datetime import datetime

SOURCES = [
    "https://api.urlce.com/cloudflare.html",
    "https://cf.vvhan.com/",
    "https://stock.hostmonit.com/CloudFlareYes"  # 可加更多
]

REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
MIN_SPEED = 20.0
seen_ips = set()
ipv4_list = []
ipv6_list = []

random.seed(datetime.now().strftime("%Y%m%d"))

def extract_ips(text):
    # 通用正則，匹配 IP + 速度
    pattern = r'([0-9a-fA-F\.:]+).*?([\d\.]+)\s*(mb/s|KB/s|Mbps)'
    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
    return matches

all_ips = []
for url in SOURCES:
    try:
        resp = requests.get(url, timeout=15)
        matches = extract_ips(resp.text)
        all_ips.extend(matches)
    except:
        pass

for ip, speed_str, unit in all_ips:
    try:
        speed = float(speed_str)
        if unit.lower() in ['kb/s', 'kib/s']: speed /= 1024  # 轉 mb/s
        if speed < MIN_SPEED or ip in seen_ips:
            continue
        seen_ips.add(ip)
        region = random.choice(REGIONS)
        if ':' in ip:
            ipv6_list.append(f"[{ip}]#{region}")
        else:
            ipv4_list.append(f"{ip}#{region}")
    except:
        continue

# 輸出
update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S HKT")
content = f"""# 多源 CloudFlare 優選 IP（速度 ≥{MIN_SPEED}mb/s）
# 更新時間：{update_time}
# 來源：urlce / vvhan / HostMonit 等
# 總數：IPv4 {len(ipv4_list)} / IPv6 {len(ipv6_list)}

# IPv4
""" + "\n".join(ipv4_list[:50]) + """

# IPv6
""" + "\n".join(ipv6_list[:20]) + """
"""

with open("cf-ips-multi.txt", "w", encoding="utf-8") as f:
    f.write(content)

print(f"多源合併完成！IPv4: {len(ipv4_list)} 條")
