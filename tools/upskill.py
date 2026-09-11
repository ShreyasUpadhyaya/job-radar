"""Aggregate skill-gap heatmap across everything the radar is tracking.

Per-job gaps answer "what does this one posting want that I lack". Aggregated
across the whole board they answer the more useful question: what should I
learn next to unlock the most roles I already nearly qualify for. Borrowed
from ai-job-search's /upskill.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    data = json.loads((ROOT / "docs" / "jobs.json").read_text())
    jobs = data["jobs"]

    counts, by_skill_score, companies = Counter(), defaultdict(list), defaultdict(set)
    for j in jobs:
        for gap in j.get("skill_gaps", []):
            counts[gap] += 1
            by_skill_score[gap].append(j["match_score"])
            companies[gap].add(j["company"])

    if not counts:
        print("no gaps recorded; portals that hide descriptions cannot show them")
        return

    lines = [f"# Skill gaps across {len(jobs)} live matches",
             f"_{datetime.now(timezone.utc).strftime('%d %B %Y')}_", "",
             "What the postings ask for that your resume does not claim, most",
             "common first. The average match score tells you whether a gap sits",
             "on roles you are otherwise close to.", "",
             "| Gap | Postings | Avg match | Companies |", "|---|---|---|---|"]
    for skill, n in counts.most_common(25):
        avg = sum(by_skill_score[skill]) / len(by_skill_score[skill])
        firms = ", ".join(sorted(companies[skill])[:4])
        lines.append(f"| {skill} | {n} | {avg:.0f} | {firms} |")

    top = counts.most_common(5)
    lines += ["", "## Where to spend the next month", ""]
    for skill, n in top:
        avg = sum(by_skill_score[skill]) / len(by_skill_score[skill])
        lines.append(f"- **{skill}** blocks {n} postings averaging {avg:.0f} match. "
                     f"Seen at {', '.join(sorted(companies[skill])[:3])}.")

    out = ROOT / "reports" / "skill-gaps.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out.relative_to(ROOT)}: {len(counts)} distinct gaps")


if __name__ == "__main__":
    main()
