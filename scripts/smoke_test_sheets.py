"""Manual smoke test for the Google Sheets side only -- no Reddit credentials
needed. Confirms the service account can actually reach the Sheet, create
the Leads/State tabs, write a row, and round-trip the State cursor, before
Reddit approval is even in the picture.

Run:
    export GOOGLE_SERVICE_ACCOUNT_JSON='...'
    export SHEET_ID=...
    python scripts/smoke_test_sheets.py

Not part of the pytest suite on purpose -- it needs real credentials and
makes real writes, so it's a manual, run-it-yourself check, not something
CI should ever execute.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sheets_client import (  # noqa: E402
    append_leads,
    ensure_leads_tab,
    ensure_state_tab,
    open_sheet,
    read_state,
    write_state,
)


def main() -> None:
    print("Opening Sheet...")
    sheet = open_sheet()
    print(f"  connected to: {sheet.title}")

    print("Ensuring Leads/State tabs exist...")
    leads_ws = ensure_leads_tab(sheet)
    state_ws = ensure_state_tab(sheet)
    print(f"  Leads tab rows: {leads_ws.row_count}, State tab rows: {state_ws.row_count}")

    print("Writing a marked test row to Leads...")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    append_leads(leads_ws, [[
        now, "SMOKE_TEST", "Post", "smoke-test-keyword", "smoke_test_author",
        "This is a smoke test row -- safe to delete",
        "Written by scripts/smoke_test_sheets.py to confirm write access.",
        "https://example.com/smoke-test", "t3_smoketest", "", "New",
        "Delete me -- smoke test only",
    ]])
    print("  row appended -- check the Leads tab for a SMOKE_TEST row.")

    print("Round-tripping the State cursor...")
    before = read_state(state_ws)
    write_state(state_ws, "smoke_test_post_cursor", "smoke_test_comment_cursor", status="smoke test ok")
    after = read_state(state_ws)
    assert after["last_post_fullname"] == "smoke_test_post_cursor"
    assert after["last_comment_fullname"] == "smoke_test_comment_cursor"
    print(f"  cursor before: {before}")
    print(f"  cursor after:  {after}")
    print("  round-trip OK.")

    print()
    print("SUCCESS -- Sheets side is fully working. Remember to:")
    print("  1. Delete the SMOKE_TEST row from Leads")
    print("  2. Restore State to blank cursors (or leave it -- next real run")
    print("     will just re-scan the last 100 items once, no harm done)")


if __name__ == "__main__":
    main()
