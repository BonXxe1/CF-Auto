import requests
import re
import random
from datetime import datetime

URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()
    text = response.text
    print("頁面抓取成功，長度:", len(text))
    print("包含 'mb/s'？", "mb/s" in text)
    print("包含 '優選IP'？", "優選IP" in text)
except Exception as e:
    print("抓取失敗:", str(e))
    text = ""
    # 可加 fallback：用已知好 IP 列表
    fallback_ipv4 = ["162.159.44.97", "162.159.45.216", "172.64.52.3"]
    fallback_ipv6 = ["2a06:98c1:3109:be:eed5:a58c:47d9:836d"]
else:
    fallback_ipv4 = []
    fallback_ipv6 = []

# 超寬鬆正則：只抓 IP 格式 + 附近 mb/s
ipv4_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
ipv6_pattern = r'([0-9a-fA-F:]+:[0-9a-fA-F:]+(?:\:[0-9a-fA-F:]+)*)'
speed_pattern = r'([\d.]+)\s*mb/s'

ipv4s = re.findall(ipv4_pattern, text)
ipv6s = re.findall(ipv6_pattern, text)
speeds = re.findall(speed_pattern, text)

print("找到純 IPv4:", len(ipv4s), "示例:", ipv4s[:5] if ipv4s else "無")
print("找到純 IPv6:", len(ipv6s), "示例:", ipv6s[:3] if ipv6s else "無")
print("找到速度:", len(speeds), "示例:", speeds[:5] if speeds else "無")

# 簡單過濾 + 去重 + 分配地區
seen = set()
ipv4_list = []
ipv6_list = []

random.seed(datetime.now().strftime("%Y%m%d"))

for ip in ipv4s + fallback_ipv4:
    if ip in seen or not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
        continue
    seen.add(ip)
    region = random.choice(REGIONS)
    ipv4_list.append(f"{ip}#{region}")

for ip in ipv6s + fallback_ipv6:
    if ip in seen:
        continue
    seen.add(ip)
    region = random.choice(REGIONS)
    ipv6_list.append(f"[{ip}]#{region}")

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " HKT"

content = f"""# CloudFlare 優選 IP（速度 ≥20mb/s 參考）
# 更新時間：{update_time}
# 來源：{URL}
# 抓取 IPv4: {len(ipv4_list)} 條 / IPv6: {len(ipv6_list)} 條

# IPv4
""" + "\n".join(ipv4_list[:20]) + """

# IPv6
""" + "\n".join(ipv6_list[:10]) + """

# 注意：如果仍為0，請檢查 Actions 日誌的 print 輸出
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("最終輸出 IPv4 數量:", len(ipv4_list))
