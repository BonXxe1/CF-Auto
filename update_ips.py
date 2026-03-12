import requests
import re
import random
from datetime import datetime

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
    text = response.text
except Exception as e:
    print(f"請求失敗: {e}")
    exit(1)

# 正則匹配表格行（兼容 Markdown 表格格式）
# 捕獲：行號 | 线路 | IP | 丟包 | 延迟 | 速度mb/s | ...
pattern = r'\|\s*\d+\s*\|\s*(电信|联通|移动|多线|IPV6)\s*\|\s*([^\s|]+)\s*\|\s*[^|]+\s*\|\s*[^|]+\s*\|\s*([\d.]+)mb/s'

matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

ipv4 = []
ipv6 = []
seen = set()

random.seed(datetime.now().strftime("%Y%m%d"))

for _, _, ip, speed_str in matches:
    try:
        speed = float(speed_str)
        if speed < MIN_SPEED or ip in seen:
            continue
        seen.add(ip)
        region = random.choice(REGIONS)
        if ':' in ip:
            ipv6.append(f"[{ip}]#{region}")
        else:
            ipv4.append(f"{ip}#{region}")
    except ValueError:
        continue

# 簡單排序（可選，按原頁面順序或隨機）
# ipv4 = sorted(ipv4)  # 如果想字母序

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " HKT"

content = f"""# CloudFlare 優選 IP（速度 ≥ {MIN_SPEED}mb/s）
# 更新時間：{update_time}
# 來源：{URL}
# 總有效數量：IPv4 {len(ipv4)} / IPv6 {len(ipv6)}

# IPv4（推薦優先使用，格式：IP#地區）
""" + "\n".join(ipv4) + """

# IPv6（格式：[IPv6]#地區）
""" + "\n".join(ipv6) + """

# 使用方式：直接複製到 v2rayN / Nekobox / Clash 的自訂優選列表
# 香港用戶建議優先測試 HK/SG 開頭的條目，延迟通常最低
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"完成！IPv4: {len(ipv4)} 條，IPv6: {len(ipv6)} 條")
if ipv4:
    print("前5條 IPv4 示例：")
    print("\n".join(ipv4[:5]))
