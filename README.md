# Reddit Lead Monitor

Watches a configured list of subreddits (posts + comments) for keyword
matches -- competitor names, switching/complaint phrasing -- and logs hits to
a Google Sheet for manual review. Built for Suburbly's contractor-pivot
outreach: catching people already naming a competitor or asking for a
recommendation, before you'd otherwise stumble on the thread.

Runs entirely on GitHub's own hosted runners on a schedule (`.github/workflows/monitor.yml`)
-- no machine of yours needs to stay on, and it's independent of any Claude
Code session. See `SETUP_CHECKLIST.md` for one-time setup (Reddit app,
Google service account, GitHub Secrets).

## How it works

Each run (`src/monitor.py`):
1. Loads `config.yaml` (subreddit list + keyword list -- edit this directly,
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

## Cost

Runs every 30 minutes by default -- about 1,440 Actions-minutes/month, which
is inside GitHub's free-tier allowance for a private repo (2,000 min/mo). If
you ever want a tighter interval (e.g. 15 min), make the repo **public**
first (unlimited free Actions minutes there) -- nothing sensitive is in this
repo either way, since credentials live only in GitHub Secrets, never in a
file.

## Local development / testing

```
pip install -r requirements.txt
export REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... REDDIT_USER_AGENT=...
export GOOGLE_SERVICE_ACCOUNT_JSON='...' SHEET_ID=...
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
  visibility gap). Keep the subreddit list niche/trade-focused.
- Matching is pure substring, case-insensitive -- no semantic understanding,
  no misspelling tolerance. Expect to tune `config.yaml` after seeing real
  false positives/negatives.
- GitHub disables scheduled workflows on a repo with no commits for 60 days
  -- if this "silently stops" long after setup with no code change, that's
  almost certainly why.
