import requests
import re
import random
from datetime import datetime

URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(URL, headers=headers, timeout=15)
text = response.text

# 用正則匹配表格行（兼容 Markdown 格式）
# 匹配格式：| 數字 | 线路 | IP | 丟包 | 延迟 | 速度mb/s | ...
pattern = r'\|\s*(\d+)\s*\|\s*(电信|联通|移动|多线|IPV6)\s*\|\s*([\d\.\:a-fA-F]+)\s*\|\s*[^|]*\|\s*[^|]*\|\s*([\d\.]+)mb/s'

matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)

ipv4 = []
ipv6 = []
seen = set()

random.seed(datetime.now().strftime("%Y%m%d"))

for _, line_type, ip, speed_str in matches:
    try:
        speed = float(speed_str)
        if speed < MIN_SPEED or ip in seen:
            continue
        seen.add(ip)
        region = random.choice(REGIONS)
        if ':' in ip:
            ipv6.append(f"[{ip}]#{region}")
        else:
            ipv4.append((f"{ip}#{region}", speed))
    except ValueError:
        continue

# 按速度降序
ipv4.sort(key=lambda x: x[1], reverse=True)
ipv4 = [item[0] for item in ipv4]

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S HKT")

content = f"""# CloudFlare 优选 IP（速度 ≥ {MIN_SPEED}mb/s）
# 更新時間：{update_time}
# 來源：{URL}
# 有效數量：IPv4 {len(ipv4)} / IPv6 {len(ipv6)}

# IPv4（推薦優先用，按速度降序）
""" + "\n".join(ipv4) + """

# IPv6
""" + "\n".join(ipv6) + """

# 使用方式：直接貼到 v2rayN / Nekobox / Clash 自訂優選列表
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"完成！抓到 IPv4: {len(ipv4)} 條，IPv6: {len(ipv6)} 條")
if ipv4:
    print("前 5 條 IPv4 示例：")
    print("\n".join(ipv4[:5]))
