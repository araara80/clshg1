def build_proxy(entry, index):
    """ساخت پروکسی بر اساس قوانین کاربر"""

    # 🔹 TLS بر اساس security
    security = entry.get("security", "").lower()
    tls_enabled = False if (not security or security == "none") else True

    # 🔹 ALPN فقط اگر تعریف شده
    alpn_values = None
    if entry.get("alpn"):
        alpn_values = [v.strip() for v in entry["alpn"].split(",") if v.strip()]

    # 🔹 grpc-service-name
    grpc_name = entry.get("host") or entry.get("serviceName") or "GunService"

    # 🔹 client fingerprint
    fingerprint = entry.get("fp") or "chrome"

    # 🔹 servername از sni
    servername = entry.get("sni", "")

    # 🔹 flow
    flow = entry.get("flow", "")

    proxy = {
        "name": f"ALRZ☃️-{index}",
        "type": "vless",
        "server": entry.get("server", ""),
        "port": entry.get("port", 0),
        "uuid": entry.get("uuid", ""),
        "network": "grpc",
        "tls": tls_enabled,
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

    # 🔹 فقط اگر alpn وجود داشته باشد، به خروجی اضافه شود
    if alpn_values:
        proxy["alpn"] = alpn_values

    return proxy
