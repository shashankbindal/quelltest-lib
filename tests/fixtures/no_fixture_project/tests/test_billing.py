"""One hand-written test, so coverage attribution has something to find.

Keep this file to the single test below — `quell find --fix` appends generated
tests here, and committing those makes the ablation measure nothing.
"""
from app.billing import upgrade
from app.seed import demo_account


def test_upgrade_sets_the_tier():
    assert upgrade(demo_account(), "team")["tier"] == "team"
