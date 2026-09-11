# Job Radar — first push and go-live checklist

This file is written for **Claude Code**, running inside the `job-radar/`
folder on the user's machine, with `gh` already authenticated to their
GitHub account. Nothing here has been pushed to GitHub yet — this is a
first-time setup, not a fix to something broken.

Work through the steps in order. Stop and report back to the user if any
step's verification fails — don't silently continue past a failure, since
later steps depend on earlier ones actually working (a push that silently
failed means every later step is operating on nothing).

---

## 0. Preflight

Confirm the tools this all depends on before touching git or GitHub.

```bash
git --version
gh --version
gh auth status
```

If `gh auth status` shows not logged in, stop and tell the user to run
`gh auth login` first — everything past step 2 needs it.

Confirm you're in the right folder — it should directly contain
`companies.yml`, `profile.yml`, `radar/`, `docs/`, and `.github/workflows/daily.yml`:

```bash
ls
```

If any of those are missing, stop — this doc assumes the full project
folder from the zip, not a partial copy.

---

## 1. Initialize git and make the first commit

```bash
git init
git add .
git status --short   # sanity check: should list every project file, nothing more
git commit -m "job radar: initial push"
```

**Verify:** `git log --oneline -1` shows the commit you just made.

---

## 2. Create the GitHub repo and push

Ask the user once, briefly, whether the repo should be public or private —
this file contains no secrets and no personal data (the resume itself
isn't in this folder), but the user may still have a preference. Default
to `--private` if they don't answer, since that's the safer default and
easy to flip later in GitHub's settings.

```bash
gh repo create job-radar --private --source=. --push
```

**Verify:**
```bash
git remote -v          # should show an origin pointing at github.com/<user>/job-radar
gh repo view --web      # opens it in the browser so the user can see it landed
```

If `gh repo create` fails because a repo named `job-radar` already exists
under this account, ask the user whether to reuse it (then `git remote add
origin <url>` and `git push -u origin main` instead) or pick a different
name — don't silently overwrite something that might already contain
unrelated content.

---

## 3. Set the Firecrawl API key as a repo secret

The workflow reads `FIRECRAWL_API_KEY` from repo secrets. Without it, the
261 portals that need JavaScript rendering are silently skipped — only the
~82 portals with a plain API (Greenhouse, Lever, Ashby, etc.) will be read,
and the run will still report success. This is the single most common way
this setup half-works without anyone noticing.

**You do not have this key.** Ask the user for it directly — do not guess,
do not invent a placeholder, do not proceed without it. If they don't have
one yet, tell them to get it from https://firecrawl.dev (free tier exists)
and pause here until they provide it.

Once you have the key:

```bash
gh secret set FIRECRAWL_API_KEY --body "<the key the user gave you>"
```

**Verify:**
```bash
gh secret list
```
Confirm `FIRECRAWL_API_KEY` appears in the list. (`gh secret list` shows
names and last-updated dates only, never values — that's expected, not a
sign something failed.)

---

## 4. Give Actions write permission

This is the step most likely to be skipped, and skipping it produces a
uniquely confusing failure mode: the workflow run shows green, the log
looks fine, and `docs/jobs.json` **still never updates** — because the
commit-and-push step at the end fails quietly on a permissions error that
doesn't fail the whole job.

The `gh` CLI can set this directly:

```bash
gh api -X PUT repos/{owner}/{repo}/actions/permissions/workflow \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=false
```

Replace `{owner}/{repo}` with the actual values, or let `gh` infer them by
running this from inside the repo folder (gh resolves `{owner}/{repo}` from
the current directory's git remote automatically when you omit them —
safe to just try the literal command above first).

**Verify:**
```bash
gh api repos/{owner}/{repo}/actions/permissions/workflow
```
Confirm the response shows `"default_workflow_permissions":"write"`.

If the `gh api` call fails (some orgs restrict this via branch/org
policy), fall back to telling the user to do it by hand: repo → **Settings
→ Actions → General → Workflow permissions → Read and write permissions →
Save**. Don't spend more than one retry trying to force it via API if the
account's permissions don't allow it — that's a real org-level restriction,
not something to work around.

---

## 5. Turn on GitHub Pages

This is what makes `docs/index.html` into a real, live, daily-updating
website rather than just a file sitting in the repo.

```bash
gh api -X POST repos/{owner}/{repo}/pages \
  -f "source[branch]=main" \
  -f "source[path]=/docs"
```

**Verify:**
```bash
gh api repos/{owner}/{repo}/pages
```
Confirm the response includes a `"html_url"` field — that URL (something
like `https://<user>.github.io/job-radar/`) is the live board. Save it;
you'll need it in step 7.

If the POST returns a 409 (Pages already configured some other way) or a
404 (Pages needs to be enabled once by hand first on this account), fall
back to telling the user: repo → **Settings → Pages → Source: Deploy from
a branch → Branch: main, folder: /docs → Save**.

---

## 6. Trigger the first run by hand

Don't wait for the 9am IST cron. Confirm the whole pipeline actually works
today, while you're still here to see it fail if it's going to.

```bash
gh workflow run daily.yml
```

Wait about 15–20 seconds for GitHub to register the dispatch, then find
and watch the run:

```bash
gh run list --workflow=daily.yml --limit=1
gh run watch    # follow it live; takes several minutes end to end
```

**Verify — check all three:**
1. `gh run list --workflow=daily.yml --limit=1` shows a `completed` /
   `success` status, not `failure`.
2. Read the actual log for the "Read every career portal" step:
   `gh run view --log | grep -A5 "Read every career portal"`
   — confirm it reports reading portals with **no Firecrawl auth errors**.
   A key that's missing or wrong will show up here as 401/403 errors on
   the rendered-portal calls specifically, even though the job as a whole
   can still exit green.
3. Confirm the commit actually landed:
   `git pull && git log --oneline -3`
   — you should see a new `radar: <today's date>` commit that did **not**
   exist before this run, with `docs/jobs.json`'s modified time updated.
   If there's no new commit, step 4 (workflow permissions) is the most
   likely cause — go back and re-verify it.

If any of the three checks fail, report the specific failure back to the
user rather than re-running blind — the log from `gh run view --log` will
usually name the exact problem (missing secret, permission denied on push,
a portal timing out).

---

## 7. Report back

Once all three verifications in step 6 pass, tell the user:

- The repo URL
- The live Pages URL from step 5 (`html_url`)
- That the workflow will now also run automatically every day at 03:30 UTC
  (09:00 IST) with no further action needed
- A reminder that they can force a run anytime with
  `gh workflow run daily.yml` from this folder, or from the Actions tab
  in the GitHub web UI

---

## Reference: files already in this folder

Nothing below needs to be created — this is a checklist of what should
already exist, so you can sanity-check the folder before step 1 if
anything seems off.

| Path | What it is |
|---|---|
| `companies.yml` | Registry of ~347 companies and their career-page URLs |
| `profile.yml` | Resume-derived matching rules: titles, skills, location tiers, language gate, deal-breakers |
| `resolved.json` | Cache of which ATS platform each company's portal runs on |
| `radar/sources.py` | Per-ATS fetchers (Greenhouse, Lever, Ashby, SmartRecruiters, Workday, iCIMS, etc.) plus the Firecrawl-based renderer for custom portals |
| `radar/score.py` | Ranking: location tier → experience fit → salary → match score, plus the language gate and deal-breaker vetoes |
| `radar/run.py` | Orchestrator — reads every portal, ranks, dedupes, diffs against `state/seen.json`, writes `docs/jobs.json` |
| `radar/resolve.py` | Re-detects which ATS a company's portal is on (`--missing` for new companies, `--audit` to recheck guessed slugs) |
| `radar/notify.py` | Builds the digest used for the GitHub issue / email |
| `tools/build_registry.py` | Regenerates `companies.yml` from source lists |
| `tools/upskill.py` | Aggregates skill gaps across all live matches into `reports/skill-gaps.md` |
| `docs/index.html` | The live board — what GitHub Pages serves |
| `docs/jobs.json` / `docs/jobs.csv` | Latest run's ranked results |
| `.github/workflows/daily.yml` | The scheduled workflow itself — cron `30 3 * * *`, plus manual `workflow_dispatch` |
| `requirements.txt` | Python deps: `httpx`, `PyYAML` |

Nothing in this folder needs editing to get Path A running — this checklist
is purely about GitHub-side configuration (repo, secret, permissions,
Pages), not code changes.
