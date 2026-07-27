from django.db import models


class Campaign(models.Model):
    # Aynı campaign_id farklı kanallarda gelebildiği için ikisini birlikte unique tutuyorum
    external_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    channel = models.CharField(max_length=32)  # google_ads, meta, tiktok, criteo

    class Meta:
        unique_together = ("channel", "external_id")

    def __str__(self):
        return f"{self.name} ({self.channel})"


class DailyMetric(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="metrics")
    date = models.DateField()
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    spend = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    conversions = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        unique_together = ("campaign", "date")  # aynı günü 2 kere yüklememek için

    def __str__(self):
        return f"{self.campaign_id} - {self.date}"
