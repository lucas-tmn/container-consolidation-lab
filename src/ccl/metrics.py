"""Pure metric functions. No I/O. Thresholds are passed in from config."""
from __future__ import annotations
import math
from typing import Iterable, Mapping


def cube(qty: float, cube_per_piece: float) -> float:
    return qty * cube_per_piece


def container_eq(total_cube_ft3: float, container_ft3: float = 2400.0) -> float:
    return total_cube_ft3 / container_ft3


def containers(total_cube_ft3: float, container_ft3: float = 2400.0) -> int:
    """A partial container still ships as one."""
    if total_cube_ft3 <= 0:
        return 0
    return math.ceil(total_cube_ft3 / container_ft3 - 1e-9)


def avg_fill(total_cube_ft3: float, n_containers: int, container_ft3: float = 2400.0) -> float:
    if n_containers == 0:
        return 0.0
    return total_cube_ft3 / (n_containers * container_ft3)


def last_container_fill(total_cube_ft3: float, container_ft3: float = 2400.0) -> float:
    """Fill of the last (partial) container; 1.0 when the cube is an exact multiple."""
    if total_cube_ft3 <= 0:
        return 0.0
    r = (total_cube_ft3 / container_ft3) % 1.0
    return 1.0 if r < 1e-9 else r


def freight_usd(containers_by_dc: Mapping[str, int], region_by_dc: Mapping[str, str],
                rate_by_region: Mapping[str, float]) -> float:
    return sum(n * rate_by_region[region_by_dc[dc]] for dc, n in containers_by_dc.items())


def weeks_of_supply(projected_inventory: float | None, weekly_forecast: float | None,
                    missing_value: float = 0.0) -> float:
    """WOS = projected shippable inventory / weekly forecast; missing data -> missing_value (app: 0)."""
    if projected_inventory is None or weekly_forecast is None or weekly_forecast <= 0:
        return missing_value
    return max(projected_inventory, 0.0) / weekly_forecast


def is_short(wos: float, short_below_weeks: float) -> bool:
    return wos < short_below_weeks


def weekly_forecast_from_monthly(monthly_by_channel: Iterable[float]) -> float:
    """Reference app: monthly channel forecast summed over channels, x 12 / 52."""
    return sum(monthly_by_channel) * 12.0 / 52.0
