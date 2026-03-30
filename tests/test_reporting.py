import pandas as pd

from marketing_attribution.reporting import RECOMMENDATION_THRESHOLDS, build_recommendation_table


def test_recommendation_engine_rejects_low_roas_invest_candidate() -> None:
    scorecard = pd.DataFrame(
        [
            {
                "channel": "webinar",
                "is_paid_channel": 1,
                "spend": 200000,
                "last_touch_revenue": 1000000,
                "time_decay_revenue": 3500000,
                "time_decay_uplift": 2500000,
                "time_decay_uplift_pct": 2.5,
                "time_decay_roas": 6.0,
            },
            {
                "channel": "google_search",
                "is_paid_channel": 1,
                "spend": 250000,
                "last_touch_revenue": 2800000,
                "time_decay_revenue": 4300000,
                "time_decay_uplift": 1500000,
                "time_decay_uplift_pct": 0.54,
                "time_decay_roas": 18.0,
            },
            {
                "channel": "partner_referral",
                "is_paid_channel": 1,
                "spend": 300000,
                "last_touch_revenue": 5200000,
                "time_decay_revenue": 2900000,
                "time_decay_uplift": -2300000,
                "time_decay_uplift_pct": -0.44,
                "time_decay_roas": 9.5,
            },
        ]
    )

    recommendations = build_recommendation_table(scorecard)
    invest_row = recommendations[recommendations["primary_recommendation"] == "invest"].iloc[0]

    assert invest_row["channel"] == "google_search"
    assert recommendations.loc[recommendations["channel"] == "webinar", "eligible_invest"].iloc[0] == 0


def test_recommendation_engine_prefers_uplift_plus_efficiency() -> None:
    scorecard = pd.DataFrame(
        [
            {
                "channel": "linkedin_ads",
                "is_paid_channel": 1,
                "spend": 100000,
                "last_touch_revenue": 0,
                "time_decay_revenue": 2800000,
                "time_decay_uplift": 2800000,
                "time_decay_uplift_pct": None,
                "time_decay_roas": RECOMMENDATION_THRESHOLDS["min_roas"] + 1,
            },
            {
                "channel": "google_search",
                "is_paid_channel": 1,
                "spend": 220000,
                "last_touch_revenue": 2600000,
                "time_decay_revenue": 4500000,
                "time_decay_uplift": 1900000,
                "time_decay_uplift_pct": 0.73,
                "time_decay_roas": 20.0,
            },
            {
                "channel": "retargeting",
                "is_paid_channel": 1,
                "spend": 85000,
                "last_touch_revenue": 5200000,
                "time_decay_revenue": 3200000,
                "time_decay_uplift": -2000000,
                "time_decay_uplift_pct": -0.38,
                "time_decay_roas": 55.0,
            },
            {
                "channel": "partner_referral",
                "is_paid_channel": 1,
                "spend": 240000,
                "last_touch_revenue": 4800000,
                "time_decay_revenue": 2600000,
                "time_decay_uplift": -2200000,
                "time_decay_uplift_pct": -0.46,
                "time_decay_roas": 10.0,
            },
        ]
    )

    recommendations = build_recommendation_table(scorecard)
    invest_row = recommendations[recommendations["primary_recommendation"] == "invest"].iloc[0]
    trim_row = recommendations[recommendations["primary_recommendation"] == "trim"].iloc[0]

    assert invest_row["channel"] == "google_search"
    assert trim_row["channel"] == "partner_referral"
