import requests
import re
import random
from datetime import datetime
from typing import List, Tuple

# =====================================================
# 多來源配置（已加入所有提到的网址）
# =====================================================
SOURCES = [
    {
        "name": "麒麟檢測 - urlce.com",
        "url": "https://api.urlce.com/cloudflare.html",
        "pattern": r'\|\s*\d+\s*\|\s*[^\|]+\s*\|\s*([^\|\s]+)\s*\|\s*[^\|]*\s*\|\s*[^\|]*\s*\|\s*([\d\.]+)mb/s',
        "speed_unit": "mb/s"
    },
    {
        "name": "uouin.com 替代域名",
        "url": "https://api.uouin.com/cloudflare.html",
        "pattern": r'\|\s*\d+\s*\|\s*[^\|]+\s*\|\s*([^\|\s]+)\s*\|\s*[^\|]*\s*\|\s*[^\|]*\s*\|\s*([\d\.]+)mb/s',
        "speed_unit": "mb/s"
    },
    {
        "name": "vvhan.com",
        "url": "https://cf.vvhan.com/",
        "pattern": r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
        "speed_unit": None
    },
    {
        "name": "WeTest IPv4",
        "url": "https://www.wetest.vip/page/cloudflare/address_v4.html",
        "pattern": r'優選地址</td>\s*<td>([\d\.]+)</td>',
        "speed_unit": None
    },
    {
        "name": "WeTest IPv6",
        "url": "https://www.wetest.vip/page/cloudflare/address_v6.html",
        "pattern": r'優選地址</td>\s*<td>([0-9a-fA-F:]+)</td>',
        "speed_unit": None
    },
    {
        "name": "HostMonit CloudFlareYes JSON",
        "url": "https://stock.hostmonit.com/CloudFlareYes",
        "pattern": r'"IP":"([^"]+)"',
        "speed_unit": None
    },
    {
        "name": "164746.xyz 自選優選",
        "url": "https://ip.164746.xyz/",
        "pattern": r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
        "speed_unit": None
    },
    {
        "name": "IPDB api cfv4",
        "url": "https://ipdb.api.030101.xyz/cfv4",
        "pattern": r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
        "speed_unit": None
    },
    {
        "name": "IPDB api cfv6",
        "url": "https://ipdb.api.030101.xyz/cfv6",
        "pattern": r'([0-9a-fA-F:]+)',
        "speed_unit": None
    },
]

REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
MIN_SPEED = 20.0
MAX_PER_TYPE = 16
OUTPUT_FILE = "cf-ips.txt"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

FALLBACK_IPV4 = ["162.159.38.250", "172.64.53.74", "172.64.52.214", "162.159.44.97"]
FALLBACK_IPV6 = ["2a06:98c1:3109:be:eed5:a58c:47d9:836d", "2a06:98c1:310f:6877:8189:86b6:1aa5:b5d"]

# =====================================================
# 提取函數
# =====================================================
def extract_from_source(source: dict) -> List[Tuple[str, float]]:
    items = []
    try:
        resp = requests.get(source["url"], headers=headers, timeout=20)
        resp.raise_for_status()
        text = resp.text
        matches = re.findall(source["pattern"], text, re.IGNORECASE | re.MULTILINE)

        for match in matches:
            if isinstance(match, tuple):
                ip, speed_str = match
                speed = float(speed_str) if speed_str.replace('.', '', 1).isdigit() else 0.0
            else:
                ip = match.strip()
                speed = 0.0

            if ip:
                items.append((ip, speed))
        print(f"從 {source['name']} 提取到 {len(items)} 個 IP")
    except Exception as e:
        print(f"來源 {source['name']} 失敗: {e}")
    return items

# =====================================================
# 主邏輯
# =====================================================
all_ipv4: List[Tuple[str, float]] = []
all_ipv6: List[Tuple[str, float]] = []

for src in SOURCES:
    items = extract_from_source(src)
    for ip, speed in items:
        if ':' in ip:
            all_ipv6.append((ip, speed))
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            all_ipv4.append((ip, speed))

# 去重 + 保留最高速度
ipv4_dict = {}
for ip, speed in all_ipv4:
    if ip not in ipv4_dict or speed > ipv4_dict[ip]:
        ipv4_dict[ip] = speed

ipv6_dict = {}
for ip, speed in all_ipv6:
    if ip not in ipv6_dict or speed > ipv6_dict[ip]:
        ipv6_dict[ip] = speed

# 排序取前16
top_ipv4 = sorted(ipv4_dict.items(), key=lambda x: x[1], reverse=True)[:MAX_PER_TYPE]
top_ipv6 = sorted(ipv6_dict.items(), key=lambda x: x[1], reverse=True)[:MAX_PER_TYPE]

# 補 fallback
for fb_ip in FALLBACK_IPV4:
    if fb_ip not in ipv4_dict and len(top_ipv4) < MAX_PER_TYPE:
        top_ipv4.append((fb_ip, 0.0))

for fb_ip in FALLBACK_IPV6:
    if fb_ip not in ipv6_dict and len(top_ipv6) < MAX_PER_TYPE:
        top_ipv6.append((fb_ip, 0.0))

# 分配地區 + 格式化為指定格式
random.seed(datetime.now().strftime("%Y%m%d"))

def format_entry(entry: Tuple[str, float], is_ipv4: bool) -> str:
    ip, _ = entry
    region = random.choice(REGIONS)
    suffix = "|IPV4优选|" if is_ipv4 else "|IPV6优选|"
    if is_ipv4:
        return f"{ip}#{region}{suffix}"
    else:
        return f"[{ip}]#{region}{suffix}"

ipv4_formatted = [format_entry(e, True) for e in top_ipv4]
ipv6_formatted = [format_entry(e, False) for e in top_ipv6]

# =====================================================
# 生成文件
# =====================================================
update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " HKT"

content = f"""# CloudFlare 優選 IP（多來源整合，按速度降序取最快16個）
# 更新時間：{update_time}
# 來源：urlce.com、uouin.com、vvhan.com、wetest.vip、hostmonit.com、164746.xyz、ipdb.api.030101.xyz 等
# IPv4 最快 {len(ipv4_formatted)} 個 / IPv6 最快 {len(ipv6_formatted)} 個
# 速度閾值 >= {MIN_SPEED} mb/s（無速度來源默認 0）

# IPv4 最快 16 個
""" + "\n".join(ipv4_formatted) + """

# IPv6 最快 16 個
""" + "\n".join(ipv6_formatted) + """

# 使用方式：直接複製到 v2rayN / Nekobox / Clash 的自訂優選列表
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

# 日誌輸出
print(f"完成！IPv4 最快 {len(ipv4_formatted)} 個，IPv6 最快 {len(ipv6_formatted)} 個")
print("IPv4 前5示例：")
for line in ipv4_formatted[:5]:
    print(line)
print("\nIPv6 前5示例：")
for line in ipv6_formatted[:5]:
    print(line)
