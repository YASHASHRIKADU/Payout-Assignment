"""
Idempotency Test: Verify that sending the same Idempotency-Key twice returns
the same response and creates only one Payout record.
"""
import uuid
from django.test import TestCase, Client

from apps.merchants.models import Merchant
from apps.ledger.models import LedgerEntry
from apps.payouts.models import Payout
from core.constants import LEDGER_CREDIT


class IdempotencyTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.merchant = Merchant.objects.create(name="Test Merchant Idempotency")

        # Seed 50,000 paise credit
        LedgerEntry.objects.create(
            merchant=self.merchant,
            type=LEDGER_CREDIT,
            amount_paise=50_000,
            reference_id=f"seed_{uuid.uuid4()}",
        )
        self.idempotency_key = str(uuid.uuid4())

    def test_duplicate_request_returns_same_response(self):
        """
        Sending the same Idempotency-Key twice must:
          - Return the same response body.
          - Create only one Payout record.
        """
        payload = {
            "merchant_id": str(self.merchant.id),
            "amount_paise": 5_000,
        }
        headers = {"Idempotency-Key": self.idempotency_key}

        # First request — should create the payout (201).
        response1 = self.client.post(
            "/api/v1/payouts/",
            data=payload,
            content_type="application/json",
            headers=headers,
        )
        self.assertEqual(response1.status_code, 201, f"First request failed: {response1.data}")
        first_data = response1.json()

        # Second request — same key, should return cached response (200).
        response2 = self.client.post(
            "/api/v1/payouts/",
            data=payload,
            content_type="application/json",
            headers=headers,
        )
        self.assertIn(response2.status_code, [200, 201], "Second request should succeed.")
        second_data = response2.json()

        # Responses must be identical.
        self.assertEqual(
            first_data["id"],
            second_data["id"],
            "Both responses must return the same payout ID.",
        )

        # Only one Payout should exist in the DB.
        payout_count = Payout.objects.filter(merchant=self.merchant).count()
        self.assertEqual(payout_count, 1, "Only one Payout record should exist.")

        print(f"\n✅ Idempotency test passed. Payout ID: {first_data['id']}")

    def test_different_keys_create_different_payouts(self):
        """
        Two requests with different idempotency keys should create two separate payouts.
        """
        payload = {
            "merchant_id": str(self.merchant.id),
            "amount_paise": 5_000,
        }

        r1 = self.client.post(
            "/api/v1/payouts/",
            data=payload,
            content_type="application/json",
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        r2 = self.client.post(
            "/api/v1/payouts/",
            data=payload,
            content_type="application/json",
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )

        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        self.assertNotEqual(r1.json()["id"], r2.json()["id"])

        payout_count = Payout.objects.filter(merchant=self.merchant).count()
        self.assertEqual(payout_count, 2, "Two different keys should create two payouts.")

        print(f"\n✅ Different-key test passed. Two distinct payouts created.")

    def test_missing_idempotency_key_returns_400(self):
        """Request without Idempotency-Key header should be rejected."""
        response = self.client.post(
            "/api/v1/payouts/",
            data={"merchant_id": str(self.merchant.id), "amount_paise": 1_000},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        print("\n✅ Missing idempotency key correctly rejected with 400.")
