import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gh.scripts.config_loader import load_config, validate_config
from gh.scripts.batch_runner import generate_batch, rank_results, write_summary, write_unit_json


def main():
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("configs/default_3br.json")
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    out_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("results")

    config = load_config(config_path)
    validate_config(config)
    results = generate_batch(config, count=count, seed_start=0)
    results = rank_results(results)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_summary(results, out_dir / "batch_summary.csv")
    for result in results[:20]:
        write_unit_json(result, out_dir)

    print(f"generated={len(results)} valid={sum(1 for r in results if r['status']=='valid')} top_score={results[0]['score'] if results else 0}")


if __name__ == "__main__":
    main()
