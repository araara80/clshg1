import requests
import base64
import re
import json

RAW_URL = "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/grpc.txt"


def fetch_raw():
    """دریافت محتوای لینک و تلاش برای decode در صورت Base64 بودن"""
    resp = requests.get(RAW_URL, timeout=10)
    resp.raise_for_status()
    text = resp.text.strip()
    try:
        decoded = base64.b64decode(text).decode("utf-8", errors="ignore")
        return decoded
    except Exception:
        return text


def parse_vless_lines(raw_text):
    """فقط خطوط vless:// که type=grpc دارند"""
    lines = raw_text.splitlines()
    return [
        line.strip()
        for line in lines
        if line.lower().startswith("vless://") and "type=grpc" in line.lower()
    ]


def extract_params(vless_url):
    """استخراج فیلدهای داخل لینک VLESS"""
    # ساختار: vless://UUID@host:port?key=value&key=value#TAG
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

    # ساخت دیکشنری با مقدار خالی در صورت نبود پارامتر
    return {
        "uuid": uuid,
        "server": server,
        "port": port,
        "type": "vless",
        "network": params.get("type", "grpc"),
        "tls": params.get("security", "").lower() in ("tls", "reality"),
        "servername": params.get("sni", ""),
        "flow": params.get("flow", ""),
        "service_name": params.get("serviceName", ""),
        "grpc_mode": params.get("mode", ""),
    }


def build_proxy_object(entry, index):
    """ساخت یک شیء پروکسی کامل با مقادیر خالی در صورت نبود داده"""
    return {
        "name": f"ALRZ☃️-{index}",
        "type": entry.get("type", "vless"),
        "server": entry.get("server", ""),
        "port": entry.get("port", 0),
        "uuid": entry.get("uuid", ""),
        "network": entry.get("network", "grpc"),
        "tls": entry.get("tls", False),
        "udp": True,
        "skip-cert-verify": False,
        "tcp-fast-open": True,
        "fast-open": True,
        "servername": entry.get("servername", ""),
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
    raw_text = fetch_raw()
    vless_list = parse_vless_lines(raw_text)

    proxies = []
    for i, vless in enumerate(vless_list, 1):
        entry = extract_params(vless)
        if not entry:
            continue
        proxy = build_proxy_object(entry, i)
        proxies.append(proxy)

    result = {
        "port": 7890,
        "socks-port": 7891,
        "mixed-port": 7893,
        "mode": "rule",
        "log-level": "info",
        "dns": {},  # برای سادگی خالی نگه می‌داریم
        "proxies": proxies,
        "proxy-groups": [],
        "rules": []
    }

    with open("clash.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ {len(proxies)} کانفیگ استخراج و در clash.json ذخیره شد.")


if __name__ == "__main__":
    main()
