import requests
import base64
import re
import json
import copy

# لینک کانفیگ‌ها
RAW_URL = "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/grpc.txt"

# مسیر فایل قالب
TEMPLATE_FILE = "template.json"
# خروجی نهایی
OUTPUT_FILE = "clash.json"


def fetch_raw_text(url):
    """دریافت محتوای لینک و تلاش برای decode در صورت Base64 بودن"""
    print(f"📥 در حال دریافت کانفیگ‌ها از {url} ...")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.text.strip()

    # اگر متن Base64 بود decode کن
    try:
        decoded = base64.b64decode(data).decode("utf-8", errors="ignore")
        return decoded
    except Exception:
        return data


def parse_vless_lines(raw_text):
    """فقط خطوط vless:// که type=grpc دارند"""
    lines = raw_text.splitlines()
    vless_list = [
        line.strip()
        for line in lines
        if line.lower().startswith("vless://") and "type=grpc" in line.lower()
    ]
    print(f"✅ {len(vless_list)} کانفیگ gRPC پیدا شد.")
    return vless_list


def extract_params(vless_url):
    """استخراج اطلاعات از لینک VLESS"""
    parts = re.split(r"\?", vless_url, maxsplit=1)
    head = parts[0]
    query = parts[1] if len(parts) > 1 else ""
    query, *_ = query.split("#", 1)

    match = re.match(r"vless://([^@]+)@([^:]+):([0-9]+)", head)
    if not match:
        return None

    uuid, server, port = match.group(1), match.group(2), int(match.group(3))

    params = {}
    for kv in query.split("&"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.lower()] = v

    return {
        "uuid": uuid,
        "server": server,
        "port": port,
        "type": "vless",
        "network": params.get("type", "grpc"),
        "security": params.get("security", ""),
        "sni": params.get("sni", ""),
        "flow": params.get("flow", ""),
        "service_name": params.get("servicename", ""),
        "grpc_mode": params.get("mode", "")
    }


def build_proxy(entry, index):
    """ساختن شیء پروکسی Clash با مقادیر واقعی یا خالی"""
    return {
        "name": f"ALRZ☃️-{index}",
        "type": "vless",
        "server": entry.get("server", ""),
        "port": entry.get("port", 0),
        "uuid": entry.get("uuid", ""),
        "network": entry.get("network", "grpc"),
        "tls": entry.get("security", "").lower() in ("tls", "reality"),
        "udp": True,
        "skip-cert-verify": False,
        "tcp-fast-open": True,
        "fast-open": True,
        "servername": entry.get("sni", ""),
        "flow": entry.get("flow", ""),
        "client-fingerprint": "",
        "packet-encoding": "",
        "alpn": [],
        "grpc-opts": {
            "grpc-service-name": entry.get("service_name", ""),
            "grpc-mode": entry.get("grpc_mode", "")
        }
    }


def main():
    # دریافت داده‌ها
    raw_text = fetch_raw_text(RAW_URL)
    vless_lines = parse_vless_lines(raw_text)

    # استخراج پارامترها
    proxies = []
    for i, vless in enumerate(vless_lines, 1):
        info = extract_params(vless)
        if info:
            proxies.append(build_proxy(info, i))

    print(f"⚙️ در حال بارگذاری template.json ...")
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = json.load(f)

    # پر کردن لیست proxies
    template["proxies"] = proxies

    # افزودن نام پروکسی‌ها به گروه‌ها
    proxy_names = [p["name"] for p in proxies]
    for group in template["proxy-groups"]:
        if "proxies" in group:
            # فقط اضافه می‌کنیم اگر گروه نوعی مثل Auto یا Fallback باشد
            if group["name"] in ["Auto", "Fallback", "Load Balance"]:
                group["proxies"] = proxy_names

    # نوشتن خروجی clash.json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"✅ فایل نهایی '{OUTPUT_FILE}' با {len(proxies)} پروکسی ساخته شد.")


if __name__ == "__main__":
    main()
