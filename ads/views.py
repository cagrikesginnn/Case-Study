from django.db.models import Sum
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from ads.ask_sql import ask_mistral_for_sql, run_select
from ads.models import Campaign, DailyMetric
from ads.serializers import CampaignSerializer, DailyMetricSerializer
from ads.utils import add_derived, normalize_channel, parse_date


def filter_metrics(request):
    qs = DailyMetric.objects.select_related("campaign").all()

    channel = request.query_params.get("channel")
    if channel:
        qs = qs.filter(campaign__channel=normalize_channel(channel))

    campaign_id = request.query_params.get("campaign_id")
    if campaign_id:
        qs = qs.filter(campaign__external_id=campaign_id)

    start = request.query_params.get("start_date")
    end = request.query_params.get("end_date")
    if start:
        qs = qs.filter(date__gte=parse_date(start))
    if end:
        qs = qs.filter(date__lte=parse_date(end))

    return qs


def ask_page(request):
    return render(request, "ads/ask.html")


class AskQueryView(APIView):
    """Türkçe soru → Mistral SQL → DB sonucu."""

    def post(self, request):
        question = (request.data.get("question") or "").strip()
        if not question:
            return Response({"error": "Soru boş olamaz"}, status=400)
        try:
            sql = ask_mistral_for_sql(question)
            columns, rows = run_select(sql)
        except Exception as exc:  # noqa: BLE001
            return Response({"error": str(exc)}, status=400)
        return Response(
            {
                "question": question,
                "sql": sql,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
            }
        )


class CampaignListView(APIView):
    def get(self, request):
        return Response(CampaignSerializer(Campaign.objects.all(), many=True).data)


class MetricListView(APIView):
    def get(self, request):
        qs = filter_metrics(request).order_by("date")
        return Response(DailyMetricSerializer(qs, many=True).data)


class MetricSummaryView(APIView):
    def get(self, request):
        group_by = request.query_params.get("group_by", "channel")
        if group_by not in ("channel", "campaign", "date"):
            return Response({"error": "group_by: channel, campaign veya date olmalı"}, status=400)

        qs = filter_metrics(request)
        sums = {
            "impressions": Sum("impressions"),
            "clicks": Sum("clicks"),
            "spend": Sum("spend"),
            "conversions": Sum("conversions"),
            "revenue": Sum("revenue"),
        }

        if group_by == "channel":
            rows = qs.values("campaign__channel").annotate(**sums)
            results = []
            for r in rows:
                item = add_derived(r["impressions"], r["clicks"], r["spend"], r["conversions"], r["revenue"])
                item["channel"] = r["campaign__channel"]
                results.append(item)
        elif group_by == "campaign":
            rows = qs.values(
                "campaign__external_id", "campaign__name", "campaign__channel"
            ).annotate(**sums)
            results = []
            for r in rows:
                item = add_derived(r["impressions"], r["clicks"], r["spend"], r["conversions"], r["revenue"])
                item["campaign_id"] = r["campaign__external_id"]
                item["campaign_name"] = r["campaign__name"]
                item["channel"] = r["campaign__channel"]
                results.append(item)
        else:
            rows = qs.values("date").annotate(**sums).order_by("date")
            results = []
            for r in rows:
                item = add_derived(r["impressions"], r["clicks"], r["spend"], r["conversions"], r["revenue"])
                item["date"] = str(r["date"])
                results.append(item)

        total = qs.aggregate(**sums)
        return Response(
            {
                "group_by": group_by,
                "results": results,
                "totals": add_derived(
                    total["impressions"] or 0,
                    total["clicks"] or 0,
                    total["spend"] or 0,
                    total["conversions"] or 0,
                    total["revenue"] or 0,
                ),
            }
        )


class TopCampaignsView(APIView):
    """Stretch: ROAS'a göre en iyi kampanyalar."""

    def get(self, request):
        qs = filter_metrics(request)
        rows = qs.values(
            "campaign__external_id", "campaign__name", "campaign__channel"
        ).annotate(
            impressions=Sum("impressions"),
            clicks=Sum("clicks"),
            spend=Sum("spend"),
            conversions=Sum("conversions"),
            revenue=Sum("revenue"),
        )
        results = []
        for r in rows:
            item = add_derived(r["impressions"], r["clicks"], r["spend"], r["conversions"], r["revenue"])
            item["campaign_id"] = r["campaign__external_id"]
            item["campaign_name"] = r["campaign__name"]
            item["channel"] = r["campaign__channel"]
            if item["roas"] is not None:
                results.append(item)

        results.sort(key=lambda row: row["roas"], reverse=True)
        return Response(results[:10])
