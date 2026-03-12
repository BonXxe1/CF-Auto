import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime

# 配置
URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

# 固定随机种子（每天一致）
random.seed(datetime.now().strftime("%Y%m%d"))

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
    print("未找到表格！页面结构变化。")
    exit(1)

rows = table.find_all("tr")[1:]  # 跳过表头
print(f"找到行数: {len(rows)}")

ipv4_list = []
ipv6_list = []
match_count = 0
seen_ips = set()

for row in rows:
    cols = [td.get_text(strip=True) for td in row.find_all("td")]
    if len(cols) < 6:
        continue

    ip = cols[2]
    speed_text = cols[5]

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
        formatted = f"[{ip}]#{region}"
        ipv6_list.append((formatted, speed))
    else:
        formatted = f"{ip}#{region}"
        ipv4_list.append((formatted, speed))

# 按速度降序
ipv4_list.sort(key=lambda x: x[1], reverse=True)
ipv6_list.sort(key=lambda x: x[1], reverse=True)
ipv4_list = [item[0] for item in ipv4_list]
ipv6_list = [item[0] for item in ipv6_list]

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

content = f"""# CloudFlare 优选 IP 列表（速度≥{MIN_SPEED}mb/s）
# 更新时间：{update_time} (香港时间)
# 来源：{URL}
# 有效条目：{match_count}（IPv4 {len(ipv4_list)} / IPv6 {len(ipv6_list)}）

# IPv4 列表（按速度降序，香港延迟低）
""" + "\n".join(ipv4_list) + """

# IPv6 列表
""" + "\n".join(ipv6_list) + """

# 使用：复制到 v2ray/Clash/Nekobox
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"成功！IPv4: {len(ipv4_list)} 条，IPv6: {len(ipv6_list)} 条")
if ipv4_list:
    print("前3 IPv4：\n" + "\n".join(ipv4_list[:3]))
