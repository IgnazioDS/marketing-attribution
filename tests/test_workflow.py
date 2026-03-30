from pathlib import Path
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def test_full_workflow_generates_expected_outputs(tmp_path) -> None:
    data_path = tmp_path / "touchpoints.csv"
    charts_dir = tmp_path / "charts"
    reports_dir = tmp_path / "reports"

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "run_analysis.py"),
            "--seed",
            "17",
            "--journeys",
            "350",
            "--data-path",
            str(data_path),
            "--charts-dir",
            str(charts_dir),
            "--reports-dir",
            str(reports_dir),
        ],
        check=True,
        cwd=ROOT,
    )

    assert data_path.exists()
    assert (charts_dir / "channel_revenue_by_model.png").exists()
    assert (charts_dir / "roas_heatmap.png").exists()
    assert (charts_dir / "conversion_path_lengths.png").exists()
    assert (reports_dir / "channel_model_summary.csv").exists()
    assert (reports_dir / "channel_recommendations.csv").exists()
    assert (reports_dir / "top_paths.csv").exists()
    assert (reports_dir / "executive_summary.md").exists()

    recommendations = pd.read_csv(reports_dir / "channel_recommendations.csv")
    invest = recommendations[recommendations["primary_recommendation"] == "invest"]
    assert not invest.empty
    assert bool(invest.iloc[0]["eligible_invest"])
    assert invest.iloc[0]["time_decay_roas"] >= 12.0

    top_paths = pd.read_csv(reports_dir / "top_paths.csv")
    for path in top_paths["path"]:
        channels = path.split(" > ")
        assert len(channels) == len(set(channels))

    summary = (reports_dir / "executive_summary.md").read_text(encoding="utf-8")
    assert "Increase investment in" in summary
    assert "channel_recommendations.csv" in summary
    assert "Reallocate 10-15%" not in summary
