# 11. HTML report (Main + How it works, EN and VI)

`python -m ccl report --runs runs --out report` builds `report/container_lab_en.html`, `report/container_lab_vi.html` and `report/bundle.json` from the run folders written by `ccl plan` (one folder per week and mode). Each file is a single static page with two tabs (`#main`, `#how-it-works`) and an EN/VI toggle. No server, no network except an optional web font.

- `--snapshot` picks a snapshot (default: latest). `--bundle file.json` builds from a bundle instead of runs.
- `ui/sample/bundle_demo.json` is SYNTHETIC (invented DEMO-xxx items) so the page can be opened without EDW. Regenerate with `python ui/make_sample.py`.
- Texts live in `src/ccl/report_i18n.py` (tests check EN and VI have the same keys and placeholders). Layout and logic: `ui/template.html`.
- Thresholds shown on the How it works page are read from `config/params.yaml` through the bundle; nothing is hardcoded in the page.
- Insights on Main are generated from the loaded data. Static notes keep evidence labels: [V] seen, [I] inferred, [?] unknown.
- Output folders (`report/`, `runs/`) are git-ignored. Lines are shown by SEQ only, never by PO, vendor id or user id.
