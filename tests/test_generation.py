import pandas as pd

from marketing_attribution.data_generation import STAGE_INDEX, generate_touchpoint_dataset, journey_quality_metrics


def test_generation_is_deterministic_for_fixed_seed(tmp_path) -> None:
    output_a = tmp_path / "a.csv"
    output_b = tmp_path / "b.csv"

    df_a = generate_touchpoint_dataset(output_a, journeys=250, seed=7)
    df_b = generate_touchpoint_dataset(output_b, journeys=250, seed=7)

    pd.testing.assert_frame_equal(df_a.reset_index(drop=True), df_b.reset_index(drop=True))


def test_generated_journeys_stay_in_credible_range(tmp_path) -> None:
    df = generate_touchpoint_dataset(tmp_path / "touchpoints.csv", journeys=600, seed=11)
    metrics = journey_quality_metrics(df)

    assert 0.12 <= metrics["conversion_rate"] <= 0.28
    assert metrics["adjacent_repeat_rate"] == 0.0
    assert metrics["repeat_any_rate"] <= 0.20
    assert metrics["avg_stage_regressions"] <= 0.30


def test_stage_progression_is_valid(tmp_path) -> None:
    df = generate_touchpoint_dataset(tmp_path / "touchpoints.csv", journeys=400, seed=3)
    journeys = (
        df.sort_values(["journey_id", "touch_timestamp"])
        .groupby("journey_id")
        .agg(stages=("funnel_stage", list))
    )

    for stages in journeys["stages"]:
        assert stages[0] == "awareness"
        assert stages[-1] == "decision"
        regressions = sum(
            1
            for left, right in zip(stages, stages[1:])
            if STAGE_INDEX[right] < STAGE_INDEX[left]
        )
        assert regressions <= 1
