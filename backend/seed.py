"""
Seed script — creates test merchants and seeds initial credits.
Run with: python seed.py

Requires DJANGO_SETTINGS_MODULE to be set (done below automatically).
"""
import os
import sys
import django
import uuid

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from apps.merchants.models import Merchant
from apps.ledger.models import LedgerEntry
from core.constants import LEDGER_CREDIT


MERCHANTS = [
    {"name": "Acme Freelancers"},
    {"name": "Bright Design Studio"},
    {"name": "CodeCraft Agency"},
]

# Each merchant gets this initial credit (in paise)
INITIAL_CREDIT_PAISE = 100_000  # ₹1,000


def seed():
    print("Seeding database...\n")

    for merchant_data in MERCHANTS:
        merchant, created = Merchant.objects.get_or_create(name=merchant_data["name"])
        action = "Created" if created else "Already exists"
        print(f"  [{action}] Merchant: {merchant.name} | ID: {merchant.id}")

        if created:
            LedgerEntry.objects.create(
                merchant=merchant,
                type=LEDGER_CREDIT,
                amount_paise=INITIAL_CREDIT_PAISE,
                reference_id=f"seed_initial_{merchant.id}",
            )
            print(f"    Credited {INITIAL_CREDIT_PAISE} paise (Rs.{INITIAL_CREDIT_PAISE // 100})")

    print("\nSeeding complete!")
    print("\nMerchant IDs (use these in the frontend):")
    for m in Merchant.objects.all():
        print(f"  {m.name}: {m.id}")


if __name__ == "__main__":
    seed()
