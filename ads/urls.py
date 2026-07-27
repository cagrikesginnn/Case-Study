from django.urls import path

from ads.views import (
    AskQueryView,
    CampaignListView,
    MetricListView,
    MetricSummaryView,
    TopCampaignsView,
    ask_page,
)

urlpatterns = [
    path("ask-page/", ask_page, name="ask-page"),
    path("ask/", AskQueryView.as_view(), name="ask-query"),
    path("campaigns/", CampaignListView.as_view()),
    path("metrics/", MetricListView.as_view()),
    path("metrics/summary/", MetricSummaryView.as_view()),
    path("insights/top-campaigns/", TopCampaignsView.as_view()),
]
