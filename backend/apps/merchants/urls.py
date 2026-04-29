from django.urls import path
from .views import MerchantListCreateView

urlpatterns = [
    path("", MerchantListCreateView.as_view(), name="merchant-list-create"),
]
