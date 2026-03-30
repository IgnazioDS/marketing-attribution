"""Synthetic B2B SaaS touchpoint generator with stage-aware journey logic."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import math
import random
from typing import Iterable

import pandas as pd


DATA_PATH = Path("data/touchpoints.csv")
DEFAULT_SEED = 42
STAGE_ORDER = ("awareness", "consideration", "decision")
STAGE_INDEX = {stage: index for index, stage in enumerate(STAGE_ORDER)}


@dataclass(frozen=True)
class ChannelProfile:
    name: str
    stage: str
    influence: float
    paid: bool
    cost_low: float
    cost_high: float
    weight: float


CHANNELS: tuple[ChannelProfile, ...] = (
    ChannelProfile("linkedin_ads", "awareness", 1.18, True, 45, 120, 0.28),
    ChannelProfile("organic_search", "awareness", 1.00, False, 0, 0, 0.22),
    ChannelProfile("google_search", "consideration", 1.12, True, 35, 95, 0.25),
    ChannelProfile("webinar", "consideration", 1.32, True, 110, 280, 0.20),
    ChannelProfile("review_sites", "consideration", 1.08, True, 22, 70, 0.15),
    ChannelProfile("email_nurture", "decision", 1.04, True, 4, 16, 0.24),
    ChannelProfile("retargeting", "decision", 1.02, True, 18, 55, 0.23),
    ChannelProfile("partner_referral", "decision", 1.30, True, 120, 320, 0.17),
    ChannelProfile("direct", "decision", 1.05, False, 0, 0, 0.16),
)
CHANNEL_LOOKUP = {channel.name: channel for channel in CHANNELS}
CHANNELS_BY_STAGE = {
    stage: tuple(channel for channel in CHANNELS if channel.stage == stage)
    for stage in STAGE_ORDER
}

SEGMENTS = {
    "SMB": {"base_prob": -3.06, "deal_min": 7000, "deal_max": 22000},
    "Mid-Market": {"base_prob": -2.81, "deal_min": 22000, "deal_max": 70000},
    "Enterprise": {"base_prob": -2.48, "deal_min": 70000, "deal_max": 180000},
}

INDUSTRIES = ("SaaS", "Fintech", "Healthcare", "Manufacturing", "Retail", "Logistics")
REGIONS = ("North America", "EMEA", "APAC")

# Current-stage -> weighted next-stage options. This allows mostly forward motion,
# with small regressions to mimic real buying journeys.
STAGE_TRANSITIONS: dict[str, tuple[tuple[str, float], ...]] = {
    "awareness": (("awareness", 0.42), ("consideration", 0.58)),
    "consideration": (("awareness", 0.08), ("consideration", 0.46), ("decision", 0.46)),
    "decision": (("consideration", 0.12), ("decision", 0.88)),
}


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _sample_timestamps(
    rng: random.Random,
    first_touch_at: datetime,
    total_touches: int,
    journey_length_days: int,
) -> list[datetime]:
    day_offsets = sorted(
        rng.sample(range(journey_length_days), k=min(total_touches, journey_length_days))
    )
    while len(day_offsets) < total_touches:
        day_offsets.append(day_offsets[-1] + 1)
    day_offsets = day_offsets[:total_touches]
    return [
        first_touch_at + timedelta(days=offset, hours=rng.randint(0, 8))
        for offset in day_offsets
    ]


def _choose_next_stage(
    rng: random.Random,
    current_stage: str,
    position: int,
    total_touches: int,
) -> str:
    positions_left = total_touches - position
    current_index = STAGE_INDEX[current_stage]

    # Force the journey to reach decision stage before the last touch.
    if positions_left <= max(0, 2 - current_index):
        return STAGE_ORDER[min(current_index + 1, 2)]
    if positions_left == 1:
        return "decision"

    candidates = STAGE_TRANSITIONS[current_stage]
    names = [name for name, _ in candidates]
    weights = [weight for _, weight in candidates]
    return rng.choices(names, weights=weights, k=1)[0]


def _build_stage_sequence(rng: random.Random, total_touches: int) -> list[str]:
    awareness_count = 1 if total_touches <= 4 else rng.choices([1, 2], weights=[0.65, 0.35], k=1)[0]
    remaining_after_awareness = total_touches - awareness_count

    if remaining_after_awareness <= 2:
        consideration_count = 1
    else:
        consideration_count = rng.randint(1, min(3, remaining_after_awareness - 1))

    decision_count = total_touches - awareness_count - consideration_count
    if decision_count > 4:
        consideration_count += decision_count - 4
        decision_count = 4

    stages = (
        ["awareness"] * awareness_count
        + ["consideration"] * consideration_count
        + ["decision"] * decision_count
    )

    # Allow one light regression to mirror real journeys without creating loops.
    if total_touches >= 6 and consideration_count >= 1 and decision_count >= 2 and rng.random() < 0.14:
        decision_start = awareness_count + consideration_count
        regression_index = min(len(stages) - 2, decision_start + 1)
        forward_index = max(awareness_count, decision_start - 1)
        stages[forward_index] = "decision"
        stages[regression_index] = "consideration"

    stages[0] = "awareness"
    stages[-1] = "decision"
    return stages


def _choose_channel(
    rng: random.Random,
    stage: str,
    used_counts: Counter[str],
    previous_channel: str | None,
) -> ChannelProfile:
    candidates = [
        channel
        for channel in CHANNELS_BY_STAGE[stage]
        if channel.name != previous_channel and used_counts[channel.name] < 1
    ]
    if not candidates:
        candidates = [
            channel
            for channel in CHANNELS_BY_STAGE[stage]
            if channel.name != previous_channel and used_counts[channel.name] < 2
        ]
    if not candidates:
        candidates = [
            channel for channel in CHANNELS_BY_STAGE[stage] if channel.name != previous_channel
        ]

    weights = [channel.weight / (1 + used_counts[channel.name]) for channel in candidates]
    return rng.choices(candidates, weights=weights, k=1)[0]


def _build_channel_path(rng: random.Random, stage_sequence: list[str]) -> list[ChannelProfile]:
    used_counts: Counter[str] = Counter()
    previous_channel: str | None = None
    path: list[ChannelProfile] = []

    for stage in stage_sequence:
        profile = _choose_channel(rng, stage, used_counts, previous_channel)
        path.append(profile)
        used_counts[profile.name] += 1
        previous_channel = profile.name

    return path


def _conversion_signal(segment: str, channel_path: Iterable[ChannelProfile]) -> float:
    signal = SEGMENTS[segment]["base_prob"]
    touches = list(channel_path)
    total = len(touches)
    stages = [touch.stage for touch in touches]
    stage_indexes = [STAGE_INDEX[stage] for stage in stages]

    for index, touch in enumerate(touches, start=1):
        recency_multiplier = 0.74 + (index / total) * 0.62
        signal += touch.influence * recency_multiplier * 0.18

    if len(set(stage_indexes)) == 3:
        signal += 0.18
    if stage_indexes == sorted(stage_indexes):
        signal += 0.14
    if stage_indexes.count(0) > max(1, total // 2):
        signal -= 0.12
    if stage_indexes[-1] != STAGE_INDEX["decision"]:
        signal -= 0.25

    channels = {touch.name for touch in touches}
    if {"webinar", "email_nurture"} <= channels:
        signal += 0.18
    if {"linkedin_ads", "google_search"} <= channels:
        signal += 0.10
    if {"retargeting", "direct"} <= channels:
        signal += 0.14
    if {"review_sites", "partner_referral"} <= channels:
        signal += 0.12

    decision_touches = sum(1 for touch in touches if touch.stage == "decision")
    if decision_touches >= 2:
        signal += 0.10

    return signal


def journey_quality_metrics(df: pd.DataFrame) -> dict[str, float]:
    """Return simple realism metrics for generated journeys."""

    journeys = (
        df.sort_values(["journey_id", "touch_timestamp"])
        .groupby("journey_id")
        .agg(
            channels=("channel", list),
            stages=("funnel_stage", list),
            converted=("converted", "max"),
        )
    )

    repeat_any = journeys["channels"].apply(lambda values: len(values) != len(set(values)))
    repeat_adjacent = journeys["channels"].apply(
        lambda values: any(a == b for a, b in zip(values, values[1:]))
    )
    stage_regressions = journeys["stages"].apply(
        lambda values: sum(
            1
            for left, right in zip(values, values[1:])
            if STAGE_INDEX[right] < STAGE_INDEX[left]
        )
    )

    return {
        "journey_count": float(len(journeys)),
        "conversion_rate": float(journeys["converted"].mean()),
        "repeat_any_rate": float(repeat_any.mean()),
        "adjacent_repeat_rate": float(repeat_adjacent.mean()),
        "avg_stage_regressions": float(stage_regressions.mean()),
    }


def generate_touchpoint_dataset(
    output_path: str | Path = DATA_PATH,
    journeys: int = 4500,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Generate a realistic B2B SaaS multi-touch attribution dataset."""

    rng = random.Random(seed)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    base_date = datetime(2024, 1, 1, 9, 0, 0)

    for journey_id in range(1, journeys + 1):
        segment = rng.choices(
            population=list(SEGMENTS.keys()),
            weights=[0.52, 0.33, 0.15],
            k=1,
        )[0]
        region = rng.choices(REGIONS, weights=[0.55, 0.28, 0.17], k=1)[0]
        industry = rng.choice(INDUSTRIES)
        account_id = rng.randint(1, max(1400, journeys // 2))
        total_touches = rng.randint(3, 8)
        journey_length_days = rng.randint(20, 120)
        first_touch_at = base_date + timedelta(days=rng.randint(0, 250))
        touch_times = _sample_timestamps(rng, first_touch_at, total_touches, journey_length_days)

        stage_sequence = _build_stage_sequence(rng, total_touches)
        channel_path = _build_channel_path(rng, stage_sequence)
        conversion_probability = _sigmoid(_conversion_signal(segment, channel_path))
        converted = int(rng.random() < conversion_probability)
        conversion_timestamp = touch_times[-1] + timedelta(days=rng.randint(2, 18))

        if converted:
            revenue_floor = SEGMENTS[segment]["deal_min"]
            revenue_ceiling = SEGMENTS[segment]["deal_max"]
            revenue = round(rng.uniform(revenue_floor, revenue_ceiling), 2)
        else:
            revenue = 0.0

        for position, (touch_time, profile) in enumerate(zip(touch_times, channel_path), start=1):
            cost = round(rng.uniform(profile.cost_low, profile.cost_high), 2) if profile.paid else 0.0
            days_to_conversion = (
                round((conversion_timestamp - touch_time).total_seconds() / 86400, 2)
                if converted
                else None
            )
            rows.append(
                {
                    "journey_id": journey_id,
                    "account_id": account_id,
                    "segment": segment,
                    "region": region,
                    "industry": industry,
                    "channel": profile.name,
                    "funnel_stage": profile.stage,
                    "touch_position": position,
                    "total_touches": total_touches,
                    "touch_timestamp": touch_time,
                    "is_paid_channel": int(profile.paid),
                    "cost": cost,
                    "converted": converted,
                    "conversion_timestamp": conversion_timestamp if converted else pd.NaT,
                    "days_to_conversion": days_to_conversion,
                    "revenue": revenue,
                }
            )

    df = pd.DataFrame(rows).sort_values(["journey_id", "touch_timestamp"]).reset_index(drop=True)
    df["touch_timestamp"] = pd.to_datetime(df["touch_timestamp"])
    df["conversion_timestamp"] = pd.to_datetime(df["conversion_timestamp"])
    df.to_csv(output_path, index=False)
    return df
