# container-consolidation-lab

A local, measurable lab for **ocean-container consolidation decisions** (fill, destination, delay, pull-forward) for import vendors.
Modelled on `forecast-accuracy-lab`: frozen local data, a deterministic engine, and a scoring layer, so every recommendation can be reproduced and measured.

> VI (tóm tắt): Repo này là bản tự dựng và tự đo của công cụ gộp container, lấy cảm hứng từ app "Container Overflow Planner" của Amanda (19/11/2026). Không phải bản sao: mục tiêu là hiểu logic, tái tạo kết quả của app trên dữ liệu đóng băng, rồi đo xem kế hoạch có thật sự tốt không.

## Status
`v0 – spec and golden data only`. The engine is a skeleton; the metric functions and golden tests run. See [docs/07_roadmap.md](docs/07_roadmap.md).

## What is in this repo
| Path | What |
|---|---|
| `docs/01_business_context.md` | Why this exists, who decides what, what "good" means |
| `docs/02_reference_app_analysis.md` | What Amanda's app does and what was verified against EDW (15 evidence rounds) |
| `docs/03_logic_spec.md` | The planning rules, formulas and algorithm the engine must implement |
| `docs/04_data_spec.md` | Inputs, EDW/Databricks sources, frozen snapshot layout, SQL notes |
| `docs/05_verification_plan.md` | Golden tests, backtest, KPIs, acceptance criteria |
| `docs/06_assumptions_and_open_questions.md` | Working assumptions and what is still unknown |
| `docs/07_roadmap.md` | Phases 0–3 |
| `docs/08_working_agreements.md` | Data-handling rules and the Claude chat / Claude Code query loop |
| `config/params.yaml` | All thresholds (placeholders; change here, not in code) |
| `data/golden/` | The reference app's Dec 21 plan lines and the item cube/FOB used to test the engine |
| `sql/` | Read-only EDW queries used to build frozen snapshots |
| `src/ccl/` | Python package (models, metrics, rules, engine, CLI) |
| `tests/` | Golden and unit tests |
| `prototype/index.html` | Static HTML prototype of the reference plan with a "verify vs app" tab |

## Quick start
```
python -m venv .venv && .venv/Scripts/activate   # or source .venv/bin/activate
pip install -e .[dev]
pytest
python -m ccl verify-golden        # recompute the Dec 21 plan totals and compare with the app
```

## Principles
1. **Read-only, local, frozen.** No write-back to any system. Every run states the snapshot it used.
2. **Reproduce before improving.** The engine must first match the reference app on the golden plan (or explain every difference), then improve.
3. **Every rule is a parameter.** The app's thresholds are placeholders; keep them in `config/params.yaml` and run sensitivity.
4. **Measure outcomes, not just plans.** Containers saved is not enough; also measure weeks-of-supply risk and capital pulled forward.
