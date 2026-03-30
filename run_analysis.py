"""Run the full attribution workflow and export client-facing outputs."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from marketing_attribution.data_generation import DEFAULT_SEED, generate_touchpoint_dataset
from marketing_attribution.models import build_attribution_report, load_touchpoints
from marketing_attribution.reporting import (
    build_executive_summary,
    build_recommendation_table,
    create_path_length_chart,
    create_revenue_chart,
    create_roas_heatmap,
    ensure_dirs,
    export_executive_summary,
    export_tables,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the B2B attribution case study outputs.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Seed used for synthetic data generation.")
    parser.add_argument("--journeys", type=int, default=4500, help="Number of buying journeys to generate.")
    parser.add_argument("--data-path", default=str(ROOT / "data" / "touchpoints.csv"), help="Touchpoint CSV path.")
    parser.add_argument("--charts-dir", default=str(ROOT / "charts"), help="Directory for exported charts.")
    parser.add_argument("--reports-dir", default=str(ROOT / "reports"), help="Directory for exported reports.")
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse an existing dataset instead of regenerating it.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data_path)
    charts_dir = Path(args.charts_dir)
    reports_dir = Path(args.reports_dir)

    ensure_dirs(data_path.parent, charts_dir, reports_dir)

    if not args.reuse_existing or not data_path.exists():
        generate_touchpoint_dataset(data_path, journeys=args.journeys, seed=args.seed)

    df = load_touchpoints(data_path)
    report = build_attribution_report(df)
    report["recommendations"] = build_recommendation_table(report["channel_scorecard"])

    create_revenue_chart(report["revenue_pivot"], charts_dir / "channel_revenue_by_model.png")
    create_roas_heatmap(report["roas_pivot"], charts_dir / "roas_heatmap.png")
    create_path_length_chart(report["path_lengths"], charts_dir / "conversion_path_lengths.png")
    export_tables(report, reports_dir)

    summary = build_executive_summary(df, report)
    export_executive_summary(summary, reports_dir / "executive_summary.md")

    print("Analysis complete.")
    print(f"Dataset: {data_path}")
    print(f"Charts: {charts_dir / 'channel_revenue_by_model.png'}, {charts_dir / 'roas_heatmap.png'}, {charts_dir / 'conversion_path_lengths.png'}")
    print(f"Reports: {reports_dir / 'channel_model_summary.csv'}, {reports_dir / 'channel_recommendations.csv'}, {reports_dir / 'top_paths.csv'}, {reports_dir / 'executive_summary.md'}")


if __name__ == "__main__":
    main()
