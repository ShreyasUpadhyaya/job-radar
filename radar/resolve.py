"""Work out where each company posts jobs and what that portal runs on.

Three passes, cheapest first:

1. Find the careers page. Where the registry only has a domain, try the paths
   companies actually use, and the careers subdomain.
2. Sniff the served HTML for an ATS. Verify against that board's API before
   trusting it, so a stray marketing link cannot mislabel a company.
3. Guess. Derive slug candidates from the company name and domain and try them
   against Greenhouse, Lever, Ashby, SmartRecruiters, Workable and Recruitee.
   A guess is only kept when the board answers with real postings, which is
   what catches boards rendered by JavaScript.

Anything still unresolved is marked custom and read by Firecrawl at run time.
"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yaml

from .sources import UA

ROOT = Path(__file__).resolve().parent.parent
RESOLVED = ROOT / "resolved.json"

CAREERS_PATHS = [
    "/careers", "/careers/", "/jobs", "/jobs/", "/company/careers",
    "/about/careers", "/careers/jobs", "/work-with-us", "/join-us",
    "/company/jobs", "/en/careers", "/career",
]

SIGNATURES = [
    ("greenhouse", r"(?:boards|job-boards)\.greenhouse\.io/(?:embed/job_board\?for=)?([a-zA-Z0-9_-]+)"),
    ("greenhouse", r"greenhouse\.io/embed/job_board/js\?for=([a-zA-Z0-9_-]+)"),
    ("lever", r"jobs\.(?:eu\.)?lever\.co/([a-zA-Z0-9_-]+)"),
    ("ashby", r"jobs\.ashbyhq\.com/([a-zA-Z0-9_.-]+)"),
    # The locale segment is optional and appears in either case, so skip it
    # rather than mistaking en-us for the site name.
    ("workday", r"([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-zA-Z]{2}-[a-zA-Z]{2}/)?([A-Za-z0-9_-]+)"),
    ("smartrecruiters", r"(?:careers|jobs)\.smartrecruiters\.com/([a-zA-Z0-9_-]+)"),
    ("workable", r"apply\.workable\.com/([a-zA-Z0-9_-]+)"),
    ("recruitee", r"([a-z0-9-]+)\.recruitee\.com"),
    ("teamtailor", r"([a-z0-9-]+)\.teamtailor\.com"),
    ("personio", r"([a-z0-9-]+)\.jobs\.personio\.(?:de|com)"),
    ("bamboohr", r"([a-z0-9-]+)\.bamboohr\.com"),
    ("jobvite", r"jobs\.jobvite\.com/([a-zA-Z0-9_-]+)"),
    ("icims", r"([a-z0-9-]+)\.icims\.com"),
    ("keka", r"([a-z0-9-]+)\.keka\.com"),
    ("darwinbox", r"([a-z0-9-]+)\.darwinbox\.(?:in|com)"),
    ("zohorecruit", r"([a-z0-9-]+)\.zohorecruit\.(?:in|com|eu)"),
    ("freshteam", r"([a-z0-9-]+)\.freshteam\.com"),
    ("successfactors", r"career\d*\.successfactors\.(?:com|eu)"),
    ("eightfold", r"([a-z0-9-]+)\.eightfold\.ai"),
]

VERIFY = {
    "greenhouse": ("https://boards-api.greenhouse.io/v1/boards/{s}/jobs?content=false", "jobs"),
    "lever": ("https://api.lever.co/v0/postings/{s}?mode=json", None),
    "ashby": ("https://api.ashbyhq.com/posting-api/job-board/{s}", "jobs"),
    "smartrecruiters": ("https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=1", "content"),
    "recruitee": ("https://{s}.recruitee.com/api/offers/", "offers"),
    "workable": ("https://apply.workable.com/api/v1/widget/accounts/{s}?details=true", "jobs"),
    "teamtailor": ("https://{s}.teamtailor.com/jobs.json", None),
}

GUESSABLE = ["greenhouse", "lever", "ashby", "smartrecruiters", "workable", "recruitee"]


def verify(ats, slug):
    spec = VERIFY.get(ats)
    if not spec:
        return True
    url, key = spec
    try:
        r = httpx.get(url.format(s=slug), headers=UA, timeout=15, follow_redirects=True)
        if r.status_code != 200:
            return False
        data = r.json()
        rows = data if key is None else data.get(key, [])
        return isinstance(rows, list) and len(rows) > 0
    except Exception:
        return False


DEMO = re.compile(r"\b(sample|demo|test|uat|dummy|placeholder)\b", re.I)


def _norm(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def identity_ok(ats, slug, company):
    """Does this board actually belong to this company?

    Slug guessing finds real boards under generic names that belong to someone
    else: recruitee/google is a demo tenant, smartrecruiters/uber holds a
    single posting called Test UAT, ashby/navi is a San Francisco startup and
    not the Indian lender. A guess is only kept when the board says whose it
    is, or its public page points back at the company's own domain.
    """
    name = _norm(company["name"])
    domain = urlparse(company["careers"]).netloc.replace("www.", "")
    root = _norm(domain.split(".")[0])

    try:
        if ats == "greenhouse":
            r = httpx.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}",
                          headers=UA, timeout=15)
            board = _norm(r.json().get("name", ""))
            return bool(board) and (board.startswith(name[:6]) or name.startswith(board[:6]))

        if ats == "smartrecruiters":
            r = httpx.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=5",
                          headers=UA, timeout=15)
            data = r.json()
            rows = data.get("content", [])
            if not rows or all(DEMO.search(j.get("name", "")) for j in rows):
                return False
            board = _norm((rows[0].get("company") or {}).get("name", ""))
            return bool(board) and (board.startswith(name[:6]) or name.startswith(board[:6]))

        if ats == "recruitee":
            r = httpx.get(f"https://{slug}.recruitee.com/api/offers/", headers=UA, timeout=15)
            rows = r.json().get("offers", [])
            if not rows or any(DEMO.search(j.get("title", "")) for j in rows):
                return False
            blob = json.dumps(rows[:3]).lower()
            return bool(re.search(rf"(?<![a-z0-9.-]){re.escape(domain.lower())}(?![a-z0-9-])", blob))

        # Ashby, Lever and Workable expose no company field, so check whether
        # the public board page points back at the company's own site.
        pages = {
            "ashby": f"https://jobs.ashbyhq.com/{slug}",
            "lever": f"https://jobs.lever.co/{slug}",
            "workable": f"https://apply.workable.com/{slug}/",
        }
        page = pages.get(ats)
        if not page:
            return True
        r = httpx.get(page, headers=UA, timeout=20, follow_redirects=True)
        html = r.text.lower()
        # Match the domain as a whole host. A bare substring test would accept
        # flynavi.com as evidence for navi.com.
        host_rx = re.compile(rf"(?<![a-z0-9.-]){re.escape(domain.lower())}(?![a-z0-9-])")
        if host_rx.search(html):
            return True
        return len(root) > 5 and root in _norm(html[:40000])
    except Exception:
        return False


def slug_candidates(name, url):
    host = urlparse(url).netloc.replace("www.", "")
    root = host.split(".")[0]
    plain = re.sub(r"[^a-z0-9]", "", name.lower())
    hyphen = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    out = []
    for c in (root, plain, hyphen, root.replace("-", "")):
        if c and c not in out and len(c) > 2:
            out.append(c)
    return out[:4]


MISSING = re.compile(
    r"<title>[^<]*\b(404|page not found|not found|no longer (?:exists|available))\b",
    re.I,
)


def looks_missing(html, final_url):
    """A soft 404 still answers 200. Delhivery's careers link lands on a page
    at /404 that returns 200, and a stale path can serve a themed not-found
    page, so neither should be recorded as a careers page."""
    if MISSING.search(html[:4000]):
        return True
    return bool(re.search(r"/(404|not-found|page-not-found)(/|$)", final_url, re.I))


def find_careers(url):
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    host = parsed.netloc.replace("www.", "")

    # Always keep the standard paths as fallbacks, even when the registry
    # names a specific one, because careers pages move.
    tries = [url] if parsed.path not in ("", "/") else []
    tries += [base + p for p in CAREERS_PATHS]
    tries += [f"https://careers.{host}/", f"https://jobs.{host}/", base]

    best = None
    for candidate in dict.fromkeys(tries):
        try:
            r = httpx.get(candidate, headers=UA, timeout=18, follow_redirects=True)
        except Exception:
            continue
        if r.status_code != 200 or len(r.text) < 500:
            continue
        if looks_missing(r.text, str(r.url)):
            continue
        if best is None:
            best = (r.text, str(r.url))
        if any(re.search(p, r.text) for _, p in SIGNATURES):
            return r.text, str(r.url)
    return best if best else (None, url)


def resolve_one(company):
    name = company["name"]
    given = company["careers"]

    if company.get("ats"):
        return name, {"ats": company["ats"], "slug": company.get("slug", ""),
                      "careers": given, "source": "pinned"}

    html, final = find_careers(given)

    if html:
        for ats, pattern in SIGNATURES:
            m = re.search(pattern, html)
            if not m:
                continue
            if ats == "workday":
                slug = f"{m.group(1)}|{m.group(2)}|{m.group(3)}"
            elif ats == "successfactors":
                slug = ""
            else:
                slug = m.group(1)
            if verify(ats, slug):
                return name, {"ats": ats, "slug": slug, "careers": final,
                              "source": "sniffed"}

    for slug in slug_candidates(name, given):
        for ats in GUESSABLE:
            if verify(ats, slug) and identity_ok(ats, slug, company):
                return name, {"ats": ats, "slug": slug, "careers": final,
                              "source": f"guessed slug {slug}, identity checked"}

    return name, {"ats": "custom", "slug": "", "careers": final,
                  "source": "custom portal" if html else "unreachable"}


def main():
    companies = yaml.safe_load((ROOT / "companies.yml").read_text())["companies"]
    args = set(sys.argv[1:])
    resolved = json.loads(RESOLVED.read_text()) if RESOLVED.exists() else {}

    audit = "--audit" in args
    args.discard("--audit")
    limit = None
    for a in list(args):
        if a.startswith("--limit="):
            limit = int(a.split("=")[1]); args.discard(a)

    if limit is not None:
        companies = [c for c in companies if c["name"] not in resolved][:limit]
    elif args == {"--missing"}:
        companies = [c for c in companies
                     if resolved.get(c["name"], {}).get("ats", "custom") == "custom"
                     or c["name"] not in resolved]
    elif args:
        companies = [c for c in companies if c["name"] in args]

    if audit:
        by_name = {c["name"]: c for c in companies}
        bad = 0
        def recheck(item):
            n, info = item
            if "guessed" not in info.get("source", "") or n not in by_name:
                return n, info, True
            return n, info, identity_ok(info["ats"], info["slug"], by_name[n])
        with ThreadPoolExecutor(max_workers=10) as ex:
            for n, info, ok in ex.map(recheck, list(resolved.items())):
                if not ok:
                    print(f"dropped {n:26s} {info['ats']}/{info['slug']} is not this company")
                    resolved[n] = {"ats": "custom", "slug": "", "careers": info["careers"],
                                   "source": "guess failed identity check"}
                    bad += 1
        RESOLVED.write_text(json.dumps(resolved, indent=2, sort_keys=True))
        print(f"audited: {bad} wrong boards dropped")
        return

    done = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        for name, info in ex.map(resolve_one, companies):
            resolved[name] = info
            done += 1
            if info["ats"] != "custom":
                print(f"{name:28s} {info['ats']:15s} {info['slug'][:32]:32s} {info['source']}")
            if done % 15 == 0:   # checkpoint, so a timeout never loses work
                RESOLVED.write_text(json.dumps(resolved, indent=2, sort_keys=True))

    RESOLVED.write_text(json.dumps(resolved, indent=2, sort_keys=True))
    counts = {}
    for info in resolved.values():
        counts[info["ats"]] = counts.get(info["ats"], 0) + 1
    print(f"\nresolved {done}: " + json.dumps(counts))


if __name__ == "__main__":
    main()
