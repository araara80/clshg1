import requests
import base64
import re
import json
import urllib.parse

# لینک raw کانفیگ‌ها
RAW_URL = "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/grpc.txt"

# قالب ثابت Clash
TEMPLATE_FILE = "template.json"
# خروجی نهایی
OUTPUT_FILE = "clash.json"

def fetch_raw_text(url):
    """دریافت محتوا از لینک و تلاش برای decode اگر Base64 باشد"""
    print(f"📥 دریافت از {url}")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    text = resp.text.strip()
    try:
        decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
        return decoded
    except Exception:
        return text

def parse_vless_lines(raw_text):
    """فقط خطوط vless:// با type=grpc"""
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    filtered = [l for l in lines if l.lower().startswith("vless://") and "type=grpc" in l.lower()]
    print(f"✅ {len(filtered)} لینک vless یافت شد")
    return filtered

def extract_params(vless_url):
    """استخراج پارامترها از لینک vless"""
    head, *query_parts = vless_url.split("?", 1)
    query = query_parts[0] if query_parts else ""
    query, *_ = query.split("#", 1)

    m = re.match(r"vless://([^@]+)@([^:]+):(\d+)", head)
    if not m:
        return None
    uuid = m.group(1)
    server = m.group(2)
    port = int(m.group(3))

    params = {}
    for kv in query.split("&"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.lower()] = urllib.parse.unquote(v)

    return {
        "uuid": uuid,
        "server": server,
        "port": port,
        "security": params.get("security", ""),  # tls یا none
        "sni": params.get("sni", ""),
        "flow": params.get("flow", ""),
        "fp": params.get("fp", "chrome"),
        "servicename": params.get("servicename", params.get("host", "")),
        "mode": params.get("mode", "gun"),
        "alpn": params.get("alpn", "")
    }

def build_proxy(entry, idx):
    """ساخت پروکسی Clash بر اساس پارامترها"""
    # alpn لیستی
    if entry["alpn"]:
        alpn_list = [a.strip() for a in entry["alpn"].replace(",", " ").split() if a.strip()]
    else:
        # اگر alpn نبود، مقدار پیش‌فرض
        alpn_list = ["h2", "http/1.1"]

    # تشخیص TLS فعال یا نه
    tls_enabled = entry["security"].lower() == "tls"

    proxy = {
        "name": f"ARISTA🔥-{idx}",
        "type": "vless",
        "server": entry["server"],
        "port": entry["port"],
        "uuid": entry["uuid"],
        "network": "grpc",
        "tls": tls_enabled,
        "udp": True,
        "skip-cert-verify": False,
        "tcp-fast-open": True,
        "fast-open": True,
        "servername": entry["sni"] or entry["server"],
        "flow": entry["flow"],
        "client-fingerprint": entry["fp"],
        "packet-encoding": "xudp",
        "alpn": alpn_list,
        "grpc-opts": {
            "grpc-service-name": entry["servicename"] or entry["sni"] or entry["server"],
            "grpc-mode": entry["mode"] or "gun"
        }
    }

    return proxy

def main():
    raw = fetch_raw_text(RAW_URL)
    vless_list = parse_vless_lines(raw)

    proxies = []
    for i, link in enumerate(vless_list, start=1):
        params = extract_params(link)
        if params:
            proxies.append(build_proxy(params, i))

    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = json.load(f)

    template["proxies"] = proxies

    # افزودن نام‌ها به گروه‌ها
    names = [p["name"] for p in proxies]
    for group in template.get("proxy-groups", []):
        # اگر گروه شامل لیست پروکسی است، آن را با names بروزرسانی کن
        if "proxies" in group:
            group["proxies"] = names

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"✅ ساخته شد {OUTPUT_FILE} با {len(proxies)} پروکسی")

if __name__ == "__main__":
    main()
