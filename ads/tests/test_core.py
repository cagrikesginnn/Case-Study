from datetime import date
from decimal import Decimal
import tempfile

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from ads.models import Campaign, DailyMetric
from ads.utils import add_derived, safe_div


class MetricMathTests(TestCase):
    def test_sifira_bolme_null_doner(self):
        self.assertIsNone(safe_div(10, 0))
        out = add_derived(0, 0, 0, 0, 0)
        self.assertIsNone(out["ctr"])
        self.assertIsNone(out["roas"])

    def test_normal_hesap(self):
        out = add_derived(1000, 100, 50, 10, 200)
        self.assertEqual(out["ctr"], 0.1)
        self.assertEqual(out["roas"], 4.0)


class SummaryTests(TestCase):
    def setUp(self):
        c = Campaign.objects.create(external_id="1", name="A", channel="meta")
        DailyMetric.objects.create(
            campaign=c,
            date=date(2026, 6, 1),
            impressions=1000,
            clicks=100,
            spend=Decimal("50"),
            conversions=Decimal("10"),
            revenue=Decimal("200"),
        )
        DailyMetric.objects.create(
            campaign=c,
            date=date(2026, 6, 2),
            impressions=1000,
            clicks=100,
            spend=Decimal("50"),
            conversions=Decimal("10"),
            revenue=Decimal("200"),
        )
        self.client = APIClient()

    def test_summary_toplamlari_dogru(self):
        # Elle: impressions=2000, clicks=200, spend=100, conv=20, rev=400, ROAS=4
        r = self.client.get(
            "/api/metrics/summary/",
            {"group_by": "channel", "start_date": "2026-06-01", "end_date": "2026-06-30"},
        )
        self.assertEqual(r.status_code, 200)
        t = r.data["totals"]
        self.assertEqual(t["impressions"], 2000)
        self.assertEqual(t["clicks"], 200)
        self.assertEqual(t["spend"], 100.0)
        self.assertEqual(t["roas"], 4.0)

    def test_bos_ay(self):
        # Bu testte DB'de sadece Haziran var. Olmayan ay sorulunca boş/null gelmeli.
        # (Gerçek CSV'de tersi: Temmuz var, Haziran yok — aynı mantık.)
        r = self.client.get(
            "/api/metrics/summary/",
            {"start_date": "2026-07-01", "end_date": "2026-07-31"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["totals"]["impressions"], 0)
        self.assertIsNone(r.data["totals"]["ctr"])


class IngestTests(TestCase):
    def test_iki_kere_yukleince_cogalmaz(self):
        csv_text = (
            "date;campaign_id;campaign_name;channel_name;impressions;clicks;spend;conversions;revenue\n"
            "1.06.2026;1; test ;Google Ads;100;10;5;1;20\n"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write(csv_text)
            path = f.name

        call_command("ingest_csv", path)
        call_command("ingest_csv", path)
        self.assertEqual(DailyMetric.objects.count(), 1)
        self.assertEqual(Campaign.objects.get().name, "test")  # trim çalıştı
