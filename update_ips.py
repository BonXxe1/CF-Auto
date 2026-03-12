import requests
import re
import random
from datetime import datetime

# =====================================================
# 設定區
# =====================================================
URL = "https://api.urlce.com/cloudflare.html"
REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
OUTPUT_FILE = "cf-ips.txt"
MIN_SPEED = 20.0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

# 當請求失敗時的備用 IP（可自行增減）
FALLBACK_IPV4 = [
    "162.159.38.250",
    "172.64.53.74",
    "172.64.52.214",
    "162.159.44.97",
    "162.159.45.216"
]

FALLBACK_IPV6 = [
    "2a06:98c1:3109:be:eed5:a58c:47d9:836d",
    "2a06:98c1:310f:6877:8189:86b6:1aa5:b5d",
    "2a06:98c1:310c:8c:e50e:942e:fbe6:b0e"
]

# =====================================================
# 主程式
# =====================================================
text = ""

try:
    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()
    text = response.text

    print("頁面抓取成功，長度:", len(text))
    print("包含 'mb/s'？", "mb/s" in text)
    print("包含 '優選IP'？", "優選IP" in text)
    print("包含 '电信'？", "电信" in text)

except Exception as e:
    print("抓取失敗:", str(e))
    print("使用 fallback IP 清單")

# =====================================================
# 正則：完整行匹配（最可靠方式）
# 格式：| 數字 | 线路 | IP | 丟包 | 延迟 | 速度mb/s | ...
# =====================================================
pattern = r'\|\s*\d+\s*\|\s*[^\|]+\s*\|\s*([^\|\s]+)\s*\|\s*[^\|]*\s*\|\s*[^\|]*\s*\|\s*([\d\.]+)mb/s'

matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)

print("匹配到的有效行數:", len(matches))

if matches and len(matches) > 0:
    print("前 3 筆匹配結果 (IP, 速度):")
    for item in matches[:3]:
        print(item)

# =====================================================
# 處理結果
# =====================================================
ipv4_list = []
ipv6_list = []
seen = set()

random.seed(datetime.now().strftime("%Y%m%d"))

for ip, speed_str in matches:
    try:
        speed = float(speed_str)
        if speed < MIN_SPEED or ip in seen:
            continue

        seen.add(ip)
        region = random.choice(REGIONS)

        if ':' in ip and ip.count(':') >= 5:  # 加強過濾，避免誤抓時間戳
            ipv6_list.append(f"[{ip}]#{region}")
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            ipv4_list.append(f"{ip}#{region}")

    except ValueError:
        continue

# 加入 fallback（當完全抓不到時至少有東西）
for ip in FALLBACK_IPV4:
    if ip not in seen:
        seen.add(ip)
        region = random.choice(REGIONS)
        ipv4_list.append(f"{ip}#{region}")

for ip in FALLBACK_IPV6:
    if ip not in seen:
        seen.add(ip)
        region = random.choice(REGIONS)
        ipv6_list.append(f"[{ip}]#{region}")

# =====================================================
# 產生檔案內容
# =====================================================
update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " HKT"

content = f"""# CloudFlare 優選 IP（速度 ≥ {MIN_SPEED} mb/s）
# 更新時間：{update_time}
# 來源：{URL}
# 抓取有效條目：IPv4 {len(ipv4_list)} 條 / IPv6 {len(ipv6_list)} 條
#
# 注意：如果數量為 0，請檢查 Actions 日誌的匹配行數與示例

# IPv4
""" + "\n".join(ipv4_list[:40]) + """

# IPv6
""" + "\n".join(ipv6_list[:20]) + """

# 使用方式：直接複製到 v2rayN / Nekobox / Clash 自訂優選列表
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

# =====================================================
# 最後輸出 debug 資訊
# =====================================================
print("\n" + "="*50)
print("最終輸出結果：")
print("IPv4 數量:", len(ipv4_list))
print("IPv6 數量:", len(ipv6_list))

if ipv4_list:
    print("前 5 條 IPv4：")
    for line in ipv4_list[:5]:
        print(line)

if ipv6_list:
    print("前 5 條 IPv6：")
    for line in ipv6_list[:5]:
        print(line)
