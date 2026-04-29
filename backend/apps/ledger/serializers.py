from rest_framework import serializers
from .models import LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = ["id", "merchant", "type", "amount_paise", "reference_id", "created_at"]
        read_only_fields = fields
