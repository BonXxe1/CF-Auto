import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime

# ================== 配置 ==================
URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
# ========================================

random.seed(datetime.now().strftime("%Y%m%d"))

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
response = requests.get(URL, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, "html.parser")
text = soup.get_text(separator="\n", strip=True)  # 更好处理换行

# 更新后的正则：更灵活匹配列，捕获 IP 和 速度
# 匹配： | 数字 | 线路 | IP | ... | 速度mb/s |
pattern = r'\|\s*\d+\s*\|\s*(电信|联通|移动|多线|IPV6)\s*\|\s*([\d\.\:a-fA-F]+)\s*\|\s*[^|]*\|\s*[^|]*\|\s*([\d\.]+)mb/s\s*\|'

matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

ipv4_list = []
ipv6_list = []

print(f"抓取到匹配条目数: {len(matches)}")  # 调试：日志里可见

for line_type, ip, speed_str in matches:
    try:
        speed = float(speed_str)
        if speed < 20:
            continue
    except ValueError:
        continue

    region = random.choice(REGIONS)

    if ':' in ip:  # IPv6
        formatted = f"[{ip}]#{region}|IPV6优选|"
        ipv6_list.append(formatted)
    else:
        formatted = f"{ip}#{region}|IPV4优选|"
        ipv4_list.append(formatted)

# 排序：按速度降序（可选，更好用）
ipv4_list.sort(key=lambda x: float(re.search(r'(\d+\.?\d*)', x).group(1)) if re.search(r'(\d+\.?\d*)', x) else 0, reverse=True)
ipv6_list.sort(key=lambda x: float(re.search(r'(\d+\.?\d*)', x).group(1)) if re.search(r'(\d+\.?\d*)', x) else 0, reverse=True)

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

content = f"""# 麒麟 CloudFlare 优选 IP 列表（速度≥20mb/s）
# 更新时间：{update_time} (每天自动更新)
# 来源：https://api.urlce.com/cloudflare.html
# 抓取匹配条目：{len(matches)}，过滤后有效：IPv4 {len(ipv4_list)} / IPv6 {len(ipv6_list)}

## IPv4 优选（推荐优先使用）
""" + "\n".join(ipv4_list[:30]) + """  # 限制前30条，避免文件过长

## IPv6 优选
""" + "\n".join(ipv6_list[:20]) + """

# 使用方法：直接复制到 v2rayN / Nekobox / Clash 的自定义优选列表即可
# 如需完整列表或调整过滤，查看仓库 Actions 日志
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"生成成功！IPv4: {len(ipv4_list)} 条，IPv6: {len(ipv6_list)} 条")
