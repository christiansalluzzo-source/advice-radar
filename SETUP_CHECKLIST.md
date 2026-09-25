# One-time setup

Do these once, in order. Nothing here needs to be repeated when
`config.yaml`'s keyword list or the `MONITORED_SUBREDDITS` secret changes
later.

## Current status (updated as we go)

- [x] Google service account created, Sheets API enabled, Sheet created and
  shared, `GOOGLE_SERVICE_ACCOUNT_JSON` + `SHEET_ID` secrets set and
  verified working end-to-end via `scripts/smoke_test_sheets.py`.
- [x] `MONITORED_SUBREDDITS` secret set with the starter list.
- [x] Repo created (`advice-radar`), made public (nothing sensitive in it --
  see README's "What's public and what isn't"), workflow pushed with the
  schedule trigger commented out.
- [x] `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` / `REDDIT_USER_AGENT`
  secrets exist but are **empty placeholders** -- fill in with real values
  once Reddit approves the request below, no other setup needed at that
  point.
- [ ] **Blocked on Reddit.** Legacy `reddit.com/prefs/apps` app creation now
  requires registering first -- see section A. Submitted a support ticket
  (category: Data Access Request → I'm a developer → "want to build a
  Reddit App that does not work in the Devvit ecosystem") describing this
  exact tool, honestly, as read-only with no automated posting/commenting/
  voting/messaging. No published turnaround time; anecdotally this can take
  weeks or go unanswered. Waiting.

## A. Reddit app access (do this part first -- it's the slow part)

Reddit's classic self-serve "create a script app" flow is gated now. The
`prefs/apps` page will let you fill out the form and pass the captcha, but
the actual creation request comes back rejected with a generic
"read our policies" message -- that's not a captcha or field problem, it
means the account hasn't been separately approved to use the Data API yet.

1. Read https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy
   first -- it governs what this tool is and isn't allowed to do. The short
   version: read-only, no automated posting/commenting/voting/messaging, no
   reselling or otherwise commercializing the data, don't misrepresent the
   use case. This tool's design already fits that (see README).
2. Go to https://www.reddit.com/wiki/api -- it points to a "submit a
   request" support form for exactly this ("Data Access Request" category).
3. Fill out that form honestly and specifically -- vague answers get vague
   (or no) responses. It asks for: what benefit the app has for Redditors,
   a detailed description of what it actually does, why Devvit doesn't fit,
   a link to the source code (this repo, already public so it's actually
   reviewable), the exact subreddit list, and the operating username (N/A
   here, since it's app-only OAuth with no logged-in account).
4. Wait. There's no published SLA. Anecdotal reports range from a couple
   weeks to no response at all.
5. **Once approved**, go to https://www.reddit.com/prefs/apps → "create
   another app…" → type **script** → name it something generic and
   low-signal (not "reddit" -- that word is rejected in app names, and
   avoid anything that describes what the tool does, same reasoning as the
   repo name) → redirect URI can be a placeholder (`http://localhost:8080`,
   unused for this auth flow).
6. After creating it, note two values:
   - **client_id** -- the string shown right under the app's name
   - **client_secret** -- the field labeled "secret"
7. Pick a User-Agent string in Reddit's required format, matching whatever
   name you used above: `github-actions:<app-name>:v1.0 (by /u/<your-reddit-username>)`
8. Overwrite the three empty placeholder secrets (`REDDIT_CLIENT_ID`,
   `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`) with the real values.

## B. Google service account + Sheet

1. https://console.cloud.google.com → create or pick a project → search
   "Google Sheets API" → **Enable**. **Don't skip this** -- creating the
   service account first and enabling the API after is a common trap; the
   API call fails with a 403 pointing you back to this exact step if you do
   it out of order.
2. IAM & Admin → Service Accounts → **Create Service Account** (no IAM roles
   needed -- access comes from sharing the Sheet, not from a role).
3. Open the service account → **Keys** tab → **Add Key** → **JSON** →
   downloads a file. Keep it private. Never commit it anywhere.
4. Create the actual Google Sheet you want results in (any name).
5. **Share** that Sheet with the service account's email address -- it's the
   `client_email` field inside the JSON key you downloaded -- and give it
   **Editor** access.
6. Copy the Sheet's ID from its URL: `https://docs.google.com/spreadsheets/d/`**`THIS_PART`**`/edit`.
7. You don't need to create the `Leads`/`State` tabs yourself -- the script
   creates them with headers on first run.
8. **Verify this whole side works right now**, without needing Reddit at
   all: set `GOOGLE_SERVICE_ACCOUNT_JSON` and `SHEET_ID` locally and run
   `python scripts/smoke_test_sheets.py` (see README). It writes one clearly
   marked test row and round-trips the `State` cursor -- delete the test row
   afterward, `State`'s test values are harmless to leave.

## C. GitHub repo + secrets

1. Create a new GitHub repo with a low-signal name, same reasoning as the
   Reddit app name above.
2. Push this code to it.
3. Repo → **Settings** → **Secrets and variables** → **Actions** → **New
   repository secret**, add all six (the three Reddit ones can be created
   with an empty value as placeholders if Reddit access is still pending --
   `gh secret set NAME --body ""` works fine, or leave the field blank in
   the web UI):
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` -- paste the **entire contents** of the
     downloaded JSON key file
   - `SHEET_ID`
   - `MONITORED_SUBREDDITS` -- comma-separated, no spaces needed either way,
     e.g. `Contractor,HVAC,Landscaping`. This is a secret rather than
     something in `config.yaml` on purpose -- it's the one part of this
     tool's targeting worth keeping off a public repo's diff.
4. Edit `config.yaml` with the real keyword list (the committed one is a
   placeholder -- safe starting point, not final). Subreddits are edited by
   updating the `MONITORED_SUBREDDITS` secret instead, not this file.
5. Settings → Actions → General → confirm workflows are allowed to run.
6. Decide repo visibility. Nothing sensitive is in the repo either way (see
   README) -- public just additionally gets unlimited free Actions minutes
   at any polling interval, and lets you actually link the repo in the
   Reddit access request above so it's reviewable.

## Testing before you trust it unattended

1. **Sheets-only smoke test first** (section B, step 8) -- this needs no
   Reddit access and can be done the moment the Google side is set up.
2. Once Reddit access is approved and the three secrets are filled in: a
   **local dry run** (see README's "Local development" section) -- confirms
   the whole pipeline works with fast feedback and full error output in
   your own terminal.
3. Push to GitHub, then run it manually a few times via the **Actions** tab
   → the workflow name → **Run workflow** (the `workflow_dispatch` trigger)
   -- watch the live log for each run.
4. Force a guaranteed match: temporarily add a very common word to
   `config.yaml`'s keywords, run once, confirm a correctly-formatted row
   appears in `Leads` with a working permalink, then revert the keyword.
5. Verify dedupe: run `workflow_dispatch` twice within a minute -- the
   second run's log should report 0 new matches, and `State`'s
   `last_run_utc` should have advanced both times.
6. Verify failure handling: temporarily break `SHEET_ID` (or un-share the
   Sheet), run once, confirm the Actions run shows red and you get GitHub's
   built-in failure-notification email, then restore it.
7. Only after 1-6 all pass, uncomment the schedule trigger in
   `.github/workflows/monitor.yml`. Check back after a day: Actions tab
   should show a consistent green run history, and `State.last_run_utc`
   should be recent (a simple "is this still alive?" heartbeat you can check
   from your phone).
