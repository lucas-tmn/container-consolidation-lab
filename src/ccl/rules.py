"""Approval rules (per to-do). Thresholds come from config."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TodoFacts:
    pulled_fob_usd: float = 0.0
    has_destination_change: bool = False
    delay_misses_po_due: bool = False
    last_container_fill: float = 1.0


def approval_reasons(t: TodoFacts, params: dict) -> list[str]:
    a = params["approvals"]
    reasons: list[str] = []
    if t.last_container_fill < params["fill"]["min"]:
        reasons.append("container_below_min_fill")
    if t.has_destination_change:
        reasons.append("destination_change")
    if t.delay_misses_po_due and a.get("delay_misses_po_due", True):
        reasons.append("delay_misses_po_due")
    if t.pulled_fob_usd > a["pull_forward_fob_usd"]:
        reasons.append("pull_forward_over_threshold")
    return reasons


def needs_approval(t: TodoFacts, params: dict) -> bool:
    return bool(approval_reasons(t, params))
