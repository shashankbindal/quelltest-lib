"""Domain objects. Constructed with literal arguments elsewhere in the project,
which is what usage_miner (#144) is meant to find."""
from __future__ import annotations


class Account:
    def __init__(self, id: int, owner_email: str, tier: str = "free"):
        self.id = id
        self.owner_email = owner_email
        self.tier = tier


class Invoice:
    def __init__(self, number: str, total_cents: int):
        self.number = number
        self.total_cents = total_cents
        self.settled = False
