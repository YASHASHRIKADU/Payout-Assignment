from rest_framework import generics
from rest_framework.response import Response

from .models import Merchant
from .serializers import MerchantSerializer


class MerchantListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/merchants/   — list all merchants
    POST /api/v1/merchants/   — create a merchant
    """
    queryset = Merchant.objects.all()
    serializer_class = MerchantSerializer
