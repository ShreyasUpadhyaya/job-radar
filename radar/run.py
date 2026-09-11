"""Daily run: read every portal, rank what is there, report what changed."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import yaml

from . import score as scoring
from .sources import FETCHERS

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
STATE = ROOT / "state"
REPORTS = ROOT / "reports"
SEEN = STATE / "seen.json"

MIN_SHOW = 20              # below this a posting is not worth your attention
STALE_AFTER_DAYS = 21      # not seen for this long and it is treated as closed
RENDERED = {"custom", "keka", "darwinbox", "zohorecruit", "freshteam",
            "firecrawl", "successfactors", "eightfold"}

# Tracking noise that makes the same job look like two jobs.
JUNK_PARAMS = re.compile(r"^(utm_|gh_|ref$|source$|src$|lever-|trackingid$|from$)", re.I)


def clean_url(url):
    try:
        u = urlparse(url)
    except ValueError:
        return url
    query = [(k, v) for k, v in parse_qsl(u.query) if not JUNK_PARAMS.match(k)]
    return urlunparse(u._replace(query=urlencode(query), fragment=""))


def job_id(company, url, title):
    return hashlib.sha1(f"{company}|{clean_url(url)}".encode()).hexdigest()[:16]


def content_key(company, title, location):
    """Same role listed twice under different URLs collapses to one row."""
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()
    return hashlib.sha1(f"{norm(company)}|{norm(title)}|{norm(location)}".encode()).hexdigest()[:16]


def fetch_company(entry):
    company, info = entry
    fetcher = FETCHERS.get(info.get("ats", "custom"))
    if fetcher is None:
        return company, [], f"no fetcher for {info.get('ats')}"
    try:
        return company, fetcher(info.get("slug", ""), info.get("careers")), None
    except Exception as exc:
        return company, [], f"{type(exc).__name__}: {exc}".split("\n")[0][:160]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="limit to these companies")
    ap.add_argument("--skip-rendered", action="store_true",
                    help="skip portals that need Firecrawl")
    ap.add_argument("--cadence", choices=["daily", "weekly"], default="daily",
                    help="daily reads priority 1 rendered portals; weekly reads all")
    ap.add_argument("--workers", type=int, default=12)
    args = ap.parse_args()

    companies = yaml.safe_load((ROOT / "companies.yml").read_text())["companies"]
    meta = {c["name"]: c for c in companies}
    resolved = json.loads((ROOT / "resolved.json").read_text())

    targets = []
    for name, info in resolved.items():
        if name not in meta:
            continue
        rendered = info.get("ats") in RENDERED
        if rendered and args.skip_rendered:
            continue
        # Rendered portals cost Firecrawl credits, so the long tail is read
        # once a week and the priority list every day. API portals are free
        # and always read.
        if rendered and args.cadence == "daily" and meta[name].get("priority", 1) != 1:
            continue
        targets.append((name, info))
    if args.only:
        targets = [t for t in targets if t[0] in set(args.only)]

    ranked, errors, raw_total, by_content = [], {}, 0, {}
    vetoed = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for company, jobs, err in ex.map(fetch_company, targets):
            if err:
                errors[company] = err
                continue
            raw_total += len(jobs)
            for j in jobs:
                if not j.get("title") or not j.get("url"):
                    continue
                j["url"] = clean_url(j["url"])
                r = scoring.rank(j, meta[company].get("tier", "india"))
                if r["location_tier"] >= scoring.DROP or r["match_score"] < MIN_SHOW:
                    continue
                if r.get("veto"):
                    vetoed.setdefault(r["veto"], 0)
                    vetoed[r["veto"]] += 1
                    continue
                key = content_key(company, j["title"], r["location_label"])
                if key in by_content:
                    by_content[key]["duplicates"] = by_content[key].get("duplicates", 0) + 1
                    continue
                r["company"] = company
                r["company_tier"] = meta[company].get("tier", "india")
                r["portal"] = resolved[company].get("ats", "custom")
                r["id"] = job_id(company, j["url"], j["title"])
                by_content[key] = r
                ranked.append(r)

    ranked.sort(key=scoring.sort_key)

    # ---- freshness -------------------------------------------------------
    STATE.mkdir(parents=True, exist_ok=True)
    seen = json.loads(SEEN.read_text()) if SEEN.exists() else {}
    now = datetime.now(timezone.utc)
    stamp = now.isoformat()
    live = {j["id"] for j in ranked}
    fresh = []

    for j in ranked:
        rec = seen.get(j["id"])
        if rec is None:
            seen[j["id"]] = {"first": stamp, "last": stamp}
            j["first_seen"], j["is_new"] = stamp, True
            fresh.append(j)
        else:
            if isinstance(rec, str):          # migrate the old flat format
                rec = {"first": rec, "last": rec}
            rec["last"] = stamp
            seen[j["id"]] = rec
            j["first_seen"], j["is_new"] = rec["first"], False
        j["days_listed"] = max(0, (now - datetime.fromisoformat(j["first_seen"])).days)

    # A job that stops appearing has almost always been filled or pulled.
    checked = {t[0] for t in targets}
    closed = 0
    cutoff = now - timedelta(days=STALE_AFTER_DAYS)
    for jid, rec in list(seen.items()):
        if isinstance(rec, str):
            rec = {"first": rec, "last": rec}
            seen[jid] = rec
        if jid in live:
            continue
        if datetime.fromisoformat(rec["last"]) < cutoff:
            del seen[jid]
            closed += 1
    SEEN.write_text(json.dumps(seen, indent=0, sort_keys=True))

    # ---- outputs ---------------------------------------------------------
    payload = {
        "generated_at": stamp,
        "cadence": args.cadence,
        "companies_checked": len(targets),
        "companies_total": len(companies),
        "companies_failed": errors,
        "postings_seen": raw_total,
        "duplicates_merged": sum(j.get("duplicates", 0) for j in ranked),
        "matches": len(ranked),
        "vetoed": vetoed,
        "new_today": len(fresh),
        "closed_since": closed,
        "jobs": ranked,
    }
    DOCS.mkdir(exist_ok=True)
    (DOCS / "jobs.json").write_text(json.dumps(payload, indent=1))
    (STATE / "new.json").write_text(json.dumps(fresh, indent=1))

    with (DOCS / "jobs.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["company", "title", "location", "experience", "salary_lpa",
                    "match", "portal", "posted", "url"])
        for j in ranked:
            w.writerow([j["company"], j["title"], j["location_label"],
                        j["experience_note"], j["salary_lpa"] or "",
                        j["match_score"], j["portal"], j["posted_at"] or "", j["url"]])

    REPORTS.mkdir(exist_ok=True)
    day = now.strftime("%Y-%m-%d")
    lines = [f"# {day}", "",
             f"{len(ranked)} live matches, {len(fresh)} new, {closed} closed since last run.",
             f"Read {len(targets)} of {len(companies)} portals ({args.cadence}).", ""]
    for j in fresh:
        pay = f", {j['salary_lpa']} LPA" if j["salary_lpa"] is not None else ""
        lines.append(f"- [{j['title']}]({j['url']}) at {j['company']} "
                     f"({j['location_label']}, {j['experience_note']}{pay}, match {j['match_score']})")
    (REPORTS / f"{day}.md").write_text("\n".join(lines) + "\n")

    print(f"read {len(targets)} portals, {raw_total} postings, {len(ranked)} matches, "
          f"{len(fresh)} new, {closed} closed, {payload['duplicates_merged']} duplicates merged")
    if vetoed:
        print("  vetoed: " + ", ".join(f"{k} ({v})" for k, v in sorted(vetoed.items())))
    for company, err in sorted(errors.items())[:25]:
        print(f"  failed: {company}: {err}")


if __name__ == "__main__":
    main()
