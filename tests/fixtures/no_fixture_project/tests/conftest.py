"""Deliberately provides NO fixture matching any parameter in app/billing.py.

`tmp_path`-style helpers only. This is what makes the project a control for
rungs 2 and 3 of the §4.4 ladder — rung 1 has nothing to match.
"""
import pytest


@pytest.fixture
def unrelated_helper():
    return object()
