import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime
import os

# ================== 配置 ==================
URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"          # ← 改成英文名，彻底解决乱码
# ========================================

random.seed(datetime.now().strftime("%Y%m%d"))

response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")
text = soup.get_text()

pattern = r'\| \d+ \| (电信|联通|移动|多线|IPV6) \| ([\w\.:]+) \| [^|]+ \| [^|]+ \| ([\d.]+)mb/s \|'
matches = re.findall(pattern, text)

ipv4_list = []
ipv6_list = []

for line_type, ip, speed_str in matches:
    try:
        speed = float(speed_str)
        if speed < 20:
            continue
    except:
        continue

    region = random.choice(REGIONS)

    if ':' in ip:
        formatted = f"[{ip}]#{region}|IPV6优选|"
        ipv6_list.append(formatted)
    else:
        formatted = f"{ip}#{region}|IPV4优选|"
        ipv4_list.append(formatted)

content = f"""# 麒麟 CloudFlare 优选 IP 列表（速度≥20mb/s）
# 更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (每天自动更新)
# 来源：https://api.urlce.com/cloudflare.html

## IPv4 优选（推荐优先使用）
""" + "\n".join(ipv4_list) + """

## IPv6 优选
""" + "\n".join(ipv6_list) + """

# 使用方法：直接复制到 v2rayN / Nekobox / Clash 的自定义优选列表即可
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"✅ 生成成功！IPv4: {len(ipv4_list)} 条，IPv6: {len(ipv6_list)} 条")
