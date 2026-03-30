# Executive Summary

_Generated 2026-03-30 19:37 UTC_

## Why this case study matters

This public demo shows the kind of attribution engagement a B2B SaaS CMO would buy:
a unified touchpoint model, defensible attribution logic, executive-ready visuals, and budget recommendations tied to pipeline outcomes.

## Dataset snapshot

- Accounts represented: 1,942
- Buying journeys analyzed: 4,500
- Converting journeys: 1,205 (26.8% conversion rate)
- Attributed pipeline in the sample: $54,973,198
- Average won opportunity value: $45,621
- Median days from first touch to conversion: 57.1
- Median touches in winning journeys: 6

## What the analysis shows

- Last-touch reporting still assigns $54,973,198 of pipeline, but it materially under-values assist channels earlier in the buying journey.
- Winning journeys usually require 6 touches, which makes single-touch reporting incomplete for budget allocation.
- Early demand creation is led by `linkedin_ads` and `organic_search`, while conversion capture concentrates in `direct` and `retargeting`.
- The strongest repeatable converting path in the sample is `organic_search > google_search > retargeting`.

## Recommendation for the client

- Increase investment in `google_search` because it is under-credited by last-touch, strong time-decay ROAS, sufficient scale.
- Trim or hold `partner_referral` because it is over-credited by last-touch, less efficient than other scaled paid channels, sufficient scale.
- Use time-decay or position-based attribution for channel steering, while keeping last-touch for directional reporting only.
- In a live engagement, the next step would be to join CRM opportunity stages, campaign metadata, and lifecycle timestamps to move from channel attribution into account-level pipeline attribution.

## How this maps to a real engagement

- The data in this public repo is synthetic so the work can be shared openly.
- The workflow itself mirrors a real project: ingest touchpoints, connect them to revenue, compare attribution models, and produce budget guidance that leadership can act on.

## Deliverables in this repo

- `run_analysis.py`: deterministic workflow to regenerate the dataset, charts, and reports.
- `reports/channel_model_summary.csv`: channel performance by attribution model.
- `reports/channel_recommendations.csv`: auditable recommendation scorecard.
- `reports/executive_summary.md`: pre-call summary for a buyer conversation.