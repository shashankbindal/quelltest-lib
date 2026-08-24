"""Real construction sites with literal arguments — rung 2's input."""
from __future__ import annotations

from app.models import Account, Invoice


def demo_account() -> Account:
    return Account(id=1, owner_email="a@example.com", tier="pro")


def demo_invoice() -> Invoice:
    return Invoice(number="INV-1", total_cents=1000)
