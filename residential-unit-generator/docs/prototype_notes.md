# Residential Unit Generator MVP — Grasshopper/Python Prototype Notes

## Prototype scope

This prototype is intentionally pure-Python first. It generates rectangular apartment plans for a 12m x 8m boundary and outputs JSON + CSV.

## Implemented files

- `gh/scripts/config_loader.py`
- `gh/scripts/rectangle_utils.py`
- `gh/scripts/bsp_splitter.py`
- `gh/scripts/room_assigner.py`
- `gh/scripts/rule_checker.py`
- `gh/scripts/rule_registry.py`
- `gh/scripts/scorer.py`
- `gh/scripts/batch_runner.py`
- `run_prototype.py`
- `tests/test_rule_registry.py`

## How to run

From the repository root:

```bash
python residential-unit-generator/run_prototype.py residential-unit-generator/configs/default_3br.json 20 residential-unit-generator/results
```

## What it generates

- `results/batch_summary.csv`
- `results/A000.json` ... `results/A019.json`

## Current prototype result

- 20 generated units
- 20 valid
- Top score: 0.9521
- Added stricter layout rules for dead-end bathrooms, kitchen-bedroom adjacency, and bedroom access
- Added explicit preferred/disallowed adjacency policy checks
- Current default 3BR layout now passes all layout warnings

## Grasshopper bridge

- `gh/GH_Interface.py` wraps the prototype for GH-facing usage.
- `gh/code.py` is a GH_ScriptInstance-compatible component skeleton.
- `gh/scripts/geometry_model.py` exposes polygon payloads for Rhino conversion.
- `gh/scripts/rhino_writer.py` contains helper routines for unit geometry extraction and Rhino-object conversion.
- `gh/metadata.json` describes the component metadata for componentization.
- `code.py` now emits geometry-oriented outputs: room polygons, wall segments, door points, and point payloads.

## Notes

- This is an MVP, not a full production model.
- The prototype uses a simple rectangular partitioning strategy.
- Rule checks and scoring are intentionally lightweight.
- Adjacency policy is externalized to `configs/policies/3br_adjacency_policy.json` and merged at config load time.
- Adjacency policy now supports soft/hard severity levels for more explicit rule handling.
- Added a focused rule-checker test for policy merge, normalization, and severity split.
- Added a minimal test runner at `tests/run_tests.py`.
- Added a minimal SVG plan exporter at `tools/make_plan_svg.py`.
- Added a second policy variant at `configs/policies/3br_adjacency_policy_variant.json`.
- Added a focused SVG test at `tests/test_plan_svg.py`.
- Added a policy switcher at `tools/switch_policy.py`.
- Added a round-trip test for policy switching at `tests/test_switch_policy.py`.
- Added a default-vs-variant comparison tool at `tools/compare_policies.py`.
- Added a comparison plan exporter at `tools/make_comparison_svg.py`.
- Added a focused comparison SVG test at `tests/test_comparison_svg.py`.
- Added a top-N plan collage tool at `tools/make_top_plans_svg.py`.
- Added a top-N report generator at `tools/generate_top_plans.py`.
- Added a rule registry abstraction at `gh/scripts/rule_registry.py`.
- Added a focused rule-registry test at `tests/test_rule_registry.py`.
- Added a dashboard builder at `tools/make_dashboard.py`.
- Added dashboard HTML generation at `results/dashboard.html`.
- Added multi-unit matrix support via `configs/unit_matrix.json` and `tools/run_unit_matrix.py`.
- Later stages should focus on:
  - richer layout logic
  - more robust adjacency / circulation
  - Rhino geometry conversion
  - unit tests
  - batch visualization
  - eliminating warnings such as dead-end bathrooms
