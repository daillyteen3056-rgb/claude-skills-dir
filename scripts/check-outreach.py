"""Monitor awesome-list outreach issues weekly.

Checks each tracked issue:
- Is it closed? Report final state (merged/rejected/other).
- Still open + silent > NUDGE_DAYS? Post a polite bump (once).
- Stop bumping after MAX_NUDGES.

State lives in `data/outreach-state.json` and gets committed by the workflow.

Posting bumps needs a Personal Access Token in env `TRACK_TOKEN` with
`public_repo` scope. Without it, the script only reads status and prints
what it would do (dry-run).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
STATE_FILE = ROOT / "data" / "outreach-state.json"

TRACKED = [
    {"repo": "ComposioHQ/awesome-claude-skills", "issue": 2480},
    {"repo": "hesreallyhim/awesome-claude-code", "issue": 3670},
    {"repo": "sickn33/agentic-awesome-skills", "issue": 2437},
]

NUDGE_DAYS = 14
MAX_NUDGES = 2
BUMP_TEMPLATE = (
    "Gentle bump — wanted to follow up in case this slid down the queue. "
    "Happy to adjust the suggested entry, move it to a different section, "
    "or close this if the list isn't accepting new third-party aggregators. "
    "No worries either way, just didn't want it to disappear."
)


def http(url: str, method: str = "GET", body: dict | None = None) -> dict | list | None:
    token = os.environ.get("TRACK_TOKEN", "").strip()
    headers = {
        "User-Agent": "claude-skills-dir-monitor/1.0",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body else None
    if body:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status not in (200, 201):
                return None
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"[http] {method} {url} -> {e.code} {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[http] {method} {url} -> {e}", file=sys.stderr)
        return None


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"issues": {}}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"issues": {}}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def days_since(iso_ts: str) -> float:
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400


def fetch_issue(repo: str, number: int) -> dict | None:
    return http(f"https://api.github.com/repos/{repo}/issues/{number}")


def fetch_last_activity(repo: str, number: int) -> str | None:
    """Return ISO timestamp of the latest comment, or None if no comments."""
    comments = http(f"https://api.github.com/repos/{repo}/issues/{number}/comments?per_page=100")
    if not isinstance(comments, list) or not comments:
        return None
    return comments[-1].get("created_at")


def post_bump(repo: str, number: int) -> bool:
    if not os.environ.get("TRACK_TOKEN"):
        print("  [dry-run] TRACK_TOKEN not set; would post bump")
        return False
    url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    result = http(url, method="POST", body={"body": BUMP_TEMPLATE})
    return result is not None


def process_one(entry: dict, state: dict) -> dict:
    key = f"{entry['repo']}#{entry['issue']}"
    st = state["issues"].setdefault(key, {"nudges": 0, "last_nudge": None, "closed": False})

    issue = fetch_issue(entry["repo"], entry["issue"])
    if not issue:
        return {"key": key, "status": "fetch-failed"}

    state_str = issue.get("state", "open")
    comments_count = issue.get("comments", 0)
    title = issue.get("title", "")

    if state_str == "closed":
        st["closed"] = True
        reason = issue.get("state_reason") or "closed"
        return {
            "key": key,
            "status": "closed",
            "reason": reason,
            "title": title,
        }

    # Determine last activity (comment or issue creation)
    last_ts = fetch_last_activity(entry["repo"], entry["issue"]) or issue["created_at"]
    days_quiet = days_since(last_ts)

    # Any reply yet?
    has_reply = comments_count > st.get("nudges", 0)
    if has_reply:
        return {
            "key": key,
            "status": "replied",
            "comments": comments_count,
            "days_quiet": round(days_quiet, 1),
        }

    # Should we bump?
    if days_quiet >= NUDGE_DAYS and st["nudges"] < MAX_NUDGES:
        bumped = post_bump(entry["repo"], entry["issue"])
        if bumped:
            st["nudges"] += 1
            st["last_nudge"] = datetime.now(timezone.utc).isoformat()
            return {"key": key, "status": "bumped", "nudge": st["nudges"]}
        return {"key": key, "status": "bump-pending", "days_quiet": round(days_quiet, 1)}

    return {
        "key": key,
        "status": "waiting",
        "days_quiet": round(days_quiet, 1),
        "until_bump": max(0, round(NUDGE_DAYS - days_quiet, 1)),
    }


def main() -> int:
    state = load_state()
    print(f"Monitoring {len(TRACKED)} outreach issues\n")
    results = []
    for entry in TRACKED:
        r = process_one(entry, state)
        results.append(r)
        print(f"  {r}")
    save_state(state)
    print(f"\nState saved to {STATE_FILE.relative_to(ROOT)}")

    # Summary for GitHub Actions
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("# Outreach issue monitor\n\n")
            f.write("| Repo | Issue | Status | Detail |\n")
            f.write("|---|---|---|---|\n")
            for r in results:
                repo, _, num = r["key"].partition("#")
                detail = ", ".join(
                    f"{k}={v}" for k, v in r.items()
                    if k not in ("key", "status")
                )
                f.write(f"| {repo} | #{num} | **{r['status']}** | {detail} |\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
