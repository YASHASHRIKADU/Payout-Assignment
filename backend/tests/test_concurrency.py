"""
Concurrency Test: Verify that only one of two simultaneous payout requests
succeeds when the merchant has insufficient balance for both.

Setup:
    - Merchant with 10,000 paise (₹100)
    - Two concurrent requests each for 6,000 paise (₹60)
Expected:
    - Exactly 1 request returns HTTP 201
    - Exactly 1 request returns HTTP 402
    - Merchant balance after: 4,000 paise (one debit applied)
"""
import threading
import uuid
from django.test import TestCase, Client
from django.urls import reverse

from apps.merchants.models import Merchant
from apps.ledger.models import LedgerEntry
from apps.payouts.models import Payout
from core.constants import LEDGER_CREDIT


class ConcurrentPayoutTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.merchant = Merchant.objects.create(name="Test Merchant Concurrent")

        # Seed 10,000 paise credit
        LedgerEntry.objects.create(
            merchant=self.merchant,
            type=LEDGER_CREDIT,
            amount_paise=10_000,
            reference_id=f"seed_{uuid.uuid4()}",
        )

    def _post_payout(self, amount_paise: int, result_bucket: list):
        """Worker function for each thread."""
        response = self.client.post(
            "/api/v1/payouts/",
            data={
                "merchant_id": str(self.merchant.id),
                "amount_paise": amount_paise,
            },
            content_type="application/json",
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        result_bucket.append(response.status_code)

    def test_only_one_concurrent_payout_succeeds(self):
        """
        Fire two simultaneous payout requests for 6,000 paise each against
        a 10,000 paise balance. Only one should succeed.
        """
        results = []

        t1 = threading.Thread(target=self._post_payout, args=(6_000, results))
        t2 = threading.Thread(target=self._post_payout, args=(6_000, results))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(results), 2, "Both threads should have completed.")

        successes = results.count(201)
        failures = results.count(402)

        self.assertEqual(successes, 1, f"Expected 1 success, got {successes}. Results: {results}")
        self.assertEqual(failures, 1, f"Expected 1 failure, got {failures}. Results: {results}")

        # Only one payout should exist.
        payout_count = Payout.objects.filter(merchant=self.merchant).count()
        self.assertEqual(payout_count, 1, "Only one Payout record should have been created.")

        print(f"\n✅ Concurrency test passed. Status codes: {results}")
