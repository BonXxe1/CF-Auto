import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime

URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"

random.seed(datetime.now().strftime("%Y%m%d"))

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
response = requests.get(URL, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, "html.parser")
text = soup.get_text(separator=" ", strip=True)  # 更好地处理空格和换行

# 更宽松的正则：匹配 IP + 速度 mb/s，忽略中间列细节
# 捕捉 优选IP (IP部分) 和 速度 (数字.mb/s)
pattern = r'\|\s*\d+\s*\|\s*(电信|联通|移动|多线|IPV6)\s*\|\s*([^\|]+?)\s*\|\s*0\.00%\s*\|\s*[\d.]+ms\s*\|\s*([\d.]+)mb/s\s*\|'

matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

ipv4_list = []
ipv6_list = []

print(f"Raw matches found: {len(matches)}")          # 调试：应该接近 40-50
if matches:
    print("First few matches:", matches[:3])         # 看前几条是否正确捕获

for provider, ip_raw, speed_str in matches:
    ip = ip_raw.strip()
    try:
        speed = float(speed_str)
        if speed < 20:
            continue
    except ValueError:
        continue

    region = random.choice(REGIONS)

    if ':' in ip and ip.count(':') >= 2:  # 简单判断 IPv6
        formatted = f"[{ip}]#{region}|IPV6优选|"
        ipv6_list.append(formatted)
    else:
        formatted = f"{ip}#{region}|IPV4优选|"
        ipv4_list.append(formatted)

# 输出文件
content = f"""# 麒麟 CloudFlare 优选 IP 列表（速度≥20mb/s）
# 更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (每天自动更新)
# 来源：https://api.urlce.com/cloudflare.html
# 当前高速度主要来自电信线路

## IPv4 优选（香港用户优先前几条，延迟最低）
""" + "\n".join(ipv4_list) + """

## IPv6 优选（如果有）
""" + "\n".join(ipv6_list) + """

# 使用方法：复制到 v2rayN / Nekobox / Clash Meta 的优选 IP 列表
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"生成完成！IPv4: {len(ipv4_list)} 条，IPv6: {len(ipv6_list)} 条")
