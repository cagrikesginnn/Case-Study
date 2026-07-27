from rest_framework import serializers

from ads.models import Campaign, DailyMetric
from ads.utils import add_derived


class CampaignSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="external_id")

    class Meta:
        model = Campaign
        fields = ["id", "name", "channel"]


class DailyMetricSerializer(serializers.ModelSerializer):
    campaign_id = serializers.CharField(source="campaign.external_id")
    campaign_name = serializers.CharField(source="campaign.name")
    channel = serializers.CharField(source="campaign.channel")

    class Meta:
        model = DailyMetric
        fields = [
            "date",
            "campaign_id",
            "campaign_name",
            "channel",
            "impressions",
            "clicks",
            "spend",
            "conversions",
            "revenue",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        derived = add_derived(
            instance.impressions,
            instance.clicks,
            instance.spend,
            instance.conversions,
            instance.revenue,
        )
        data["ctr"] = derived["ctr"]
        data["cvr"] = derived["cvr"]
        data["cpc"] = derived["cpc"]
        data["cpa"] = derived["cpa"]
        data["roas"] = derived["roas"]
        return data
