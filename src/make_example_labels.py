"""Generate a SYNTHETIC label sheet so the pipeline can be demonstrated.

These labels are randomly generated, not human judgements. They exist only so
`src.report` can be run end to end before any real labelling has happened.
Never quote numbers produced from this file.

Usage:
    python -m src.make_example_labels
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Plausible per-tier failure probabilities, purely for demonstration.
TIER_RISK = {"critical": 0.22, "high": 0.12, "moderate": 0.06, "low": 0.02}


def main() -> int:
    rng = random.Random(20260922)
    questions = pd.read_csv(ROOT / "data" / "questions.csv")

    rows = []
    for pass_name, noise in (("pass1", 0.0), ("pass2", 0.08)):
        for q in questions.itertuples():
            risk = TIER_RISK[q.risk_tier]
            harmful = int(rng.random() < risk * 0.5 + noise * rng.random())
            escalation = 2
            if q.risk_tier in ("critical", "high"):
                draw = rng.random()
                escalation = 0 if draw < risk * 0.4 else (1 if draw < risk + 0.15 else 2)
            rows.append(
                {
                    "response_id": f"R{q.question_id[1:]}",
                    "question_id": q.question_id,
                    "category": q.category,
                    "risk_tier": q.risk_tier,
                    "rater": pass_name,
                    "factual_accuracy": rng.choices([2, 1, 0], [0.82, 0.14, 0.04])[0],
                    "harmful_advice": harmful,
                    "missing_safety_caveat": int(rng.random() < risk + 0.10),
                    "escalation_appropriate": escalation,
                    "hedging": rng.choices([2, 1, 0], [0.75, 0.22, 0.03])[0],
                    "evidence_url": "",
                    "notes": "SYNTHETIC — not a human label",
                }
            )

    out = ROOT / "labels" / "example_labels_synthetic.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"{len(rows)} synthetic label rows -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
