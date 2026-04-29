from django.urls import path
from .views import BalanceView, LedgerEntryListView

urlpatterns = [
    path(
        "merchants/<uuid:merchant_id>/balance/",
        BalanceView.as_view(),
        name="merchant-balance",
    ),
    path(
        "merchants/<uuid:merchant_id>/ledger/",
        LedgerEntryListView.as_view(),
        name="merchant-ledger",
    ),
]
