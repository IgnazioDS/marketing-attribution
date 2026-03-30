"""Rebuild the walkthrough notebook from the reusable analysis package."""

from __future__ import annotations

from pathlib import Path
import sys

import nbformat as nbf


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


def main() -> None:
    nb = nbf.v4.new_notebook()
    cells = []

    cells.append(
        nbf.v4.new_markdown_cell(
            "# B2B SaaS Attribution Walkthrough\n\n"
            "This notebook mirrors the client-facing case study in the repository. "
            "It uses the reusable package code and the same recommendation logic that drives the exported executive summary."
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            "## Buyer Problem\n\n"
            "A B2B SaaS team can have healthy pipeline creation and still make poor budget decisions if it relies on a closing-touch reporting model. "
            "The goal here is to show, with synthetic public data, how a more defensible attribution workflow changes the budget conversation."
        )
    )

    cells.append(
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "\n"
            "ROOT = Path.cwd()\n"
            "sys.path.insert(0, str(ROOT / 'src'))\n"
            "\n"
            "from marketing_attribution.models import build_attribution_report, load_touchpoints\n"
            "from marketing_attribution.reporting import build_executive_summary, build_recommendation_table\n"
            "\n"
            "df = load_touchpoints(ROOT / 'data' / 'touchpoints.csv')\n"
            "report = build_attribution_report(df)\n"
            "report['recommendations'] = build_recommendation_table(report['channel_scorecard'])\n"
            "df.head()"
        )
    )

    cells.append(
        nbf.v4.new_code_cell(
            "converted = df[df['converted'] == 1]\n"
            "kpis = {\n"
            "    'accounts': int(df['account_id'].nunique()),\n"
            "    'journeys': int(df['journey_id'].nunique()),\n"
            "    'converting_journeys': int(converted['journey_id'].nunique()),\n"
            "    'conversion_rate': round(converted['journey_id'].nunique() / df['journey_id'].nunique(), 4),\n"
            "    'pipeline': round(converted.groupby('journey_id')['revenue'].max().sum(), 2),\n"
            "    'median_touches': float(converted.groupby('journey_id')['total_touches'].max().median()),\n"
            "}\n"
            "kpis"
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell("## Channel Revenue by Model")
    )

    cells.append(
        nbf.v4.new_code_cell(
            "report['revenue_pivot'].round(0)"
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell("## Top Converting Paths")
    )

    cells.append(
        nbf.v4.new_code_cell(
            "report['top_paths'].head(10)"
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell("## Recommendation Scorecard")
    )

    cells.append(
        nbf.v4.new_code_cell(
            "report['recommendations'][['channel', 'primary_recommendation', 'rationale', 'time_decay_roas', 'time_decay_uplift']].round(2)"
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell(
            "## What this would look like in a real engagement\n\n"
            "In production, the same workflow would connect campaign touches, lifecycle timestamps, and CRM opportunity history. "
            "The public version here uses synthetic data so the methodology can be reviewed openly."
        )
    )

    cells.append(
        nbf.v4.new_markdown_cell("## Executive Summary Draft")
    )

    cells.append(
        nbf.v4.new_code_cell(
            "print(build_executive_summary(df, report))"
        )
    )

    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": sys.version.split()[0]},
    }

    output_path = ROOT / "marketing_attribution.ipynb"
    output_path.write_text(nbf.writes(nb), encoding="utf-8")
    print(f"Rebuilt notebook -> {output_path}")


if __name__ == "__main__":
    main()
