"""gspread auth + the Leads/State worksheet contract.

State lives in a tab of the same Sheet rather than a committed file -- see
the plan doc's "State/dedupe" section for why. Layout: column A holds a
human-readable label, column B holds the value, so opening the State tab by
hand is self-explanatory even though nothing should hand-edit it.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

LEADS_HEADERS = [
    "Timestamp (UTC)",
    "Subreddit",
    "Type",
    "Matched Keywords",
    "Author",
    "Title",
    "Snippet",
    "Permalink",
    "Fullname",
    "Category",
    "Status",
    "Notes",
]

STATE_ROWS = [
    ("last_post_fullname", ""),
    ("last_comment_fullname", ""),
    ("last_run_utc", ""),
    ("last_run_status", ""),
]


def open_sheet() -> gspread.Spreadsheet:
    creds_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ["SHEET_ID"])


def get_or_create_worksheet(sheet: gspread.Spreadsheet, title: str, rows: int, cols: int) -> gspread.Worksheet:
    try:
        return sheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return sheet.add_worksheet(title=title, rows=rows, cols=cols)


def ensure_leads_tab(sheet: gspread.Spreadsheet) -> gspread.Worksheet:
    ws = get_or_create_worksheet(sheet, "Leads", rows=1000, cols=len(LEADS_HEADERS))
    if ws.row_values(1) != LEADS_HEADERS:
        ws.update("A1", [LEADS_HEADERS])
    return ws


def ensure_state_tab(sheet: gspread.Spreadsheet) -> gspread.Worksheet:
    ws = get_or_create_worksheet(sheet, "State", rows=10, cols=2)
    if not ws.acell("A1").value:
        ws.update("A1", [[label, value] for label, value in STATE_ROWS])
    return ws


def read_state(state_ws: gspread.Worksheet) -> dict[str, str]:
    values = state_ws.get("A1:B4")
    state = {label: "" for label, _ in STATE_ROWS}
    for row in values:
        if len(row) >= 2:
            state[row[0]] = row[1]
        elif len(row) == 1:
            state[row[0]] = ""
    return state


def write_state(state_ws: gspread.Worksheet, last_post_fullname: str, last_comment_fullname: str, status: str) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state_ws.update(
        "A1:B4",
        [
            ["last_post_fullname", last_post_fullname],
            ["last_comment_fullname", last_comment_fullname],
            ["last_run_utc", now],
            ["last_run_status", status],
        ],
    )


def append_leads(leads_ws: gspread.Worksheet, rows: list[list[str]]) -> None:
    if not rows:
        return
    leads_ws.append_rows(rows, value_input_option="USER_ENTERED")
