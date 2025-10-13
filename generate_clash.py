import requests
import base64
import re
import json

RAW_URL = "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/grpc.txt"

# اسکلت پیش‌فرض Clash که دادی
CLASH_TEMPLATE = {
  "port": 7890,
  "socks-port": 7891,
  "mixed-port": 7893,
  "mode": "rule",
  "log-level": "info",
  "dns": {
    "enable": True,
    "listen": ":53",
    "enhanced-mode": "fake-ip",
    "fake-ip-range": "198.18.0.1/16",
    "fake-ip-filter": [
      "*.lan",
      "*.local",
      "*.localhost",
      "*.ir",
      "*.test"
    ],
    "nameserver": [
      "78.157.42.100",
      "78.157.42.101",
      "10.202.10.10",
      "8.8.8.8",
      "1.1.1.1"
    ],
    "fallback": [
      "10.202.10.11",
      "78.157.42.100",
      "8.8.4.4"
    ],
    "fallback-filter": {
      "geoip": True,
      "geoip-code": "IR",
      "ipcidr": [
        "0.0.0.0/8",
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16"
      ]
    }
  },
  "proxies": [],
  "proxy-groups": [],  # این بخش بعداً هم اضافه می‌کنیم
  "rules": [
    "DOMAIN-SUFFIX,google.com,ARISTA Auto",
    "DOMAIN-SUFFIX,youtube.com,ARISTA Auto",
    "DOMAIN-SUFFIX,github.com,ARISTA Auto",
    "DOMAIN-KEYWORD,telegram,ARISTA Auto",
    "DOMAIN-SUFFIX,instagram.com,ARISTA Auto",
    "DOMAIN-SUFFIX,twitter.com,ARISTA Auto",
    "DOMAIN-SUFFIX,whatsapp.com,ARISTA Auto",
    "DOMAIN-SUFFIX,cdn.ir,DIRECT",
    "DOMAIN-SUFFIX,aparat.com,DIRECT",
    "DOMAIN-SUFFIX,digikala.com,DIRECT",
    "DOMAIN-SUFFIX,divar.ir,DIRECT",
    "DOMAIN-SUFFIX,snapp.ir,DIRECT",
    "DOMAIN-SUFFIX,torob.com,DIRECT",
    "DOMAIN-SUFFIX,bamilo.com,DIRECT",
    "DOMAIN-SUFFIX,alibaba.ir,DIRECT",
    "DOMAIN-SUFFIX,ban.ir,DIRECT",
    "GEOIP,IR,DIRECT",
    "MATCH,ARISTA Auto"
  ]
}

def fetch_raw():
    resp = requests.get(RAW_URL, timeout=10)
    resp.raise_for_status()
    text = resp.text.strip()
    # اگر متن Base64 باشه، تلاش به decode
    try:
        decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
        return decoded
    except Exception:
        return text

def parse_vless_lines(raw_text):
    lines = raw_text.splitlines()
    # فقط خطوطی که vless:// و type=grpc دارند
    filtered = [
        line for line in lines
        if line.lower().startswith("vless://") and "type=grpc" in line.lower()
    ]
    return filtered

def extract_params(vless_url):
    """
    از لینک vless:// پارامترهای لازم را برمی‌دارد:
    server, port, uuid, tls, servername, flow, grpc-service-name و ... 
    """
    # Pattern ساده‌تر برای گرفتن بخش before ? و بخش query بعدش
    # ساختار ممکن: vless://UUID@host:port?key1=val1&key2=val2#tag
    parts = re.split(r"\?", vless_url, maxsplit=1)
    head = parts[0]
    query = parts[1] if len(parts) > 1 else ""
    # جدا کردن بخش fragment (بعد #)
    query, *_ = query.split("#", 1)
    # parse head: vless://UUID@host:port
    m = re.match(r"vless://([^@]+)@([^:]+):([0-9]+)", head)
    if not m:
        return None
    uuid, server, port = m.group(1), m.group(2), int(m.group(3))

    # parse query parameters
    params = {}
    for kv in query.split("&"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.lower()] = v

    # جمع کردن همه چیز در دیکشنری
    d = {
        "type": "vless",
        "server": server,
        "port": port,
        "uuid": uuid,
        "network": params.get("network", "grpc"),
        "tls": params.get("tls", "false").lower() in ("true", "1", "yes"),
        "servername": params.get("sni", server),
        "flow": params.get("flow", ""),
        # grpc opts
        "grpc-opts": {
            "grpc-service-name": params.get("serviceName", ""),
            "grpc-mode": params.get("mode", "gun")
        }
    }
    return d

def build_proxies(vless_list):
    proxies = []
    for i, url in enumerate(vless_list, 1):
        p = extract_params(url)
        if not p:
            continue
        # اضافه کردن فیلدهایی که قالب داده بودی
        proxy = {
            "name": f"ALRZ☃️-{i}",
            "type": "vless",
            "server": p["server"],
            "port": p["port"],
            "uuid": p["uuid"],
            "network": "grpc",
            "tls": p["tls"],
            "udp": True,
            "skip-cert-verify": False,
            "tcp-fast-open": True,
            "fast-open": True,
            "servername": p["servername"],
            "flow": p["flow"],
            "client-fingerprint": "chrome",
            "packet-encoding": "xudp",
            "alpn": ["h2", "http/1.1"],
            "grpc-opts": {
                "grpc-service-name": p["grpc-opts"]["grpc-service-name"],
                "grpc-mode": p["grpc-opts"]["grpc-mode"]
            }
        }
        proxies.append(proxy)
    return proxies

def main():
    raw = fetch_raw()
    vless_urls = parse_vless_lines(raw)
    proxies = build_proxies(vless_urls)

    # پر کردن بخش proxies در قالب
    result = CLASH_TEMPLATE.copy()
    result["proxies"] = proxies

    # می‌تونی اینجا بخش proxy-groups رو هم به دلخواه اضافه کنی
    # مثلاً همان proxy-groups که قبلاً داشتی:
    result["proxy-groups"] = [
        {
            "name": "ARISTA Select",
            "type": "select",
            "proxies": [p["name"] for p in proxies],
            "disable-udp": False
        },
        {
            "name": "ARISTA Auto",
            "type": "url-test",
            "proxies": [p["name"] for p in proxies],
            "url": "http://www.gstatic.com/generate_204",
            "interval": 120,
            "tolerance": 50,
            "lazy": True,
            "disable-udp": False
        },
        {
            "name": "ARISTA Fallback",
            "type": "fallback",
            "proxies": [p["name"] for p in proxies],
            "url": "http://www.gstatic.com/generate_204",
            "interval": 120,
            "tolerance": 100,
            "disable-udp": False
        },
        {
            "name": "ARISTA Load Balance",
            "type": "load-balance",
            "proxies": [p["name"] for p in proxies],
            "url": "http://www.gstatic.com/generate_204",
            "interval": 300,
            "strategy": "consistent-hashing",
            "disable-udp": False
        }
    ]

    # خروجی به صورت فایل JSON
    with open("clash.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ فایل clash.json با {len(proxies)} پروکسی ساخته شد.")

if __name__ == "__main__":
    main()
