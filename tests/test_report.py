import json, re
from pathlib import Path
from ccl.report import build_html, collect_runs
from ccl.report_i18n import EN, VI

SAMPLE = Path(__file__).resolve().parents[1] / "ui" / "sample" / "bundle_demo.json"

def test_i18n_key_parity():
    assert set(EN) == set(VI)

def test_i18n_placeholders_match():
    for k in EN:
        assert set(re.findall(r"\{(\w+)\}", EN[k])) == set(re.findall(r"\{(\w+)\}", VI[k])), k

def test_build_both_languages():
    b = json.loads(SAMPLE.read_text(encoding="utf-8"))
    for lang in ("en", "vi"):
        h = build_html(b, lang)
        assert "__DATA__" not in h and "__I18N__" not in h and "__LANG__" not in h
        assert f'lang="{lang}"' in h
        assert "</script><script" not in h

def test_sample_has_no_ids():
    t = SAMPLE.read_text(encoding="utf-8").lower()
    for bad in ("po_number", "ponumber", "vendor_id", "user_id", "pomnum"):
        assert bad not in t

def test_collect_runs_missing(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        collect_runs(tmp_path)
