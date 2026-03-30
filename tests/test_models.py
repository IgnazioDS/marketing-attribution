import math

import pandas as pd

from marketing_attribution.models import (
    aggregate_model_results,
    build_attribution_report,
    last_touch_attribution,
    time_decay_attribution,
    u_shaped_attribution,
)


def sample_touchpoints() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "journey_id": 1,
                "account_id": 10,
                "segment": "Mid-Market",
                "region": "North America",
                "industry": "SaaS",
                "channel": "linkedin_ads",
                "funnel_stage": "awareness",
                "touch_timestamp": pd.Timestamp("2024-01-01"),
                "conversion_timestamp": pd.Timestamp("2024-01-10"),
                "days_to_conversion": 9.0,
                "touch_position": 1,
                "total_touches": 3,
                "cost": 100.0,
                "is_paid_channel": 1,
                "converted": 1,
                "revenue": 3000.0,
            },
            {
                "journey_id": 1,
                "account_id": 10,
                "segment": "Mid-Market",
                "region": "North America",
                "industry": "SaaS",
                "channel": "webinar",
                "funnel_stage": "consideration",
                "touch_timestamp": pd.Timestamp("2024-01-05"),
                "conversion_timestamp": pd.Timestamp("2024-01-10"),
                "days_to_conversion": 5.0,
                "touch_position": 2,
                "total_touches": 3,
                "cost": 220.0,
                "is_paid_channel": 1,
                "converted": 1,
                "revenue": 3000.0,
            },
            {
                "journey_id": 1,
                "account_id": 10,
                "segment": "Mid-Market",
                "region": "North America",
                "industry": "SaaS",
                "channel": "direct",
                "funnel_stage": "decision",
                "touch_timestamp": pd.Timestamp("2024-01-09"),
                "conversion_timestamp": pd.Timestamp("2024-01-10"),
                "days_to_conversion": 1.0,
                "touch_position": 3,
                "total_touches": 3,
                "cost": 0.0,
                "is_paid_channel": 0,
                "converted": 1,
                "revenue": 3000.0,
            },
        ]
    )


def test_all_models_preserve_total_revenue() -> None:
    df = sample_touchpoints()
    expected = df.groupby("journey_id")["revenue"].max().sum()

    results = aggregate_model_results(df)
    totals = results.groupby("model")["attributed_revenue"].sum()

    for total in totals:
        assert math.isclose(total, expected, rel_tol=1e-9)


def test_time_decay_favors_late_touches() -> None:
    summary = time_decay_attribution(sample_touchpoints(), half_life_days=7)
    direct = summary.loc[summary["channel"] == "direct", "attributed_revenue"].iloc[0]
    linkedin = summary.loc[summary["channel"] == "linkedin_ads", "attributed_revenue"].iloc[0]
    assert direct > linkedin


def test_u_shaped_emphasizes_first_and_last_touch() -> None:
    summary = u_shaped_attribution(sample_touchpoints(), first_touch_weight=0.4, last_touch_weight=0.4)
    direct = summary.loc[summary["channel"] == "direct", "attributed_revenue"].iloc[0]
    webinar = summary.loc[summary["channel"] == "webinar", "attributed_revenue"].iloc[0]
    linkedin = summary.loc[summary["channel"] == "linkedin_ads", "attributed_revenue"].iloc[0]
    assert direct > webinar
    assert linkedin > webinar


def test_last_touch_assigns_full_credit_to_final_touch() -> None:
    summary = last_touch_attribution(sample_touchpoints())
    direct = summary.loc[summary["channel"] == "direct", "attributed_revenue"].iloc[0]
    assert direct == 3000.0
    assert summary["attributed_revenue"].sum() == 3000.0


def test_report_includes_channel_scorecard() -> None:
    report = build_attribution_report(sample_touchpoints())
    assert "channel_scorecard" in report
    assert {"channel", "time_decay_uplift", "time_decay_roas"}.issubset(report["channel_scorecard"].columns)
