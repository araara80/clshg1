import requests
import base64
import re
import json

# 🔗 لینک فایل کانفیگ‌های gRPC
RAW_URL = "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/grpc.txt"

# 📁 فایل قالب ثابت (template.json)
TEMPLATE_FILE = "template.json"

# 📤 فایل خروجی نهایی
OUTPUT_FILE = "clash.json"


def fetch_raw_text(url):
    """دریافت محتوای لینک و تلاش برای decode در صورت Base64 بودن"""
    print(f"📥 در حال دریافت کانفیگ‌ها از {url} ...")
    resp = requests.get(url, timeout=20)
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
    """استخراج مقادیر از لینک vless://"""
    parts = re.split(r"\?", vless_url, maxsplit=1)
    head = parts[0]
    query = parts[1] if len(parts) > 1 else ""
    query, *_ = query.split("#", 1)

    m = re.match(r"vless://([^@]+)@([^:]+):([0-9]+)", head)
    if not m:
        return None

    uuid, server, port = m.group(1), m.group(2), int(m.group(3))

    params = {}
    for kv in query.split("&"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.lower()] = v

    return {
        "uuid": uuid,
        "server": server,
        "port": port,
        "security": params.get("security", ""),
        "sni": params.get("sni", ""),
        "flow": params.get("flow", ""),
        "fp": params.get("fp", ""),
        "host": params.get("host", ""),
        "serviceName": params.get("servicename", ""),
        "alpn": params.get("alpn", "")
    }


def build_proxy(entry, index):
    """ساخت پروکسی بر اساس قوانین کاربر"""

    # 🔹 TLS بر اساس security
    security = entry.get("security", "").lower()
    tls_enabled = False if (not security or security == "none") else True

    # 🔹 ALPN فقط اگر تعریف شده
    alpn_values = None
    if entry.get("alpn"):
        alpn_values = [v.strip() for v in entry["alpn"].split(",") if v.strip()]

    # 🔹 grpc-service-name (host یا serviceName یا پیش‌فرض GunService)
    grpc_name = entry.get("host") or entry.get("serviceName") or "GunService"

    # 🔹 client fingerprint
    fingerprint = entry.get("fp") or "chrome"

    # 🔹 servername از sni
    servername = entry.get("sni", "")

    # 🔹 flow
    flow = entry.get("flow", "")

    # 🔹 ساخت پروکسی نهایی
    proxy = {
        "name": f"ALRZ☃️-{index}",
        "type": "vless",
        "server": entry.get("server", ""),
        "port": entry.get("port", 0),
        "uuid": entry.get("uuid", ""),
        "network": "grpc",
        "tls": tls_enabled,

        # مقادیر ثابت
        "udp": True,
        "skip-cert-verify": False,
        "tcp-fast-open": True,
        "fast-open": True,

        "servername": servername,
        "flow": flow,
        "client-fingerprint": fingerprint,
        "packet-encoding": "xudp",

        "grpc-opts": {
            "grpc-service-name": grpc_name,
            "grpc-mode": "gun"
        }
    }

    # فقط اگر alpn وجود داشته باشد، اضافه شود
    if alpn_values:
        proxy["alpn"] = alpn_values

    return proxy


def main():
    # دریافت داده‌ها
    raw_text = fetch_raw_text(RAW_URL)
    vless_lines = parse_vless_lines(raw_text)

    proxies = []
    for i, vless in enumerate(vless_lines, 1):
        info = extract_params(vless)
        if info:
            proxies.append(build_proxy(info, i))

    print(f"⚙️ در حال بارگذاری template.json ...")
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = json.load(f)

    # جایگذاری پروکسی‌ها در قالب
    template["proxies"] = proxies

    # افزودن نام پروکسی‌ها به گروه‌های Auto / Fallback / Load Balance
    proxy_names = [p["name"] for p in proxies]
    for group in template.get("proxy-groups", []):
        if group["name"] in ["Auto", "Fallback", "Load Balance"]:
            group["proxies"] = proxy_names

    # ذخیره خروجی
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"✅ فایل '{OUTPUT_FILE}' با {len(proxies)} پروکسی ساخته شد.")


if __name__ == "__main__":
    main()
