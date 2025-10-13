import requests
import base64
import re
import json
import urllib.parse

# 🔗 لینک فایل کانفیگ‌ها (raw)
RAW_URL = "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/grpc.txt"

# 📄 فایل قالب (template.json)
TEMPLATE_FILE = "template.json"

# 📤 خروجی نهایی
OUTPUT_FILE = "clash.json"


def fetch_raw_text(url):
    """دریافت محتوای لینک و دیکد درصورت Base64"""
    print(f"📥 دریافت کانفیگ‌ها از {url} ...")
    res = requests.get(url, timeout=20)
    res.raise_for_status()
    text = res.text.strip()
    try:
        return base64.b64decode(text).decode("utf-8", errors="ignore")
    except Exception:
        return text


def parse_vless_lines(raw):
    """انتخاب فقط خطوط VLESS که type=grpc دارند"""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    vless_list = [
        l for l in lines if l.lower().startswith("vless://") and "type=grpc" in l.lower()
    ]
    print(f"✅ {len(vless_list)} لینک VLESS (gRPC) پیدا شد.")
    return vless_list


def extract_params(vless_url):
    """استخراج پارامترها از لینک VLESS"""
    head, *query_parts = vless_url.split("?", 1)
    query = query_parts[0] if query_parts else ""
    query, *_ = query.split("#", 1)

    m = re.match(r"vless://([^@]+)@([^:]+):(\d+)", head)
    if not m:
        return None

    uuid, server, port = m.group(1), m.group(2), int(m.group(3))
    params = {}
    for kv in query.split("&"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            params[k.lower()] = urllib.parse.unquote(v)

    return {
        "uuid": uuid,
        "server": server,
        "port": port,
        "security": params.get("security", ""),
        "sni": params.get("sni", ""),
        "flow": params.get("flow", ""),
        "fp": params.get("fp", "chrome"),
        "pbk": params.get("pbk", ""),
        "sid": params.get("sid", ""),
        "servicename": params.get("servicename", params.get("host", "")),
        "mode": params.get("mode", "gun"),
        "alpn": params.get("alpn", ""),
    }


def build_proxy(entry, index):
    """ساختن یک شیء پروکسی مطابق فرمت Clash"""
    alpn_list = []
    if entry["alpn"]:
        alpn_list = [a.strip() for a in entry["alpn"].replace(",", " ").split() if a.strip()]
    else:
        alpn_list = ["h2", "http/1.1"]

    # مقدار tls
    tls_enabled = entry["security"].lower() in ("tls", "reality")

    proxy = {
        "name": f"ARISTA🔥-{index}",
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
            "grpc-service-name": (
                entry["servicename"]
                or entry["sni"]
                or entry["server"]
            ),
            "grpc-mode": entry["mode"] or "gun",
        },
    }

    # درصورت Reality
    if entry["security"].lower() == "reality":
        proxy["reality-opts"] = {
            "public-key": entry["pbk"],
            "short-id": entry["sid"],
        }

    return proxy


def main():
    raw_text = fetch_raw_text(RAW_URL)
    vless_list = parse_vless_lines(raw_text)

    proxies = []
    for i, link in enumerate(vless_list, 1):
        params = extract_params(link)
        if not params:
            continue
        proxies.append(build_proxy(params, i))

    # 📂 بارگذاری قالب
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        template = json.load(f)

    # 🔁 جایگزینی پروکسی‌ها
    template["proxies"] = proxies

    # 🧩 افزودن نام‌ها به گروه‌ها
    names = [p["name"] for p in proxies]
    for group in template["proxy-groups"]:
        if group["name"] in ["Auto", "Fallback", "Load Balance"]:
            group["proxies"] = names

    # 📝 ذخیره فایل نهایی
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(proxies)} پروکسی ساخته شد و در {OUTPUT_FILE} ذخیره شد.")


if __name__ == "__main__":
    main()
