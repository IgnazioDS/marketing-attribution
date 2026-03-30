# B2B SaaS Marketing Attribution Case Study

Most B2B SaaS teams still allocate budget with a reporting view that over-rewards closing touches and under-values the channels that create qualified demand earlier in the buying journey. That gap leads to the wrong conversations in budget reviews: teams protect channels that appear to close pipeline and underinvest in the programs that actually create it.

This repository is a public, synthetic case study of the attribution work I would deliver for a B2B SaaS CMO or RevOps leader. It is built to answer a buyer’s real question: can this person turn fragmented marketing touchpoints into defensible budget guidance tied to pipeline?

## What this case study demonstrates

- A unified touchpoint model across awareness, consideration, and decision-stage channels.
- Four attribution views that serve different decisions: last-touch, linear, time-decay, and U-shaped.
- An auditable recommendation engine that weighs attribution uplift, efficiency, and scale before suggesting budget moves.
- Executive-ready outputs that can be used in a buyer conversation without opening the code first.

## What the analysis reveals

- Last-touch reporting systematically over-credits late-stage capture channels and misses assist value in mid-funnel programs.
- Multi-touch B2B buying journeys require a budget-steering model that is different from a reporting model.
- The strongest investment candidates are not simply the channels with the most attributed revenue. They are the channels with under-credited influence, acceptable efficiency, and enough scale to matter.

## Deliverables in the repo

- [reports/executive_summary.md](/Users/ignaziodesantis/Desktop/Development/portfolio-projects/marketing-attribution/reports/executive_summary.md): buyer-facing summary with a recommended budget move.
- [reports/channel_recommendations.csv](/Users/ignaziodesantis/Desktop/Development/portfolio-projects/marketing-attribution/reports/channel_recommendations.csv): auditable recommendation table with eligibility and scoring.
- [reports/channel_model_summary.csv](/Users/ignaziodesantis/Desktop/Development/portfolio-projects/marketing-attribution/reports/channel_model_summary.csv): attributed pipeline and ROAS by model.
- [charts/channel_revenue_by_model.png](/Users/ignaziodesantis/Desktop/Development/portfolio-projects/marketing-attribution/charts/channel_revenue_by_model.png): channel-by-model revenue comparison.
- [charts/roas_heatmap.png](/Users/ignaziodesantis/Desktop/Development/portfolio-projects/marketing-attribution/charts/roas_heatmap.png): efficiency comparison across models.
- [marketing_attribution.ipynb](/Users/ignaziodesantis/Desktop/Development/portfolio-projects/marketing-attribution/marketing_attribution.ipynb): walkthrough notebook for live demos or buyer conversations.

## How to reproduce the exact outputs

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py --seed 42 --journeys 4500
python build_notebook.py
pytest
```

The `run_analysis.py` command regenerates the dataset by default, then rebuilds all charts and reports from that same deterministic seed.

## What a real client engagement would include

This public version uses synthetic data so the full workflow can be shared openly. In a live engagement, the same structure would run on:

- CRM opportunity history and stage progression
- ad platform spend and campaign metadata
- marketing automation touches and lifecycle timestamps
- website or product events where account-level identity is available

The deliverable would be the same shape as this repo: cleaned data, attribution comparisons, recommendation logic, and a buyer-ready narrative tied to pipeline outcomes.

## Why this is stronger than a notebook demo

The value is not just in the charts. The value is in the decision quality:

- the dataset is generated with realistic stage-aware journey logic
- recommendations are thresholded and scored, not hand-waved
- outputs are deterministic and reproducible
- the summary is written for a CMO or RevOps stakeholder, not for a notebook reader

## Selected visuals

![Attributed revenue by model](/Users/ignaziodesantis/Desktop/Development/portfolio-projects/marketing-attribution/charts/channel_revenue_by_model.png)

![ROAS heatmap](/Users/ignaziodesantis/Desktop/Development/portfolio-projects/marketing-attribution/charts/roas_heatmap.png)
