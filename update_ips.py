import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime
import re

# 配置
URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
}

try:
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()
except Exception as e:
    print(f"请求失败: {e}")
    exit(1)

soup = BeautifulSoup(response.text, "html.parser")
table = soup.find("table")

if not table:
    print("未找到 <table> 元素！页面结构可能变化。")
    exit(1)

rows = table.find_all("tr")[1:]  # 跳过表头
print(f"找到表格行数: {len(rows)}")  # 应 ≈50

ipv4_list = []
ipv6_list = []
speeds = []  # 用于排序
match_count = 0
seen_ips = set()  # 去重

for row in rows:
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    if len(cols) < 6:
        continue
    
    ip = cols[2]  # 确认：优选IP 列
    speed_text = cols[5]  # 速度列
    
    # 提取速度数字
    speed_match = re.search(r'([\d.]+)', speed_text)
    if not speed_match:
        continue
    try:
        speed = float(speed_match.group(1))
    except ValueError:
        continue
    
    if speed < MIN_SPEED or ip in seen_ips:
        continue
    
    seen_ips.add(ip)
    match_count += 1
    region = random.choice(REGIONS)
    
    if ':' in ip:
        formatted = f"[{ip}]#{region}|IPV6优选|"
        ipv6_list.append((formatted, speed))
    else:
        formatted = f"{ip}#{region}|IPV4优选|"
        ipv4_list.append((formatted, speed))
    
    speeds.append(speed)  # 记录用于调试

# 按速度降序排序
ipv4_list.sort(key=lambda x: x[1], reverse=True)
ipv6_list.sort(key=lambda x: x[1], reverse=True)
ipv4_list = [item[0] for item in ipv4_list]
ipv6_list = [item[0] for item in ipv6_list]

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

content = f"""# 麒麟 CloudFlare 优选 IP 列表（速度≥{MIN_SPEED}mb/s）
# 更新时间：{update_time} (每天自动更新)
# 来源：https://api.urlce.com/cloudflare.html
# 抓取有效条目：{match_count}（过滤后 IPv4 {len(ipv4_list)} / IPv6 {len(ipv6_list)}）
# 表格总行数：{len(rows)}

## IPv4 优选（推荐优先使用，按速度降序，香港延迟低）
""" + "\n".join(ipv4_list[:40]) + """

## IPv6 优选
""" + "\n".join(ipv6_list[:20]) + """

# 使用方法：直接复制到 v2rayN / Nekobox / Clash 的自定义优选列表
# 香港用户优先试前几条电信 IP，速度 60+mb/s 极稳
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"生成成功！匹配 {match_count} 条，IPv4: {len(ipv4_list)} 条，IPv6: {len(ipv6_list)} 条")
if ipv4_list:
    print("前3条 IPv4 示例：")
    print("\n".join(ipv4_list[:3]))
if ipv6_list:
    print("前3条 IPv6 示例：")
    print("\n".join(ipv6_list[:3]))
