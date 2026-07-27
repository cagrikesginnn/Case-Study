"""
Türkçe soru → Mistral SQL üretir → sadece SELECT çalıştırılır → sonuç döner.
"""

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from django.conf import settings
from django.db import connection


SCHEMA_INFO = """
SQLite veritabanı. Django tabloları:

1) ads_campaign
   - id (INTEGER, PK)
   - external_id (TEXT)  -- CSV'deki campaign_id, örn: "1","2","3"
   - name (TEXT)         -- örn: campaign_1
   - channel (TEXT)      -- google_ads | meta | tiktok | criteo

2) ads_dailymetric
   - id (INTEGER, PK)
   - campaign_id (INTEGER, FK → ads_campaign.id)  !! external_id değil, sayısal PK
   - date (TEXT/DATE)    -- YYYY-MM-DD, veri Temmuz 2026
   - impressions (INTEGER)
   - clicks (INTEGER)
   - spend (DECIMAL)     -- harcama
   - conversions (DECIMAL)
   - revenue (DECIMAL)   -- gelir

Join örneği:
  SELECT ... FROM ads_dailymetric m
  JOIN ads_campaign c ON c.id = m.campaign_id
"""


def get_mistral_key():
    """Her seferinde .env'den oku (eski key ortamda kalmasın)."""
    env_path = Path(settings.BASE_DIR) / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "MISTRAL_API_KEY":
                return value.strip().strip('"').strip("'")
    return os.environ.get("MISTRAL_API_KEY", "").strip()


def ask_mistral_for_sql(question: str) -> str:
    api_key = get_mistral_key()
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY yok. .env dosyasına ekle.")

    system = (
        "Sen SQLite uzmanısın. Kullanıcı Türkçe soru soracak. "
        "SADECE tek bir SELECT SQL sorgusu yaz. "
        "Açıklama, markdown, kod bloğu YAZMA. Sadece SQL. "
        "DELETE/UPDATE/DROP/INSERT/ALTER yasak. "
        "Sonuç çok olmasın diye gerekirse LIMIT 50 koy. "
        f"\nŞema:\n{SCHEMA_INFO}"
    )

    body = {
        "model": "mistral-small-latest",
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
    }
    req = urllib.request.Request(
        "https://api.mistral.ai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Mistral API hata {e.code}: {detail}") from e

    text = data["choices"][0]["message"]["content"].strip()
    return clean_sql(text)


def clean_sql(text: str) -> str:
    text = text.strip()
    # ```sql ... ``` temizle
    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    # Birden fazla statement varsa ilkini al
    text = text.split(";")[0].strip()
    return text


def is_safe_select(sql: str) -> bool:
    normalized = re.sub(r"\s+", " ", sql.strip().lower())
    if not normalized.startswith("select"):
        return False
    # Tehlikeli komutlar (fonksiyon adı REPLACE ile karışmasın diye kelime sınırı)
    banned = re.compile(
        r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|truncate|grant|revoke)\b",
        re.IGNORECASE,
    )
    if banned.search(normalized):
        return False
    if "--" in sql or "/*" in sql:
        return False
    return True



def run_select(sql: str, limit: int = 100):
    if not is_safe_select(sql):
        raise ValueError("Sadece güvenli SELECT sorgularına izin var.")

    with connection.cursor() as cursor:
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(limit)
        results = []
        for row in rows:
            item = {}
            for col, val in zip(columns, row):
                item[col] = str(val) if val is not None else None
            results.append(item)
    return columns, results
