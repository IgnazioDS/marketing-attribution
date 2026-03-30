"""Attribution models and summary builders."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def load_touchpoints(path: str | Path = "data/touchpoints.csv") -> pd.DataFrame:
    df = pd.read_csv(
        path,
        parse_dates=["touch_timestamp", "conversion_timestamp"],
    )
    df = df.sort_values(["journey_id", "touch_timestamp"]).reset_index(drop=True)
    return df


def _converted_touchpoints(df: pd.DataFrame) -> pd.DataFrame:
    converted = df[df["converted"] == 1].copy()
    if converted.empty:
        raise ValueError("Dataset does not contain any converted journeys.")
    return converted


def _attach_common_weighted_metrics(
    weighted: pd.DataFrame,
    all_touchpoints: pd.DataFrame,
    model_name: str,
) -> pd.DataFrame:
    spend = all_touchpoints.groupby("channel")["cost"].sum()
    summary = (
        weighted.groupby("channel")
        .agg(
            attributed_revenue=("attributed_revenue", "sum"),
            attributed_conversions=("attributed_conversions", "sum"),
            assisted_touchpoints=("journey_id", "count"),
        )
        .join(spend.rename("spend"), how="outer")
        .fillna(0)
        .reset_index()
    )
    summary["roas"] = np.where(
        summary["spend"] > 0,
        summary["attributed_revenue"] / summary["spend"],
        np.nan,
    )
    summary["model"] = model_name
    return summary.sort_values("attributed_revenue", ascending=False).reset_index(drop=True)


def last_touch_attribution(df: pd.DataFrame) -> pd.DataFrame:
    converted = _converted_touchpoints(df)
    last_touch = converted.loc[converted.groupby("journey_id")["touch_timestamp"].idxmax()].copy()
    last_touch["attributed_revenue"] = last_touch["revenue"]
    last_touch["attributed_conversions"] = 1.0
    return _attach_common_weighted_metrics(last_touch, df, "last_touch")


def linear_attribution(df: pd.DataFrame) -> pd.DataFrame:
    converted = _converted_touchpoints(df)
    converted["weight"] = 1.0 / converted["total_touches"]
    converted["attributed_revenue"] = converted["revenue"] * converted["weight"]
    converted["attributed_conversions"] = converted["weight"]
    return _attach_common_weighted_metrics(converted, df, "linear")


def time_decay_attribution(df: pd.DataFrame, half_life_days: float = 14.0) -> pd.DataFrame:
    converted = _converted_touchpoints(df)
    converted["raw_weight"] = np.power(0.5, converted["days_to_conversion"] / half_life_days)
    converted["weight"] = converted["raw_weight"] / converted.groupby("journey_id")["raw_weight"].transform("sum")
    converted["attributed_revenue"] = converted["revenue"] * converted["weight"]
    converted["attributed_conversions"] = converted["weight"]
    return _attach_common_weighted_metrics(converted, df, "time_decay")


def u_shaped_attribution(
    df: pd.DataFrame,
    first_touch_weight: float = 0.4,
    last_touch_weight: float = 0.4,
) -> pd.DataFrame:
    converted = _converted_touchpoints(df)
    middle_weight = max(0.0, 1.0 - first_touch_weight - last_touch_weight)
    weighted = converted.copy()
    weighted["weight"] = np.where(
        weighted["total_touches"] == 1,
        1.0,
        np.where(
            weighted["total_touches"] == 2,
            0.5,
            middle_weight / (weighted["total_touches"] - 2),
        ),
    )
    weighted.loc[weighted["touch_position"] == 1, "weight"] = np.where(
        weighted.loc[weighted["touch_position"] == 1, "total_touches"] <= 2,
        weighted.loc[weighted["touch_position"] == 1, "weight"],
        first_touch_weight,
    )
    weighted.loc[weighted["touch_position"] == weighted["total_touches"], "weight"] = np.where(
        weighted.loc[weighted["touch_position"] == weighted["total_touches"], "total_touches"] <= 2,
        weighted.loc[weighted["touch_position"] == weighted["total_touches"], "weight"],
        last_touch_weight,
    )
    weighted["attributed_revenue"] = weighted["revenue"] * weighted["weight"]
    weighted["attributed_conversions"] = weighted["weight"]
    return _attach_common_weighted_metrics(weighted, df, "u_shaped")


def aggregate_model_results(df: pd.DataFrame) -> pd.DataFrame:
    models = [
        last_touch_attribution(df),
        linear_attribution(df),
        time_decay_attribution(df),
        u_shaped_attribution(df),
    ]
    return pd.concat(models, ignore_index=True)


def build_attribution_report(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    model_results = aggregate_model_results(df)
    revenue_pivot = (
        model_results.pivot(index="channel", columns="model", values="attributed_revenue")
        .fillna(0)
        .sort_values("time_decay", ascending=False)
    )
    roas_pivot = model_results.pivot(index="channel", columns="model", values="roas").fillna(np.nan)
    conversion_pivot = (
        model_results.pivot(index="channel", columns="model", values="attributed_conversions")
        .fillna(0)
    )
    spend = df.groupby("channel")["cost"].sum().rename("spend")
    paid = df.groupby("channel")["is_paid_channel"].max().rename("is_paid_channel")
    scorecard = revenue_pivot.add_suffix("_revenue").join(
        roas_pivot.add_suffix("_roas"),
        how="left",
    )
    scorecard = scorecard.join(conversion_pivot.add_suffix("_conversions"), how="left")
    scorecard = scorecard.join(spend, how="left").join(paid, how="left").fillna({"spend": 0, "is_paid_channel": 0})
    scorecard["time_decay_uplift"] = scorecard["time_decay_revenue"] - scorecard["last_touch_revenue"]
    scorecard["time_decay_uplift_pct"] = np.where(
        scorecard["last_touch_revenue"] > 0,
        scorecard["time_decay_uplift"] / scorecard["last_touch_revenue"],
        np.nan,
    )
    scorecard = scorecard.reset_index()

    converted = _converted_touchpoints(df)
    path_lengths = (
        converted.groupby("journey_id")
        .agg(total_touches=("total_touches", "max"), revenue=("revenue", "max"))
        .reset_index(drop=True)
    )
    top_paths = (
        converted.sort_values(["journey_id", "touch_timestamp"])
        .groupby("journey_id")
        .agg(
            path=("channel", lambda values: " > ".join(values)),
            revenue=("revenue", "max"),
        )
        .groupby("path")
        .agg(
            journeys=("revenue", "size"),
            revenue=("revenue", "sum"),
        )
        .sort_values(["journeys", "revenue"], ascending=[False, False])
        .head(10)
        .reset_index()
    )

    return {
        "model_results": model_results,
        "revenue_pivot": revenue_pivot,
        "roas_pivot": roas_pivot,
        "channel_scorecard": scorecard,
        "path_lengths": path_lengths,
        "top_paths": top_paths,
    }
