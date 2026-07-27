# Orphex Case Study

Reklam performans CSV’sini okuyup veritabanına atan, sonra API’den sorgulatan küçük bir proje.

Django + Django REST Framework kullandım. Brief’te onlar vardı, bilmiyordum biraz, denemek istedim.

## Nasıl çalıştırılır


python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py ingest_csv ad_performance.csv
python manage.py runserver


`ingest_csv` komutunu iki kere çalıştırsan da satırlar çiftlenmez.

Test için:

python manage.py test ads

## Örnek istekler


curl "http://127.0.0.1:8000/api/campaigns/"

curl "http://127.0.0.1:8000/api/metrics/?channel=meta&campaign_id=1&start_date=2026-07-01&end_date=2026-07-07"

curl "http://127.0.0.1:8000/api/metrics/summary/?group_by=campaign&channel=meta"

curl "http://127.0.0.1:8000/api/insights/top-campaigns/"



## Soru sor (Mistral → SQL → DB)

Tarayıcıda aç:


http://127.0.0.1:8000/api/ask-page/


