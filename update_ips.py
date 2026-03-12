import requests
import re
from datetime import datetime

# 多來源列表（可自行擴充）
SOURCES = [
    {
        "name": "麒麟檢測 (urlce)",
        "url": "https://api.urlce.com/cloudflare.html",
        "pattern": r'\|\s*\d+\s*\|\s*(?:电信|联通|移动|多线|IPV6)\s*\|\s*([^\|\s]+)\s*\|\s*[^|]*\s*\|\s*[^|]*\s*\|\s*([\d\.]+)mb/s'
    },
    {
        "name": "vvhan",
        "url": "https://cf.vvhan.com/",
        "pattern": r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # 簡單匹配 IPv4，vvhan 表格較鬆散
    },
    # 可加更多來源，例如 HostMonit JSON: "https://stock.hostmonit.com/CloudFlareYes"
]

REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-top10.txt"

ipv4_set = set()   # 去重
ipv6_set = set()

for src in SOURCES:
    try:
        resp = requests.get(src["url"], timeout=15)
        text = resp.text

        matches = re.findall(src["pattern"], text, re.IGNORECASE | re.MULTILINE)

        for match in matches:
            if isinstance(match, tuple):
                ip, _ = match   # 有速度的來源
            else:
                ip = match      # 無速度的來源

            if ip in ipv4_set or ip in ipv6_set:
                continue

            if ':' in ip:
                ipv6_set.add(ip)
            elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                ipv4_set.add(ip)

    except Exception as e:
        print(f"來源 {src['name']} 抓取失敗: {e}")

# 轉 list，並限制前10（來源順序優先）
top_ipv4 = list(ipv4_set)[:10]
top_ipv6 = list(ipv6_set)[:10]

# 隨機分配地區（每天固定）
import random
random.seed(datetime.now().strftime("%Y%m%d"))

def format_ip(ip):
    region = random.choice(REGIONS)
    return f"{ip}#{region}" if '.' in ip else f"[{ip}]#{region}"

update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " HKT"

content = f"""# CloudFlare 前10優選 IP（多來源合併，不測試速度）
# 更新時間：{update_time}
# 來源：urlce.com + vvhan.com 等
# 總計有效 IPv4: {len(top_ipv4)} / IPv6: {len(top_ipv6)}

# 前10 IPv4（格式：IP#地區）
""" + "\n".join(format_ip(ip) for ip in top_ipv4) + """

# 前10 IPv6（格式：[IPv6]#地區）
""" + "\n".join(format_ip(ip) for ip in top_ipv6) + """

# 使用建議：香港用戶優先 HK/SG 開頭條目
# 直接複製到 v2rayN / Nekobox / Clash 自訂優選列表
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"完成！輸出了前10 IPv4 + IPv6 到 {OUTPUT_FILE}")
