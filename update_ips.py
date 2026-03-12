import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

URL = "https://api.urlce.com/cloudflare.html"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(URL, headers=headers, timeout=15)
soup = BeautifulSoup(response.text, "html.parser")

# 获取所有文本，方便匹配
text = soup.get_text(separator=" ", strip=True)

# 匹配模式：找包含 IP 和 mb/s 的行
# IP 可能是 数字.数字.数字.数字 或 IPv6 格式
# 速度是 数字.mb/s
lines = text.splitlines()
high_speed_ips = []

for line in lines:
    line = line.strip()
    if not line or '正在加载' in line or '查询' in line:
        continue
    
    # 找速度
    speed_match = re.search(r'([\d.]+)mb/s', line)
    if not speed_match:
        continue
    
    speed = float(speed_match.group(1))
    if speed < 20:
        continue
    
    # 从整行提取 IP（找最像 IP 的部分）
    # IPv4: 四段数字点分隔
    # IPv6: 含 : 的
    ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
    if ip_match:
        ip = ip_match.group(1)
        high_speed_ips.append(ip)
        continue
    
    # IPv6 匹配（更宽松）
    ipv6_match = re.search(r'([0-9a-fA-F:]+:[0-9a-fA-F:]+)', line)
    if ipv6_match:
        ip = ipv6_match.group(1).strip('[]')  # 去掉可能的 []
        high_speed_ips.append(ip)

# 去重 + 排序（可选，按出现顺序）
high_speed_ips = list(dict.fromkeys(high_speed_ips))

# 只输出 IP，一行一个
print("\n".join(high_speed_ips))
