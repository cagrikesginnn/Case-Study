import csv
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ads.models import Campaign, DailyMetric
from ads.utils import normalize_channel, parse_date


class Command(BaseCommand):
    help = "CSV dosyasını veritabanına yükler (2 kere çalıştırınca satır çoğalmaz)"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", nargs="?", default="ad_performance.csv")

    def handle(self, *args, **options):
        path = Path(options["csv_path"])
        if not path.exists():
            raise CommandError(f"Dosya yok: {path}")

        created = 0
        updated = 0

        # utf-8-sig: BOM varsa temizler. delimiter=';' çünkü dosya noktalı virgüllü.
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                channel = normalize_channel(row["channel_name"])
                campaign, _ = Campaign.objects.update_or_create(
                    channel=channel,
                    external_id=row["campaign_id"].strip(),
                    defaults={"name": row["campaign_name"].strip()},
                )
                _, was_created = DailyMetric.objects.update_or_create(
                    campaign=campaign,
                    date=parse_date(row["date"]),
                    defaults={
                        "impressions": int(row["impressions"]),
                        "clicks": int(row["clicks"]),
                        "spend": Decimal(row["spend"]),
                        "conversions": Decimal(row["conversions"]),
                        "revenue": Decimal(row["revenue"]),
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Bitti. yeni={created}, güncellenen={updated}, "
                f"kampanya={Campaign.objects.count()}, metrik={DailyMetric.objects.count()}"
            )
        )
