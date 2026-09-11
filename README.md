# Job Radar

Reads the careers portal of all 343 companies from your screenshots each morning
at 9:00 IST, keeps what fits your resume, ranks it, and tells you what is new.

It points at each company's own portal. Where that portal is built on Greenhouse,
Lever, Ashby, SmartRecruiters, Workable, Recruitee or Workday, it reads that
board's own feed, which is the same data the careers page renders and the same
apply link the careers page sends you to. Razorpay's careers page is a Greenhouse
board, BrowserStack's is Workday, Wingify's is Keka. Portals with no feed are
rendered and extracted with Firecrawl. Nothing comes from an aggregator.

## Setup

1. Create an empty GitHub repo and push these files to it.
2. Settings, Pages: set Source to "Deploy from a branch", branch `main`, folder
   `/docs`. Your board lands at `https://<you>.github.io/<repo>/`.
3. Settings, Actions, General: under Workflow permissions pick
   "Read and write permissions", so the run can commit results and open issues.
4. Settings, Secrets and variables, Actions: add `FIRECRAWL_API_KEY` from
   firecrawl.dev. Without it the run still works, it just skips the portals that
   need rendering, which is most of the NCR startups.
5. Actions tab, "Morning job radar", Run workflow. That first run fills the board.

Optional email on top of the GitHub issue: add `MAIL_USERNAME`, `MAIL_PASSWORD`
(a Gmail app password, not your login) and `MAIL_TO` as secrets.

## Daily

The workflow runs at 03:30 UTC, which is 09:00 IST. GitHub's scheduler is
best-effort and can drift ten or twenty minutes under load. Each run:

- reads every portal in `resolved.json`
- ranks and filters against `profile.yml`
- diffs against `state/seen.json` to find what is genuinely new
- writes `docs/jobs.json` and commits it
- opens a GitHub issue listing new roles above your score threshold, which
  GitHub emails you
- re-sniffs unresolved portals on Mondays and re-audits guessed boards, so a
  company migrating its ATS is picked up
- reads the whole registry on Sundays and the priority list on other days, so
  Firecrawl credits are not spent on 261 rendered portals every morning

## Ranking

Sorted by, in order:

1. **Location.** Remote that hires into India first, then Noida, Delhi,
   Gurugram, Bengaluru, Hyderabad, Pune, Mumbai. Anywhere else is dropped.
   Mumbai only survives if the posting discloses more than 24 LPA.
2. **Experience.** 2 to 5 years first, unstated next, 6+ and senior titles last.
3. **Salary,** high to low, in 10 LPA bands so a small disclosed gap cannot bury
   a much better match. Most Indian postings disclose nothing; those are not
   pushed down for it.
4. **Match score,** your titles and skills from `profile.yml` against the
   posting. Below 20 a posting is not shown at all.

A remote role only counts as remote if its own location field says India, APAC,
Asia, worldwide or anywhere. A US-only role whose description happens to mention
an India office does not qualify.

## What each run tracks

- **Freshness.** Every job carries first-seen and last-seen. A role that stops
  appearing for 21 days is treated as filled and dropped from state.
- **Duplicates.** Same company, title and location collapses to one row, and
  utm, gh_, ref and lever tracking parameters are stripped from URLs first.
- **Skill gaps.** Dashed tags on a row are what the posting asks for that your
  resume does not claim: Go, Rust, Terraform, Snowflake, vLLM and so on.
- **Weak postings.** Red tags flag unpaid or equity-only roles, bond or
  training-fee demands, six-day weeks, thin descriptions and stale listings.
- **Outputs.** `docs/jobs.json` for the board, `docs/jobs.csv` for a
  spreadsheet, and `reports/YYYY-MM-DD.md` as a dated archive of what was new.

## Borrowed from ai-job-search

Four ideas taken from [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search):

- **Language gate.** A posting that requires a language absent from your
  `languages:` list is hard-rejected, not merely scored low. Declaring a
  higher level than yours in a language you do have is flagged instead, so a
  borderline case gets your judgement.
- **Free-form deal-breakers.** `deal_breakers:` in `profile.yml` is a list of
  pattern and reason. Unpaid roles, service bonds, six-day weeks and
  bring-your-own-hardware veto by name. Add a line, no code change.
- **Deadline expiry.** A posting past its own stated application deadline is
  dropped however well it scores.
- **Postings are untrusted input.** The Firecrawl extraction prompt now states
  that page content is data to transcribe, never instruction, so a careers
  page cannot steer the extractor into inventing rows or following links.

`python3 tools/upskill.py` writes `reports/skill-gaps.md`: the same per-job
gaps aggregated across the whole board, ranked by how many postings each one
blocks and the average match score of those postings. Go blocks 28 roles
averaging 33; Bedrock blocks only 3 but they average 64, which is the more
interesting number.

## Why the board might look stale

The published claude.ai artifact is a **snapshot**: the jobs are baked into the
file. It shows a Refresh button when opened from claude.ai, which re-reads 30
portals live through your Firecrawl connector, but it does not update on its
own and never will.

Daily updating is the GitHub Pages board, and only after you have pushed this
repo. If it stops updating, check in this order:

1. Actions tab, "Morning job radar": is there a run today? No run at all means
   the schedule is not firing.
2. **GitHub disables scheduled workflows after 60 days without repository
   activity.** The run now writes `state/heartbeat.txt` every day so the repo
   is never quiet, but if it already lapsed, GitHub shows a banner on the
   Actions tab with a button to re-enable it.
3. Scheduled runs only fire from the **default branch**. A workflow file on a
   feature branch never runs on cron.
4. Settings, Actions, General, Workflow permissions must be
   "Read and write", or the commit step fails and the board never changes even
   though the run succeeded.
5. GitHub's scheduler is best-effort and drops runs under load. A missed
   morning is normal; three in a row is not.
6. `FIRECRAWL_API_KEY` missing or out of credits means only the 82 API portals
   are read. The run still succeeds, so check the log line for how many
   portals it actually read.

## The board

Keyboard: `j` and `k` move, `o` opens, `a` marks applied, `s` saves, `x`
dismisses, `/` focuses search. There is a match-score slider, a search box,
filters for new, remote, NCR, salary-shown and no-red-flags, and a CSV export
of whatever is currently on screen. Status is kept in your browser, so it is
per device and never leaves it.

## How portals are resolved

`radar/resolve.py` runs three passes per company, cheapest first.

1. **Find the careers page.** Twelve common paths plus the careers and jobs
   subdomains. Soft 404s are rejected: Delhivery's careers link lands on a page
   at `/404` that still answers 200, and a stale path often serves a themed
   not-found page.
2. **Sniff the HTML** for nineteen ATS signatures, then verify against that
   board's API before trusting it.
3. **Guess and verify.** Derive slug candidates from the name and domain, try
   them against six boards, and keep only what passes an identity check.

That identity check matters. Slug guessing finds real boards belonging to
other people: `recruitee/google` is a demo tenant full of sample postings,
`smartrecruiters/uber` holds one job called Test UAT, and `ashby/navi` is a San
Francisco startup rather than the Indian lender. A guessed board is kept only
when it names the company, or its public page points back at the company's own
domain as a whole host. Four wrong boards were dropped this way.

Current spread across 343 companies: 82 on a readable API (28 Greenhouse,
13 Ashby, 10 Lever, 9 Workday, 7 SmartRecruiters, 3 Eightfold, 3 Keka, plus
Recruitee, Workable, iCIMS, BambooHR, Darwinbox, Zoho Recruit and
SuccessFactors), and 261 rendered by Firecrawl.

## Files

| Path | What it does |
|---|---|
| `companies.yml` | The company list and each one's own careers URL |
| `profile.yml` | Your titles, skills, location order and thresholds |
| `resolved.json` | What each portal turned out to run on. Written by the resolver |
| `radar/resolve.py` | Sniffs a careers page, verifies the board answers, records it |
| `radar/sources.py` | One fetcher per portal technology |
| `radar/score.py` | Location tier, experience bucket, salary parsing, match score |
| `radar/run.py` | Reads everything, ranks, diffs, writes `docs/jobs.json` |
| `radar/notify.py` | Builds the morning digest |
| `tools/build_registry.py` | Regenerates `companies.yml` from the source lists |
| `docs/index.html` | The board |
| `docs/jobs.csv` | The same matches as a spreadsheet |
| `reports/` | One dated markdown report per run |

## Tuning

Add a company: append it to `companies.yml` with its careers URL, then
`python -m radar.resolve "Company Name"`. Leave `ats` blank and the resolver
works it out.

Change what counts as a match: edit `profile.yml`. Nothing in the code needs
touching for weights, titles, skills, city order or the Mumbai bar.

Check a single company by hand: `python -m radar.run --only "Razorpay"`.

Re-resolve only the portals that are still unresolved:
`python -m radar.resolve --missing`. Re-check every guessed board:
`python -m radar.resolve --audit`.

Move a company between the daily and weekly scan: change its `priority` in
`companies.yml`. 1 is daily, 2 is Sundays only.

## Known limits

- Some portals hide the job body behind a click, so those postings score on
  title alone. They score lower than they deserve rather than higher.
- Where a careers page opens jobs in a modal instead of its own URL, the link
  goes to the careers page.
- Salary in USD is converted at a flat rate for ordering. Treat it as a sort
  key, not an offer.
- Firecrawl extraction costs credits per portal per run. The daily scan reads
  about 35 rendered portals, the Sunday scan all 261. Raise or lower that by
  editing `priority` in `companies.yml`.
- Recruitment agencies post client roles without naming the client, so their
  rows carry less signal than a direct employer's. They are all priority 2.
- remoteatlas.app advertises 3,705 companies, but its listings are
  overwhelmingly locked to one region: "United States - Remote", "Remote —
  France". Searching it for India mostly returns Indianapolis and Indiana.
  Four companies there genuinely name India inside the hiring scope, and those
  four are in the registry.
- One dead entry remains: Bloc was acquired and its domain now redirects to
  Chegg's Workday board, which rejects the site name it advertises. The run
  reports it as a failure rather than hiding it.
