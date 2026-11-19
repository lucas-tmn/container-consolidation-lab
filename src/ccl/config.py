from __future__ import annotations
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def load_params(path: Path | None = None) -> dict:
    p = Path(path) if path else ROOT / "config" / "params.yaml"
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)
