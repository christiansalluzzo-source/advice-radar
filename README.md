# Advice Radar

Watches a small list of subreddits (posts + comments) for people asking for
advice or describing a problem in areas I can actually help with, and logs
matches to a Google Sheet so I can look them over and decide, case by case,
whether I have something useful to offer. Read-only -- it never posts,
comments, votes, or messages anyone on its own.

Runs entirely on GitHub's own hosted runners on a schedule
(`.github/workflows/monitor.yml`) -- no machine of yours needs to stay on,
and it's independent of any Claude Code session. See `SETUP_CHECKLIST.md`
for one-time setup (Reddit app, Google service account, GitHub Secrets).

## How it works

Each run (`src/monitor.py`):
1. Loads the subreddit list from the `MONITORED_SUBREDDITS` secret and the
   keyword list from `config.yaml` (edit the keyword list directly,
   including from GitHub's web UI on a phone, no code changes needed).
2. Fetches new posts and new comments across all configured subreddits in
   two API calls total (Reddit's multireddit syntax), regardless of how many
   subreddits are listed.
3. Matches each item's text against the keyword list (case-insensitive
   substring).
4. Appends any matches to the `Leads` tab of the configured Google Sheet.
5. Advances a `last-seen` cursor in the `State` tab so the same post/comment
   is never logged twice.

**First run for a fresh Sheet primes the cursor without emitting any
matches** -- it won't dump a backlog of historical posts the first time it
runs, only things that are new *after* that first run.

## The Sheet

- **`Leads`** -- what you review. Columns: Timestamp, Subreddit, Type
  (Post/Comment), Matched Keywords, Author, Title, Snippet, Permalink,
  Fullname, **Category** (blank by default -- fill in manually: *Product
  Insight / DM Candidate / Test Candidate / Multiple*), **Status** (`New` by
  default -- update to `DM Sent` / `Not Relevant` / `Replied` as you triage),
  Notes.
- **`State`** -- internal bookkeeping (last-seen cursors, last run time/status).
  Don't hand-edit; worst case if you do is the next run re-scans the last 100
  items, not a crash.

## What's public and what isn't

This repo is public. That means the code and `config.yaml` (just the
keyword list) are visible to anyone. It does **not** mean anyone can act on
this repo, run it, or see anything sensitive:

- **Secrets are never exposed**, in the repo or in logs -- GitHub encrypts
  them and automatically masks their values (`***`) anywhere they'd appear
  in an Actions log, and there's no UI or API that reveals a saved secret's
  value again, ever, to anyone including the repo owner.
- **The subreddit list lives in a secret** (`MONITORED_SUBREDDITS`), not in
  a committed file, specifically so it isn't part of the public diff.
- **Only someone with write access can trigger a run, change a secret, or
  edit the schedule** -- public visibility is read-only for everyone else.
  A public repo's Actions run logs are visible to anyone, which is why
  `monitor.py` only ever prints counts (e.g. "3 posts matched"), never the
  actual matched content, keywords, or subreddit names, to those logs.
- **The Google Sheet itself stays private** regardless of repo visibility --
  it's a separate system, shared only with the service account and you.

## Cost

Runs every 30 minutes by default -- about 1,440 Actions-minutes/month. On a
public repo, GitHub Actions minutes on standard runners are unlimited and
free regardless of interval, so this isn't a real constraint here.

## Local development / testing

```
pip install -r requirements.txt
export REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... REDDIT_USER_AGENT=...
export GOOGLE_SERVICE_ACCOUNT_JSON='...' SHEET_ID=...
export MONITORED_SUBREDDITS=Contractor,HVAC,Landscaping
python src/monitor.py
```

Unit tests (no network, no credentials needed):
```
pip install pytest
pytest tests/
```

## Known limitations

- Reddit's `/comments` endpoint only returns a recent window of comments
  network-wide for the configured subreddits -- a high-volume subreddit or a
  long gap between runs can miss comments silently (not an error, just a
  visibility gap). Keep the subreddit list niche/topic-focused.
- Matching is pure substring, case-insensitive -- no semantic understanding,
  no misspelling tolerance. Expect to tune `config.yaml` and
  `MONITORED_SUBREDDITS` after seeing real false positives/negatives.
- GitHub disables scheduled workflows on a repo with no commits for 60 days
  -- if this "silently stops" long after setup with no code change, that's
  almost certainly why.
