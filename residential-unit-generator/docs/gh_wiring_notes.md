# Minimal Grasshopper wiring for Residential Unit Generator

This file is a lightweight reference for wiring the generated GH component into Rhino without building a full `.gh` package yet.

## Inputs

| Input | Suggested wire | Notes |
|---|---|---|
| `config_path` | File path text | Point to `residential-unit-generator/configs/default_3br.json` |
| `count` | Number | Default 20 |
| `seed_start` | Number | Default 0 |
| `out_dir` | Folder path text | Default `residential-unit-generator/results` |

## Outputs

| Output | Suggested downstream use |
|---|---|
| `out` | Display summary JSON in a panel |
| `top_result` | Store best unit JSON in a file / panel |
| `summary_path` | Reference the CSV summary path |
| `geometry` | Batch geometry payload for panels / debugging |
| `rooms` | Draw room outlines with a polyline / curve component |
| `walls` | Draw wall segments as curves |
| `doors` | Draw door locations as points |
| `points` | Optional room point cloud for debugging |
| `rhino_objects` | Ready-to-use Rhino geometry objects when Rhino is available |

## Recommended minimal graph

```text
File Path -> config_path
Number -> count
Number -> seed_start
File Path -> out_dir
                         │
                         ▼
              Residential Unit Generator
                         │
        ┌────────────────┼────────────────┬────────────────┬──────────────┐
        ▼                ▼                ▼                ▼              ▼
    Panel(summary)   Curve Room      Line Wall        Point Door   Panel(top_result)
      (out)          (rooms)          (walls)           (doors)
```

## Notes

- `rooms` are 2D polygon outlines in the unit coordinate system.
- `doors` and `points` are also 2D coordinate lists and can be projected to Rhino plane view.
- `walls` may be sparse in the MVP because the current prototype only creates shared-edge segments where rooms are directly adjacent.
- `rhino_objects` is produced by the helper in `residential-unit-generator/gh/scripts/rhino_writer.py` via `convert_to_rhino_objects(top_result)`.

## Matrix generator component

`ResidentialUnitMatrixGenerator` is a lightweight Grasshopper wrapper for running the unit matrix.

### Inputs

| Input | Suggested wire | Notes |
|---|---|---|
| `matrix_path` | File path text | Point to `residential-unit-generator/configs/unit_matrix.json` |
| `out_dir` | Folder path text | Default `results/unit_matrix` |

### Outputs

| Output | Suggested downstream use |
|---|---|---|
| `summary` | Matrix summary JSON |
| `summary_path` | Path to `matrix_summary.csv` |
| `report` | Raw matrix report JSON |
| `best_unit_svg_paths` | JSON array of generated best-unit SVG paths |

### Notes

- The matrix wrapper runs the same matrix logic used by the CLI runner.
- Use the dashboard to inspect the matrix report after a run.
- If you add more matrix configs, update `configs/unit_matrix.json` first, then rerun the matrix component.

## Policy matrix component

`ResidentialPolicyMatrixGenerator` runs default vs variant adjacency-policy comparisons across all configs in the unit matrix.

### Inputs

| Input | Suggested wire | Notes |
|---|---|---|
| `matrix_path` | File path text | Point to `residential-unit-generator/configs/unit_matrix.json` |
| `out_dir` | Folder path text | Default `results/policy_matrix` |
| `count` | Number | Usually `1` for report generation, `5` for scoring samples |

### Outputs

| Output | Suggested downstream use |
|---|---|
| `summary` | Policy matrix summary JSON with report path, item counts, SVG path count, and comparison SVG list |
| `summary_path` | Path to `policy_matrix_summary.csv` |
| `report` | Path to raw `policy_matrix_report.json` |
| `comparison_svg_paths` | JSON array of generated comparison SVG paths |

### Notes

- Use the dashboard's **Policy matrix** section to inspect aggregate results.
- If a unit has no variant policy file, the wrapper records the failure in the matrix report instead of stopping the whole run.

## Report pack helper

`tools/generate_report_pack.py` runs the unit matrix, policy matrix, and dashboard in one pass.

### Grasshopper wrapper

`ResidentialReportPackGenerator` wraps the same helper for GH.

### Inputs

| Input | Suggested wire | Notes |
|---|---|---|
| `matrix_path` | File path text | Point to `residential-unit-generator/configs/unit_matrix.json` |
| `out_dir` | Folder path text | Default `results` |
| `unit_count` | Number | Default 5 |
| `policy_count` | Number | Default 1 |
| `dry_run` | Boolean | Default false |
| `skip_dashboard` | Boolean | Default false |
| `verify` | Boolean | Default false |

### Outputs

| Output | Suggested downstream use |
|---|---|
| `stdout` | Console text from the report pack helper |
| `stderr` | Console error text from the report pack helper |
| `script_path` | Path to `generate_report_pack.py` |
| `args` | Argument list used to launch the helper |
| `summary_path` | Path to the machine-readable `report_pack_summary.json` |
| `summary_json` | JSON summary with paths for unit report, policy report, dashboard, `dry_run`, `skip_dashboard`, `verify`, `summary_path`, and when available `started_at`/`finished_at` |

### Example

```bash
python residential-unit-generator/tools/generate_report_pack.py residential-unit-generator/configs/unit_matrix.json --unit-count 5 --policy-count 1
```

### Optional flags

- `--dry-run`: print the commands that would run without executing them
- `--skip-dashboard`: run matrices only, skip dashboard regeneration
- `--verify`: check whether the expected report artifacts exist without running generation
- `--json-summary`: write a machine-readable summary JSON next to the run artifacts (default `report_pack_summary.json`)

### Notes

- Writes `results/unit_matrix/matrix_report.json`
- Writes `results/policy_matrix/policy_matrix_report.json`
- Writes `results/dashboard.html` unless `--skip-dashboard` is used
- Writes `results/report_pack_summary.json` for machine-readable run metadata
- Useful as a local sanity check before wiring the GH components in Rhino

## Suggested next step

Once the wiring is verified in Rhino, add a second component that consumes `top_result` and writes Rhino blocks/layers/text labels.
