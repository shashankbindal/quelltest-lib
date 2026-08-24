"""Guards reading attributes off complex parameters.

No conftest fixture is named `account` or `invoice`, so rung 1 (#143) cannot
fire here. That is the point of this fixture: rungs 2 and 3 get a chance.
"""
from __future__ import annotations

from app.models import Account, Invoice


def settle(account: Account, invoice: Invoice, amount_cents: int) -> dict:
    """Settle an invoice against an account.

    Raises:
        ValueError: if the account has no owner or the amount is not positive.
    """
    if not account.owner_email:
        raise ValueError("account has no owner")
    if amount_cents <= 0:
        raise ValueError("amount must be positive")
    if invoice.settled:
        raise ValueError("invoice already settled")
    invoice.settled = True
    return {"invoice": invoice.number, "paid": amount_cents}


def upgrade(account: Account, tier: str) -> dict:
    """Move an account to a new tier.

    Raises:
        ValueError: if the tier is empty.
    """
    if not tier:
        raise ValueError("tier is required")
    account.tier = tier
    return {"id": account.id, "tier": tier}
