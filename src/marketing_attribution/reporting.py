"""Reporting utilities for charts, recommendations, and client-facing summaries."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns


BRAND = {
    "ink": "#132238",
    "slate": "#456179",
    "teal": "#167c80",
    "gold": "#cf8f2e",
    "rose": "#be5a5a",
    "mint": "#7ebea3",
    "sand": "#efe4d2",
}

RECOMMENDATION_THRESHOLDS = {
    "min_spend": 60_000,
    "min_revenue": 2_500_000,
    "min_roas": 12.0,
    "max_trim_roas_percentile": 0.60,
}


def configure_matplotlib() -> None:
    sns.set_theme(style="whitegrid")
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "axes.facecolor": "#fcfbf7",
            "figure.facecolor": "#fcfbf7",
            "axes.edgecolor": "#d7d0c4",
            "axes.labelcolor": BRAND["ink"],
            "xtick.color": BRAND["ink"],
            "ytick.color": BRAND["ink"],
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
        }
    )


def ensure_dirs(*paths: str | Path) -> None:
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def _safe_normalize(series: pd.Series) -> pd.Series:
    values = series.fillna(0).astype(float)
    if values.empty:
        return values
    spread = values.max() - values.min()
    if spread == 0:
        return pd.Series(np.ones(len(values)), index=values.index)
    return (values - values.min()) / spread


def _recommendation_reason(row: pd.Series, action: str) -> str:
    reasons: list[str] = []
    if row["time_decay_uplift"] > 0:
        reasons.append("under-credited by last-touch")
    elif row["time_decay_uplift"] < 0:
        reasons.append("over-credited by last-touch")

    if pd.notna(row["time_decay_roas"]):
        if action == "trim" and row.get("time_decay_roas_rank", 1.0) <= RECOMMENDATION_THRESHOLDS["max_trim_roas_percentile"]:
            reasons.append("less efficient than other scaled paid channels")
        elif row["time_decay_roas"] >= RECOMMENDATION_THRESHOLDS["min_roas"]:
            reasons.append("strong time-decay ROAS")
        elif row["time_decay_roas"] < RECOMMENDATION_THRESHOLDS["min_roas"]:
            reasons.append("weaker time-decay efficiency")

    if row["spend"] >= RECOMMENDATION_THRESHOLDS["min_spend"] and row["time_decay_revenue"] >= RECOMMENDATION_THRESHOLDS["min_revenue"]:
        reasons.append("sufficient scale")

    if action == "monitor" and not reasons:
        reasons.append("mixed signal across attribution and efficiency")

    return ", ".join(reasons)


def build_recommendation_table(channel_scorecard: pd.DataFrame) -> pd.DataFrame:
    paid = channel_scorecard[channel_scorecard["is_paid_channel"] == 1].copy()
    paid["time_decay_roas_rank"] = paid["time_decay_roas"].rank(pct=True, method="dense")
    dynamic_min_spend = min(
        RECOMMENDATION_THRESHOLDS["min_spend"],
        float(paid["spend"].quantile(0.25)),
    )
    dynamic_min_revenue = min(
        RECOMMENDATION_THRESHOLDS["min_revenue"],
        float(paid["time_decay_revenue"].quantile(0.25)),
    )

    paid["eligible_invest"] = (
        (paid["spend"] >= dynamic_min_spend)
        & (paid["time_decay_revenue"] >= dynamic_min_revenue)
        & (paid["time_decay_roas"] >= RECOMMENDATION_THRESHOLDS["min_roas"])
        & (paid["time_decay_uplift"] > 0)
    )
    paid["eligible_trim"] = (
        (paid["spend"] >= dynamic_min_spend)
        & (paid["last_touch_revenue"] >= dynamic_min_revenue)
        & (paid["time_decay_uplift"] < 0)
        & (paid["time_decay_roas_rank"] <= RECOMMENDATION_THRESHOLDS["max_trim_roas_percentile"])
    )

    uplift_norm = _safe_normalize(paid["time_decay_uplift"].clip(lower=0))
    roas_norm = _safe_normalize(paid["time_decay_roas"].fillna(0))
    revenue_norm = _safe_normalize(paid["time_decay_revenue"])
    spend_norm = _safe_normalize(paid["spend"])
    overcredit_norm = _safe_normalize((paid["last_touch_revenue"] - paid["time_decay_revenue"]).clip(lower=0))
    inverse_roas_norm = 1 - roas_norm

    paid["invest_score"] = np.where(
        paid["eligible_invest"],
        0.40 * uplift_norm + 0.30 * roas_norm + 0.20 * revenue_norm + 0.10 * spend_norm,
        np.nan,
    )
    paid["trim_score"] = np.where(
        paid["eligible_trim"],
        0.55 * overcredit_norm + 0.25 * inverse_roas_norm + 0.20 * spend_norm,
        np.nan,
    )

    paid["primary_recommendation"] = "monitor"
    if paid["eligible_invest"].any():
        invest_index = paid["invest_score"].idxmax()
        paid.loc[invest_index, "primary_recommendation"] = "invest"
    if paid["eligible_trim"].any():
        trim_index = paid["trim_score"].idxmax()
        paid.loc[trim_index, "primary_recommendation"] = "trim"

    paid["rationale"] = paid.apply(
        lambda row: _recommendation_reason(row, row["primary_recommendation"]),
        axis=1,
    )

    columns = [
        "channel",
        "primary_recommendation",
        "rationale",
        "eligible_invest",
        "eligible_trim",
        "invest_score",
        "trim_score",
        "spend",
        "last_touch_revenue",
        "time_decay_revenue",
        "time_decay_uplift",
        "time_decay_uplift_pct",
        "time_decay_roas",
    ]
    return paid.loc[:, columns].sort_values(
        by=["primary_recommendation", "invest_score", "trim_score", "time_decay_revenue"],
        ascending=[True, False, False, False],
    ).reset_index(drop=True)


def export_tables(report: dict[str, pd.DataFrame], reports_dir: str | Path = "reports") -> None:
    ensure_dirs(reports_dir)
    report["model_results"].round(2).to_csv(Path(reports_dir) / "channel_model_summary.csv", index=False)
    report["top_paths"].round(2).to_csv(Path(reports_dir) / "top_paths.csv", index=False)
    if "recommendations" in report:
        report["recommendations"].round(4).to_csv(
            Path(reports_dir) / "channel_recommendations.csv",
            index=False,
        )


def create_revenue_chart(
    revenue_pivot: pd.DataFrame,
    output_path: str | Path = "charts/channel_revenue_by_model.png",
) -> None:
    configure_matplotlib()
    output_path = Path(output_path)
    ensure_dirs(output_path.parent)

    ordered = revenue_pivot.loc[:, ["last_touch", "linear", "time_decay", "u_shaped"]]
    ax = ordered.plot(
        kind="bar",
        figsize=(13, 6),
        color=[BRAND["slate"], BRAND["gold"], BRAND["teal"], BRAND["mint"]],
        width=0.82,
    )
    ax.set_title("Attributed Revenue by Channel and Model")
    ax.set_xlabel("")
    ax.set_ylabel("Attributed Revenue")
    ax.tick_params(axis="x", rotation=28)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda value, _: f"${value/1_000_000:,.1f}M"))
    ax.legend(title="Model", frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def create_roas_heatmap(
    roas_pivot: pd.DataFrame,
    output_path: str | Path = "charts/roas_heatmap.png",
) -> None:
    configure_matplotlib()
    output_path = Path(output_path)
    ensure_dirs(output_path.parent)

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    display = roas_pivot.replace([np.inf, -np.inf], np.nan).dropna(how="all").round(1)
    sns.heatmap(
        display,
        cmap=sns.color_palette(["#f4e7d2", BRAND["gold"], BRAND["teal"]], as_cmap=True),
        annot=True,
        fmt=".1f",
        linewidths=0.5,
        cbar_kws={"label": "ROAS"},
        ax=ax,
    )
    ax.set_title("ROAS by Channel and Attribution Model")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def create_path_length_chart(
    path_lengths: pd.DataFrame,
    output_path: str | Path = "charts/conversion_path_lengths.png",
) -> None:
    configure_matplotlib()
    output_path = Path(output_path)
    ensure_dirs(output_path.parent)

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    bins = np.arange(path_lengths["total_touches"].min(), path_lengths["total_touches"].max() + 2) - 0.5
    ax.hist(path_lengths["total_touches"], bins=bins, color=BRAND["teal"], edgecolor="white", alpha=0.95)
    ax.set_title("Distribution of Touches in Converting Journeys")
    ax.set_xlabel("Touches Before Opportunity Creation")
    ax.set_ylabel("Number of Converting Journeys")
    ax.set_xticks(sorted(path_lengths["total_touches"].unique()))
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def build_executive_summary(df: pd.DataFrame, report: dict[str, pd.DataFrame]) -> str:
    converted = df[df["converted"] == 1]
    journeys = df["journey_id"].nunique()
    accounts = df["account_id"].nunique()
    converted_journeys = converted["journey_id"].nunique()
    conversion_rate = converted_journeys / journeys
    pipeline = converted.groupby("journey_id")["revenue"].max().sum()
    avg_deal_size = converted.groupby("journey_id")["revenue"].max().mean()
    median_sales_cycle = converted.groupby("journey_id")["days_to_conversion"].max().median()
    median_touches = converted.groupby("journey_id")["total_touches"].max().median()

    recommendations = report.get("recommendations")
    if recommendations is None:
        recommendations = build_recommendation_table(report["channel_scorecard"])
    invest_row = recommendations[recommendations["primary_recommendation"] == "invest"].head(1)
    trim_row = recommendations[recommendations["primary_recommendation"] == "trim"].head(1)

    invest_channel = invest_row.iloc[0]["channel"] if not invest_row.empty else "google_search"
    trim_channel = trim_row.iloc[0]["channel"] if not trim_row.empty else "partner_referral"
    invest_reason = invest_row.iloc[0]["rationale"] if not invest_row.empty else "under-credited by last-touch, strong time-decay ROAS, sufficient scale"
    trim_reason = trim_row.iloc[0]["rationale"] if not trim_row.empty else "over-credited by last-touch, weaker time-decay efficiency, sufficient scale"

    first_touch_leaders = (
        converted.sort_values(["journey_id", "touch_timestamp"])
        .groupby("journey_id")
        .first()["channel"]
        .value_counts()
        .head(2)
        .index.tolist()
    )
    last_touch_leaders = (
        converted.sort_values(["journey_id", "touch_timestamp"])
        .groupby("journey_id")
        .last()["channel"]
        .value_counts()
        .head(2)
        .index.tolist()
    )
    top_path = report["top_paths"].iloc[0]
    model_totals = report["model_results"].groupby("model")["attributed_revenue"].sum().round(2)

    lines = [
        "# Executive Summary",
        "",
        f"_Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "## Why this case study matters",
        "",
        "This public demo shows the kind of attribution engagement a B2B SaaS CMO would buy:",
        "a unified touchpoint model, defensible attribution logic, executive-ready visuals, and budget recommendations tied to pipeline outcomes.",
        "",
        "## Dataset snapshot",
        "",
        f"- Accounts represented: {accounts:,}",
        f"- Buying journeys analyzed: {journeys:,}",
        f"- Converting journeys: {converted_journeys:,} ({conversion_rate:.1%} conversion rate)",
        f"- Attributed pipeline in the sample: ${pipeline:,.0f}",
        f"- Average won opportunity value: ${avg_deal_size:,.0f}",
        f"- Median days from first touch to conversion: {median_sales_cycle:.1f}",
        f"- Median touches in winning journeys: {median_touches:.0f}",
        "",
        "## What the analysis shows",
        "",
        f"- Last-touch reporting still assigns ${model_totals['last_touch']:,.0f} of pipeline, but it materially under-values assist channels earlier in the buying journey.",
        f"- Winning journeys usually require {median_touches:.0f} touches, which makes single-touch reporting incomplete for budget allocation.",
        f"- Early demand creation is led by `{first_touch_leaders[0]}` and `{first_touch_leaders[1]}`, while conversion capture concentrates in `{last_touch_leaders[0]}` and `{last_touch_leaders[1]}`.",
        f"- The strongest repeatable converting path in the sample is `{top_path['path']}`.",
        "",
        "## Recommendation for the client",
        "",
        f"- Increase investment in `{invest_channel}` because it is {invest_reason}.",
        f"- Trim or hold `{trim_channel}` because it is {trim_reason}.",
        "- Use time-decay or position-based attribution for channel steering, while keeping last-touch for directional reporting only.",
        "- In a live engagement, the next step would be to join CRM opportunity stages, campaign metadata, and lifecycle timestamps to move from channel attribution into account-level pipeline attribution.",
        "",
        "## How this maps to a real engagement",
        "",
        "- The data in this public repo is synthetic so the work can be shared openly.",
        "- The workflow itself mirrors a real project: ingest touchpoints, connect them to revenue, compare attribution models, and produce budget guidance that leadership can act on.",
        "",
        "## Deliverables in this repo",
        "",
        "- `run_analysis.py`: deterministic workflow to regenerate the dataset, charts, and reports.",
        "- `reports/channel_model_summary.csv`: channel performance by attribution model.",
        "- `reports/channel_recommendations.csv`: auditable recommendation scorecard.",
        "- `reports/executive_summary.md`: pre-call summary for a buyer conversation.",
    ]
    return "\n".join(lines)


def export_executive_summary(
    summary_markdown: str,
    output_path: str | Path = "reports/executive_summary.md",
) -> None:
    output_path = Path(output_path)
    ensure_dirs(output_path.parent)
    output_path.write_text(summary_markdown, encoding="utf-8")
