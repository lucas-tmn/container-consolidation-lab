"""Planning engine (phase 1, not implemented yet). See docs/03_logic_spec.md for the steps.

Intended structure:
    baseline -> spread -> find_overflow -> change_destination -> delay -> pull_forward -> leftover -> rank_options
Every step is a pure function of (state, params) so each can be unit-tested and replayed.
"""
from __future__ import annotations


def plan_week(snapshot_dir: str, vendor: str, ship_week: str, params: dict) -> dict:
    raise NotImplementedError(
        "Engine v1 is planned for phase 1. Needs a frozen snapshot (docs/04_data_spec.md) "
        "with planned lines of the ship week and the next week, item master, inventory projection and forecast."
    )
