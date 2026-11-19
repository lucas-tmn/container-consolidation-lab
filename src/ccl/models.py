from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    code: str
    cube_ft3: float   # per piece
    fob_usd: float    # per piece


@dataclass(frozen=True)
class Line:
    seq: int
    item: str
    qty: int
    destination: str          # DC name, e.g. "Mesquite"
    change_type: str          # "pull_in" | "destination_change" | "delay" | "none"
    from_ship_week: str = ""
    to_ship_week: str = ""
