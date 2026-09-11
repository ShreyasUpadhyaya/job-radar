"""Write the morning digest. The workflow turns it into a GitHub issue,
which GitHub emails to you, and optionally into a direct email.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROFILE = yaml.safe_load((ROOT / "profile.yml").read_text())
PAGES = os.environ.get("PAGES_URL", "")


def line(j):
    bits = [j["experience_note"]]
    if j["salary_lpa"] is not None:
        bits.append(f"{j['salary_lpa']} LPA")
    bits.append(f"match {j['match_score']}")
    hits = ", ".join(j["match_hits"][:5])
    tail = f"  \n  {hits}" if hits else ""
    return (
        f"- **[{j['title']}]({j['url']})** at {j['company']}  \n"
        f"  {j['location_label']} · {' · '.join(bits)}{tail}"
    )


def main():
    fresh = json.loads((ROOT / "state" / "new.json").read_text())
    floor = PROFILE.get("min_score_to_notify", 40)
    worth = [j for j in fresh if j["match_score"] >= floor]

    out = ROOT / "state" / "digest.md"
    if not worth:
        out.write_text("")
        print("nothing above the notify threshold")
        return

    today = datetime.now(timezone.utc).strftime("%d %B %Y")
    parts = [f"{len(worth)} new {'role' if len(worth) == 1 else 'roles'} this morning, {today}.", ""]

    by_tier = {}
    for j in sorted(worth, key=lambda x: (x["location_tier"], -x["match_score"])):
        by_tier.setdefault(j["location_label"], []).append(j)
    for place, jobs in by_tier.items():
        parts.append(f"### {place}")
        parts += [line(j) for j in jobs]
        parts.append("")

    if PAGES:
        parts.append(f"[Open the full board]({PAGES})")
    out.write_text("\n".join(parts))
    print(f"digest written: {len(worth)} roles")


if __name__ == "__main__":
    main()
