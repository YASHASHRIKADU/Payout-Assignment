from django.urls import path
from .views import PayoutCreateView, PayoutListView, PayoutDetailView

urlpatterns = [
    path("payouts/", PayoutCreateView.as_view(), name="payout-create"),
    path("payouts/<uuid:id>/", PayoutDetailView.as_view(), name="payout-detail"),
    path(
        "merchants/<uuid:merchant_id>/payouts/",
        PayoutListView.as_view(),
        name="merchant-payout-list",
    ),
]
