import base64
import requests
import re

def fetch_and_decode(url):
    """دریافت محتوا از لینک و در صورت نیاز decode"""
    try:
        data = requests.get(url, timeout=10).text.strip()
        # اگر Base64 بود
        try:
            decoded = base64.b64decode(data).decode("utf-8", errors="ignore")
            data = decoded
        except Exception:
            pass
        return data
    except Exception as e:
        print(f"❌ خطا در دریافت {url}: {e}")
        return ""

def extract_server_port(vless_url):
    """
    از لینک vless:// آدرس و پورت رو استخراج می‌کنه
    مثال:
    vless://uuid@host:port?... => host, port
    """
    match = re.search(r"@([^:/]+):(\d+)", vless_url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def main():
    # خواندن لیست لینک‌ها از فایل
    with open("subs.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    all_configs = []

    # خواندن و ترکیب محتوا
    for url in urls:
        print(f"📥 در حال خواندن {url} ...")
        content = fetch_and_decode(url)
        all_configs.extend(content.splitlines())

    # فیلتر فقط VLESSهایی که type=grpc دارن (بدون حساسیت به حروف)
    vless_list = [
        line.strip() for line in all_configs
        if line.lower().startswith("vless://") and "type=grpc" in line.lower()
    ]

    # حذف لینک‌های تکراری با سرور و پورت یکسان
    unique = []
    seen = set()
    for line in vless_list:
        host, port = extract_server_port(line)
        if host and port:
            key = f"{host}:{port}"
            if key not in seen:
                seen.add(key)
                unique.append(line)
        else:
            # اگر نتونست سرور و پورت رو پیدا کنه، نگه‌دار (برای اطمینان)
            unique.append(line)

    # افزودن اسم ALRZ☃️-n به هر کانفیگ
    final = []
    for i, line in enumerate(unique, 1):
        if "#" in line:
            base = line.split("#")[0]
        else:
            base = line
        labeled = f"{base}#ALRZ☃️-{i}"
        final.append(labeled)

    # ذخیره خروجی
    with open("vless_grpc.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final))

    print(f"✅ تمام شد! {len(final)} لینک نهایی بعد از حذف تکراری‌ها پیدا شد.")

if __name__ == "__main__":
    main()
