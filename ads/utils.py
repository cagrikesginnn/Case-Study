from datetime import datetime


CHANNEL_MAP = {
    "google ads": "google_ads",
    "google_ads": "google_ads",
    "meta ads": "meta",
    "meta": "meta",
    "tiktok ads": "tiktok",
    "tiktok": "tiktok",
    "criteo": "criteo",
}


def normalize_channel(value):
    key = value.strip().lower()
    if key not in CHANNEL_MAP:
        raise ValueError(f"Bilinmeyen kanal: {value}")
    return CHANNEL_MAP[key]


def parse_date(value):
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Tarih okunamadı: {value}")


def safe_div(a, b):
    """Payda 0 ise None döner (JSON'da null)."""
    if b == 0 or b is None:
        return None
    return round(float(a) / float(b), 6)


def add_derived(impressions, clicks, spend, conversions, revenue):
    return {
        "impressions": int(impressions or 0),
        "clicks": int(clicks or 0),
        "spend": float(spend or 0),
        "conversions": float(conversions or 0),
        "revenue": float(revenue or 0),
        "ctr": safe_div(clicks, impressions),
        "cvr": safe_div(conversions, clicks),
        "cpc": safe_div(spend, clicks),
        "cpa": safe_div(spend, conversions),
        "roas": safe_div(revenue, spend),
    }
