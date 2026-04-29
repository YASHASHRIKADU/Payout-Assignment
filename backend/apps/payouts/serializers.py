from rest_framework import serializers
from .models import Payout


class PayoutCreateSerializer(serializers.Serializer):
    """Validates incoming payout creation request body."""
    merchant_id = serializers.UUIDField()
    amount_paise = serializers.IntegerField(min_value=1)

    def validate_amount_paise(self, value):
        if value <= 0:
            raise serializers.ValidationError("amount_paise must be a positive integer.")
        return value


class PayoutResponseSerializer(serializers.ModelSerializer):
    """Serializes a Payout for API responses."""
    class Meta:
        model = Payout
        fields = [
            "id",
            "merchant",
            "amount_paise",
            "status",
            "retry_count",
            "idempotency_key",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
