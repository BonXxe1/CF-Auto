import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime

URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"

random.seed(datetime.now().strftime("%Y%m%d"))

response = requests.get(URL)
soup = BeautifulSoup(response.text, "html.parser")
text = soup.get_text()

# 新正则：适配当前表格（多了查询链接列，速度在第6列）
# 格式示例：| 1 | 电信 | 172.64.52.63 | 0.00% | 51.66ms | 62.88mb/s | 503.04mb | [查询](...) | 时间 |
pattern = r'\|\s*\d+\s*\|\s*(电信|联通|移动|多线|IPV6)\s*\|\s*([\w\.:]+)\s*\|\s*[^|]+\s*\|\s*[^|]+\s*\|\s*([\d.]+)mb/s\s*\|'

matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

ipv4_list = []
ipv6_list = []

print(f"找到匹配行数: {len(matches)}")  # 调试：应该 >0

for line_type, ip, speed_str in matches:
    try:
        speed = float(speed_str)
        if speed < 20:
            continue
    except ValueError:
        continue

    region = random.choice(REGIONS)

    if ':' in ip:
        formatted = f"[{ip}]#{region}|IPV6优选|"
        ipv6_list.append(formatted)
    else:
        formatted = f"{ip}#{region}|IPV4优选|"
        ipv4_list.append(formatted)

# 生成文件
content = f"""# 麒麟 CloudFlare 优选 IP 列表（速度≥20mb/s）
# 更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (每天自动更新)
# 来源：https://api.urlce.com/cloudflare.html

## IPv4 优选（推荐优先使用）
""" + "\n".join(ipv4_list[:10]) + """  # 只取前10条避免过长，可改

## IPv6 优选
""" + "\n".join(ipv6_list) + """

# 使用方法：直接复制到 v2rayN / Nekobox / Clash 的自定义优选列表即可
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"生成成功！IPv4: {len(ipv4_list)} 条，IPv6: {len(ipv6_list)} 条")
