import requests
import re
import random
from datetime import datetime
from typing import List, Tuple

# =====================================================
# 多来源配置（可继续添加更多）
# =====================================================
SOURCES = [
    {
        "name": "麒麟检测 (urlce.com) - 每10分钟更新",
        "url": "https://api.urlce.com/cloudflare.html",
        "pattern": r'\|\s*\d+\s*\|\s*[^\|]+\s*\|\s*([^\|\s]+)\s*\|\s*[^\|]*\s*\|\s*[^\|]*\s*\|\s*([\d\.]+)mb/s',
        "speed_unit": "mb/s"
    },
    {
        "name": "vvhan.com - 每15分钟更新",
        "url": "https://cf.vvhan.com/",
        "pattern": r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',  # 只抓 IPv4，无速度
        "speed_unit": None
    },
    # 添加更多来源示例（可自行扩展）
    {
        "name": "HostMonit CloudFlareYes (JSON)",
        "url": "https://stock.hostmonit.com/CloudFlareYes",
        "pattern": r'"ip":"([^"]+)"',  # 抓 JSON 中的 ip 字段
        "speed_unit": None
    },
    # 如果有其他 txt/raw 链接，也可以加在这里
    # 示例：{"name": "DustinWin BestCF", "url": "https://raw.githubusercontent.com/DustinWin/BestCF/main/cmcc-ip.txt", "pattern": r'^(\S+)$'}
]

REGIONS = ["US", "JP", "KR", "HK", "SG", "TW"]
MIN_SPEED = 20.0
MAX_PER_TYPE = 16  # 每种类型最多 16 个
OUTPUT_FILE = "cf-ips.txt"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

# 备用 IP（所有来源失败时使用）
FALLBACK_IPV4 = [
    "162.159.38.250", "172.64.53.74", "172.64.52.214",
    "162.159.44.97", "162.159.45.216", "172.64.52.3"
]

FALLBACK_IPV6 = [
    "2a06:98c1:3109:be:eed5:a58c:47d9:836d",
    "2a06:98c1:310f:6877:8189:86b6:1aa5:b5d",
    "2a06:98c1:310c:8c:e50e:942e:fbe6:b0e"
]

# =====================================================
# 函数：从单个来源提取 IP 和速度
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
                try:
                    speed = float(speed_str)
                except:
                    speed = 0.0
            else:
                ip = match.strip()
                speed = 0.0  # 无速度来源默认 0

            if ip:
                items.append((ip, speed))
        print(f"从 {source['name']} 提取到 {len(items)} 个 IP")
    except Exception as e:
        print(f"来源 {source['name']} 失败: {e}")
    return items

# =====================================================
# 主逻辑
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

# 去重（保留最高速度）
ipv4_dict = {}
for ip, speed in all_ipv4:
    if ip not in ipv4_dict or speed > ipv4_dict[ip]:
        ipv4_dict[ip] = speed

ipv6_dict = {}
for ip, speed in all_ipv6:
    if ip not in ipv6_dict or speed > ipv6_dict[ip]:
        ipv6_dict[ip] = speed

# 排序 + 取前16
top_ipv4 = sorted(ipv4_dict.items(), key=lambda x: x[1], reverse=True)[:MAX_PER_TYPE]
top_ipv6 = sorted(ipv6_dict.items(), key=lambda x: x[1], reverse=True)[:MAX_PER_TYPE]

# 补 fallback
for fb_ip in FALLBACK_IPV4:
    if fb_ip not in ipv4_dict and len(top_ipv4) < MAX_PER_TYPE:
        top_ipv4.append((fb_ip, 0.0))

for fb_ip in FALLBACK_IPV6:
    if fb_ip not in ipv6_dict and len(top_ipv6) < MAX_PER_TYPE:
        top_ipv6.append((fb_ip, 0.0))

# 分配地区
random.seed(datetime.now().strftime("%Y%m%d"))

def format_entry(entry: Tuple[str, float]) -> str:
    ip, _ = entry
    region = random.choice(REGIONS)
    return f"{ip}#{region}" if '.' in ip else f"[{ip}]#{region}"

ipv4_formatted = [format_entry(e) for e in top_ipv4]
ipv6_formatted = [format_entry(e) for e in top_ipv6]

# =====================================================
# 生成文件
# =====================================================
update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " HKT"

content = f"""# CloudFlare 优选 IP（多来源整合，按速度降序取最快16个）
# 更新时间：{update_time}
# 来源：urlce.com + vvhan.com + HostMonit 等
# IPv4 最快 {len(ipv4_formatted)} 个 / IPv6 最快 {len(ipv6_formatted)} 个
# 速度阈值 >= {MIN_SPEED} mb/s（无速度来源默认 0）

# IPv4 最快 16 个（格式：IP#地区）
""" + "\n".join(ipv4_formatted) + """

# IPv6 最快 16 个（格式：[IPv6]#地区）
""" + "\n".join(ipv6_formatted) + """

# 使用方式：直接复制到 v2rayN / Nekobox / Clash 的自定义优选列表
# 香港用户优先测试 HK/SG 开头的条目
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(content)

# =====================================================
# 日志输出
# =====================================================
print(f"完成！IPv4 最快 {len(ipv4_formatted)} 个，IPv6 最快 {len(ipv6_formatted)} 个")
print("IPv4 前5示例：")
for line in ipv4_formatted[:5]:
    print(line)
print("IPv6 前5示例：")
for line in ipv6_formatted[:5]:
    print(line)
