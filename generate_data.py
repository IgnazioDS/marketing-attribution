"""Generate synthetic multi-touch marketing attribution dataset."""

import csv
import random
from datetime import date, timedelta

random.seed(99)

CHANNELS = ["google_ads", "facebook_ads", "email", "organic_search", "referral", "direct"]
CHANNEL_COST_PER_TOUCH = {"google_ads": 12, "facebook_ads": 8, "email": 1,
                           "organic_search": 0, "referral": 5, "direct": 0}
CONVERT_PROB = {"google_ads": 0.12, "facebook_ads": 0.08, "email": 0.18,
                "organic_search": 0.15, "referral": 0.22, "direct": 0.20}

rows = []
for session_id in range(1, 5001):
    user_id = random.randint(1, 2000)
    n_touches = random.randint(1, 6)
    session_date = date(2024, 1, 1) + timedelta(days=random.randint(0, 270))
    touches = random.choices(CHANNELS, k=n_touches)
    revenue = 0
    converted = 0
    last_channel = touches[-1]
    if random.random() < CONVERT_PROB[last_channel]:
        converted = 1
        revenue = random.choice([49, 99, 149, 299, 499])
    for position, channel in enumerate(touches):
        rows.append({
            "session_id": session_id,
            "user_id": user_id,
            "session_date": session_date.isoformat(),
            "channel": channel,
            "touch_position": position + 1,
            "total_touches": n_touches,
            "converted": converted,
            "revenue": revenue,
            "cost": CHANNEL_COST_PER_TOUCH[channel],
        })

with open("data/touchpoints.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows):,} touchpoints → data/touchpoints.csv")
