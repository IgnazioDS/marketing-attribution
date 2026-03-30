"""CLI entry point for generating the synthetic B2B attribution dataset."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from marketing_attribution.data_generation import DEFAULT_SEED, generate_touchpoint_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the synthetic B2B attribution dataset.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Seed for deterministic dataset generation.")
    parser.add_argument("--journeys", type=int, default=4500, help="Number of journeys to create.")
    parser.add_argument(
        "--output-path",
        default=str(ROOT / "data" / "touchpoints.csv"),
        help="CSV output path.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    df = generate_touchpoint_dataset(args.output_path, journeys=args.journeys, seed=args.seed)
    print(
        f"Generated {len(df):,} touchpoints across {df['journey_id'].nunique():,} buying journeys "
        f"-> {Path(args.output_path).resolve()}"
    )
