import base64
import requests

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

    # فیلتر کردن فقط VLESSهایی که type=grpc دارن
    filtered = [line for line in all_configs if line.startswith("vless://") and "type=grpc" in line]

    # ذخیره خروجی
    with open("filtered.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(filtered))

    print(f"✅ تمام شد! تعداد {len(filtered)} لینک VLESS با type=grpc پیدا شد.")

if __name__ == "__main__":
    main()
