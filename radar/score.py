"""Turn a raw posting into a ranked one.

Sort order, highest priority first:
    1. location tier      (remote-into-India, then Noida down to Mumbai)
    2. experience fit     (2-5 years first, unstated next, 6+ last)
    3. disclosed salary   (high to low; undisclosed does not push a job down)
    4. match score        (title and skills against the resume profile)
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROFILE = yaml.safe_load((ROOT / "profile.yml").read_text())

DROP = 99  # location tier meaning "not somewhere I would work"

REMOTE = re.compile(r"\b(remote|home ?based|anywhere|work from home|wfh|distributed)\b", re.I)
INDIA_SCOPE = re.compile(r"\b(india|indian|apac|asia|worldwide|global(?:ly)?|anywhere)\b", re.I)
ELSEWHERE = re.compile(
    r"\b(usa|u\.s\.|united states|americas?|canada|emea|europe|england|uk|"
    r"united kingdom|germany|france|poland|spain|portugal|netherlands|sweden|"
    r"nordics|ireland|australia|singapore|japan|brazil|latam|mexico|dublin|"
    r"london|berlin|paris|new york|seattle|san francisco|austin|toronto|"
    r"amsterdam|tel aviv|dubai|malaysia|philippines|indonesia|vietnam)\b",
    re.I,
)


def location_tier(location, description, company_tier):
    """Lower is better. DROP means it is not somewhere you would work.

    The location field decides this, not the description: a job body that
    mentions an India office does not make a US-only role India-eligible.
    """
    loc = (location or "").strip()
    low = loc.lower()
    ranks = PROFILE["location_rank"]

    for city, rank in sorted(ranks.items(), key=lambda kv: kv[1]):
        if city == "remote_india":
            continue
        if re.search(rf"\b{re.escape(city)}\b", low):
            label = city.title()
            if REMOTE.search(low):
                label += " / Remote"
            return rank, label

    if REMOTE.search(low):
        india_scope = INDIA_SCOPE.search(low)
        if india_scope:
            # "Home based - EMEA" names a region that is not ours.
            if ELSEWHERE.search(low) and not re.search(r"\b(india|apac|asia)\b", low):
                return DROP, loc
            return ranks["remote_india"], f"Remote ({india_scope.group(0).title()})"
        if ELSEWHERE.search(low):
            return DROP, loc
        # A bare "Remote" from an India-based employer means India.
        if company_tier in ("india", "noida"):
            return ranks["remote_india"], "Remote (India)"
        return DROP, loc or "Remote"

    if not low:
        return (ranks["remote_india"], "Unspecified") if company_tier in ("india", "noida") else (DROP, "Unspecified")

    if ELSEWHERE.search(low):
        return DROP, loc

    if re.search(r"\b(india|bharat)\b", low):
        return ranks["bengaluru"], loc

    return DROP, loc


# -------------------------------------------------------------- experience

YEARS = [
    re.compile(r"(\d+)\s*(?:\+|plus)?\s*(?:-|to|–)\s*(\d+)\s*(?:\+)?\s*(?:years|yrs|yoe)", re.I),
    re.compile(r"(\d+)\s*\+\s*(?:years|yrs|yoe)", re.I),
    re.compile(r"(?:minimum|min\.?|at least)\s*(\d+)\s*(?:years|yrs)", re.I),
    re.compile(r"(\d+)\s*(?:years|yrs|yoe)", re.I),
]


def parse_years(text):
    if not text:
        return None, None
    window = text[:4000]
    m = YEARS[0].search(window)
    if m:
        return int(m.group(1)), int(m.group(2))
    for rx in YEARS[1:]:
        m = rx.search(window)
        if m:
            return int(m.group(1)), None
    return None, None


def experience_bucket(title, description):
    blob = f"{title} {description or ''}"
    lo, hi = parse_years(blob)
    cfg = PROFILE["experience"]
    t = (title or "").lower()

    if re.search(r"\b(intern|internship|trainee|fresher|graduate programme)\b", t):
        return 3, "Entry only"
    if re.search(r"\b(senior|sr\.?|lead|staff|principal|architect|manager|head)\b", t):
        if lo is not None and lo <= cfg["ideal_max"]:
            return 1, f"{lo}+ yrs, senior title"
        return 2, "Senior title"

    if lo is None:
        return 1, "Years not stated"
    if lo >= cfg["senior_from"]:
        return 2, f"{lo}+ yrs"
    if lo <= cfg["ideal_max"] and (hi is None or hi >= cfg["ideal_min"]):
        return 0, f"{lo}-{hi} yrs" if hi else f"{lo}+ yrs"
    if lo < cfg["ideal_min"]:
        return 0, f"{lo}+ yrs"
    return 1, f"{lo} yrs"


# ------------------------------------------------------------------ salary

LAKH = re.compile(
    r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:\.\d+)?)\s*(?:-|–|to)?\s*(\d{1,3}(?:\.\d+)?)?\s*"
    r"(?:lpa|lakhs?|lacs?|l\b)",
    re.I,
)
RUPEES = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]{6,12})", re.I)
USD = re.compile(r"\$\s*([\d,]{5,7})\s*(?:-|–|to)?\s*\$?\s*([\d,]{5,7})?", re.I)


def parse_salary_lpa(text):
    """Best disclosed annual figure, in lakhs per annum. None when unstated."""
    if not text:
        return None
    blob = text[:6000]

    m = LAKH.search(blob)
    if m:
        vals = [float(v) for v in m.groups() if v]
        top = max(vals)
        if 2 <= top <= 200:
            return round(top, 1)

    m = RUPEES.search(blob)
    if m:
        rupees = float(m.group(1).replace(",", ""))
        if rupees > 200000:  # annual figure, not a monthly stipend
            return round(rupees / 100000, 1)

    m = USD.search(blob)
    if m:
        vals = [float(v.replace(",", "")) for v in m.groups() if v]
        top = max(vals)
        if 20000 <= top <= 600000:
            return round(top * 88 / 100000, 1)  # rough USD to LPA

    return None


# ------------------------------------------------------------- match score


def match_score(title, description, department):
    t = (title or "").lower()
    blob = f"{t} {(description or '').lower()} {(department or '').lower()}"
    score, hits = 0, []

    for bad in PROFILE["exclude_titles"]:
        if bad in t:
            return 0, [f"excluded: {bad}"]

    title_points = 0
    for tier, points in (("strong", 30), ("good", 20), ("weak", 8)):
        for phrase in PROFILE["titles"][tier]:
            if phrase in t:
                title_points = max(title_points, points)
                if points >= 20:
                    hits.append(phrase)
    score += title_points

    for group, points, cap in (("core", 6, 36), ("supporting", 3, 15), ("domain", 4, 12)):
        got = 0
        for skill in PROFILE["skills"][group]:
            if re.search(rf"(?<![a-z]){re.escape(skill)}(?![a-z])", blob):
                got += points
                if len(hits) < 12:
                    hits.append(skill)
        score += min(got, cap)

    if not description:
        score += 5  # do not punish a portal that hides the body text

    # "machine learning engineer" and "machine learning" are one fact, not two.
    tidy = []
    for h in sorted(set(hits), key=len, reverse=True):
        if not any(h in kept and h != kept for kept in tidy):
            tidy.append(h)
    return min(score, 100), tidy[:8]


# ------------------------------------------------------- gaps and weak posts

# Things employers ask for that are not on your resume. Used to show what a
# posting wants that you would have to learn or argue around.
GAP_VOCAB = [
    "go", "golang", "rust", "java", "scala", "ruby", "php", "kotlin", "swift",
    "terraform", "snowflake", "databricks", "dbt", "bigquery", "redshift",
    "flink", "beam", "ray", "vertex ai", "bedrock", "gcp", "azure ml",
    "kubeflow", "triton", "vllm", "tensorrt", "jax", "deepspeed",
    "salesforce", "sap", "tableau", "power bi", "looker", "figma",
    "graphql", "grpc", "elasticsearch", "clickhouse", "cassandra", "neo4j",
]

WEAK_SIGNS = [
    (r"\b(unpaid|equity[ -]only|no salary|stipend)\b", "unpaid or equity only"),
    (r"\b(rockstar|ninja|guru|hustle|wear many hats)\b", "vague culture language"),
    (r"\b(bond|surety|training fee|security deposit)\b", "asks for a bond or fee"),
    (r"\b(immediate joiner|joining within \d+ days)\b", "wants an immediate joiner"),
    (r"\b(6 days|six days a week|saturday working)\b", "six-day week"),
]


def skill_gaps(description):
    """What the posting asks for that your resume does not claim."""
    if not description:
        return []
    blob = description.lower()
    mine = set()
    for group in ("core", "supporting", "domain"):
        mine.update(PROFILE["skills"][group])
    gaps = []
    for term in GAP_VOCAB:
        if term in mine:
            continue
        if re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", blob):
            gaps.append(term)
    return gaps[:6]


def posting_flags(job, description, salary):
    """Cues that a posting is weak or stale, so you can spend attention well."""
    flags = []
    blob = (description or "").lower()
    for pattern, label in WEAK_SIGNS:
        if re.search(pattern, blob):
            flags.append(label)
    if description and len(description) < 300:
        flags.append("thin description")
    age = posting_age_days(job.get("posted_at"))
    if age is not None and age > 45:
        flags.append(f"posted {age} days ago")
    return flags


def posting_age_days(posted_at):
    if not posted_at:
        return None
    try:
        when = datetime.fromisoformat(str(posted_at).replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - when).days)



# ---- language gate and deal-breakers -------------------------------------
# Borrowed from MadsLorentzen/ai-job-search: a posting that requires a
# language you do not work in is a hard reject, not a low score, and
# free-form deal-breakers veto by reason rather than by nudging a number.

LANGUAGE_NAMES = [
    "german", "french", "spanish", "portuguese", "italian", "dutch", "danish",
    "swedish", "norwegian", "finnish", "polish", "czech", "romanian", "greek",
    "turkish", "russian", "ukrainian", "arabic", "hebrew", "japanese",
    "mandarin", "cantonese", "chinese", "korean", "thai", "vietnamese",
    "indonesian", "malay", "tagalog", "bahasa",
]

# Built by concatenation, not str.format: the pattern carries regex
# quantifiers like {0,60} that format() would read as fields.
_LANGS = "|".join(LANGUAGE_NAMES)
REQUIRES_LANG = re.compile(
    r"\b(?:fluent|fluency|native|proficient|proficiency|business[- ]level|"
    r"c1|c2|b2|must speak|required to speak)\b[^.]{0,60}?\b(" + _LANGS + r")\b"
    r"|\b(" + _LANGS + r")\b[^.]{0,40}?\b(?:required|mandatory|fluency|native|is a must)\b",
    re.I,
)


def language_gate(text):
    """Return a veto reason when a posting needs a language you do not have."""
    if not text:
        return None
    mine = {l.lower() for l in PROFILE.get("languages", [])}
    blob = text[:6000]
    for m in REQUIRES_LANG.finditer(blob):
        found = next((g for g in m.groups() if g and g.lower() in LANGUAGE_NAMES), None)
        if found and found.lower() not in mine:
            return f"requires {found.lower()}"
    return None


def deal_breaker(text):
    if not text:
        return None
    blob = text[:6000]
    for rule in PROFILE.get("deal_breakers", []):
        if re.search(rule["pattern"], blob, re.I):
            return rule["reason"]
    return None


DEADLINE = re.compile(
    r"(?:apply|applications?|deadline|closes?|closing date)[^.\n]{0,30}?"
    r"(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}"
    r"|\d{4}-\d{2}-\d{2})",
    re.I,
)


def deadline_passed(text):
    """A posting past its own stated deadline is dead, however well it scores."""
    if not text:
        return None
    m = DEADLINE.search(text[:6000])
    if not m:
        return None
    raw = m.group(1)
    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            when = datetime.strptime(raw.replace(",", ""), fmt).replace(tzinfo=timezone.utc)
            return when if when < datetime.now(timezone.utc) else None
        except ValueError:
            continue
    return None


# ----------------------------------------------------------------- ranking


def rank(job, company_tier):
    title = job.get("title", "")
    desc = job.get("description", "")
    blob = f"{title} {desc}"

    tier, place = location_tier(job.get("location", ""), desc, company_tier)
    exp_bucket, exp_note = experience_bucket(title, desc)
    salary = parse_salary_lpa(blob)
    score, hits = match_score(title, desc, job.get("department", ""))

    ranks = PROFILE["location_rank"]
    if tier == ranks.get("mumbai") and place.lower().startswith("mumbai"):
        if salary is None or salary <= PROFILE["mumbai_min_lpa"]:
            tier = DROP  # your Mumbai rule: only worth it above the bar

    veto = language_gate(blob) or deal_breaker(blob)
    expired = deadline_passed(desc)
    if expired:
        veto = veto or f"deadline passed {expired.date()}"

    return {
        **job,
        "veto": veto,
        "skill_gaps": skill_gaps(desc),
        "flags": posting_flags(job, desc, salary),
        "age_days": posting_age_days(job.get("posted_at")),
        "location_tier": tier,
        "location_label": place,
        "experience_bucket": exp_bucket,
        "experience_note": exp_note,
        "salary_lpa": salary,
        "match_score": score,
        "match_hits": hits,
    }


SALARY_BAND = 10  # LPA. Salary outranks match score, but only in real steps.


def sort_key(job):
    salary = job["salary_lpa"] or 0
    return (
        job["location_tier"],
        job["experience_bucket"],
        -int(salary // SALARY_BAND),
        -job["match_score"],
        -salary,
    )
