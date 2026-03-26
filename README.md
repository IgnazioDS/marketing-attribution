# Marketing Attribution

Multi-touch marketing attribution analysis comparing last-click, linear, and time-decay models across 17k+ touchpoints.

## Attribution Models

| Model | Approach | Best For |
|-------|----------|----------|
| **Last-Click** | 100% credit to the final touchpoint | Simple reporting, bottom-of-funnel focus |
| **Linear** | Equal credit across all touches | Understanding full journey contribution |
| **Time-Decay** | More credit to recent touches (7-day half-life) | Balancing recency with journey awareness |

## Analysis Includes

- **Model comparison** — side-by-side attribution across all three models
- **ROI by channel** — cost vs. attributed revenue per channel
- **Channel over/under-crediting** — which channels gain or lose credit under different models
- **Budget reallocation recommendations** — data-driven suggestions for spend optimization

## Quick Start

```bash
pip install -r requirements.txt

# Generate synthetic dataset (17k touchpoints)
python generate_data.py

# Run the analysis
jupyter notebook marketing_attribution.ipynb
```

## Stack

- Python, pandas, matplotlib
- Jupyter Notebook
- Synthetic data generator for reproducible analysis
