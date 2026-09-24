# One-time setup

Do these once, in order. Nothing here needs to be repeated when
`config.yaml`'s subreddit/keyword list changes later.

## A. Reddit app (no password needed)

1. Go to https://www.reddit.com/prefs/apps
2. "create another app…" → type **script** → name it something like
   `suburbly-lead-monitor` → redirect URI can be a placeholder
   (`http://localhost:8080`) -- it's unused for this auth flow.
3. After creating it, note two values:
   - **client_id** -- the string shown right under the app's name
   - **client_secret** -- the field labeled "secret"
4. Pick a User-Agent string in Reddit's required format:
   `github-actions:suburbly-lead-monitor:v1.0 (by /u/<your-reddit-username>)`

## B. Google service account + Sheet

1. https://console.cloud.google.com → create or pick a project → search
   "Google Sheets API" → **Enable**.
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
   creates them with headers on first run. (You can pre-create them if
   you'd rather see them exist before the first run.)

## C. GitHub repo + secrets

1. Create a new **private** GitHub repo (e.g. `reddit-lead-monitor`).
2. Push this code to it.
3. Repo → **Settings** → **Secrets and variables** → **Actions** → **New
   repository secret**, add all five:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`
   - `REDDIT_USER_AGENT`
   - `GOOGLE_SERVICE_ACCOUNT_JSON` -- paste the **entire contents** of the
     downloaded JSON key file
   - `SHEET_ID`
4. Edit `config.yaml` with the real subreddit/keyword list (the committed
   one is a placeholder -- safe starting point, not final).
5. Settings → Actions → General → confirm workflows are allowed to run.

## Testing before you trust it unattended

1. **Local dry run** first (see README's "Local development" section) --
   confirms credentials work and rows land in the Sheet correctly, with
   fast feedback and full error output in your own terminal.
2. Push to GitHub, then run it manually a few times via the **Actions** tab
   → *Reddit Lead Monitor* → **Run workflow** (the `workflow_dispatch`
   trigger) -- watch the live log for each run.
3. Force a guaranteed match: temporarily add a very common word to
   `config.yaml`'s keywords, run once, confirm a correctly-formatted row
   appears in `Leads` with a working permalink, then revert the keyword.
4. Verify dedupe: run `workflow_dispatch` twice within a minute -- the
   second run's log should report 0 new matches, and `State`'s
   `last_run_utc` should have advanced both times.
5. Verify failure handling: temporarily break `SHEET_ID` (or un-share the
   Sheet), run once, confirm the Actions run shows red and you get GitHub's
   built-in failure-notification email, then restore it.
6. Only after 1-5 all pass, leave it on the cron schedule. Check back after
   a day: Actions tab should show a consistent green run history, and
   `State.last_run_utc` should be recent (a simple "is this still alive?"
   heartbeat you can check from your phone).
