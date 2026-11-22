"""Scrape Claude Code skills from GitHub + merge with hand-curated seed.

Writes `../data/skills.json`. Idempotent: run as often as you want.

Strategy:
1. Load seed (hand-curated, highest trust).
2. Search GitHub for repos with topic:claude-code-skill.
3. For each new repo, fetch README's first 1000 chars → auto-generate description.
4. Merge, dedupe by slug, write.

Rate limits:
- Unauthenticated GitHub API: 60 req/hour. Fine for <60 new skills/run.
- Authenticated (GH_TOKEN env): 5000/hour.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Force UTF-8 on Windows stdout
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).parent.parent
SEED = Path(__file__).parent / "seed.json"
OUT = ROOT / "data" / "skills.json"

GH_SEARCH = "https://api.github.com/search/repositories?q={q}&sort=stars&per_page=100"
GH_SEARCH_CODE = "https://api.github.com/search/code?q={q}&per_page=50"
GH_README = "https://api.github.com/repos/{full_name}/readme"
GH_TREE = "https://api.github.com/repos/{full_name}/git/trees/{branch}?recursive=1"
GH_REPO = "https://api.github.com/repos/{full_name}"
GH_CONTENT = "https://api.github.com/repos/{full_name}/contents/{path}"

TOPICS = [
    "claude-code-skill",
    "claude-skill",
    "claude-code-plugin",
    "anthropic-skill",
    "claude-agent",
    "claude-code",
]

KEYWORD_QUERIES = [
    "claude-code skill in:name,description",
    "claude skill in:readme fork:false stars:>=2",
    "anthropic skill in:name fork:false",
]

# Hand-list of mono-repos that contain multiple skills as subdirectories.
# Scraper will enumerate their top-level folders and treat each as a skill.
MONOREPOS = [
    "anthropics/skills",
]

CATEGORY_BY_KEYWORD = {
    "pdf": "document-processing",
    "docx": "document-processing",
    "pptx": "document-processing",
    "xlsx": "document-processing",
    "csv": "document-processing",
    "excel": "document-processing",
    "word": "document-processing",
    "powerpoint": "document-processing",
    "google": "integrations",
    "slack": "integrations",
    "notion": "integrations",
    "linear": "integrations",
    "chart": "charts",
    "graph": "charts",
    "visualization": "charts",
    "dataviz": "charts",
    "research": "research",
    "web-search": "research",
    "code-review": "development",
    "review": "development",
    "test": "development",
    "lint": "development",
    "security": "security",
    "audit": "security",
    "cron": "automation",
    "schedule": "automation",
    "loop": "automation",
    "memory": "meta",
    "skill-creator": "meta",
    "plugin-dev": "meta",
    "mod": "meta",
}


def http_get(url: str) -> dict | list | None:
    headers = {
        "User-Agent": "claude-skills-dir-scraper/1.0",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GH_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[warn] fetch {url}: {e}", file=sys.stderr)
        return None


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return s or "untitled"


def guess_category(tags: list[str], name: str, desc: str) -> str:
    blob = " ".join(tags + [name.lower(), (desc or "").lower()])
    for k, cat in CATEGORY_BY_KEYWORD.items():
        if k in blob:
            return cat
    return "other"


def extract_description(readme_raw: str, max_len: int = 240) -> str:
    """Pull first meaningful paragraph from a README."""
    if not readme_raw:
        return ""
    # Strip images, badges, HTML comments, code fences.
    txt = re.sub(r"<!--.*?-->", "", readme_raw, flags=re.DOTALL)
    txt = re.sub(r"```[\s\S]*?```", "", txt)
    txt = re.sub(r"!\[.*?\]\(.*?\)", "", txt)
    txt = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", txt)
    # Drop headings + leading skills-frontmatter + badges rows.
    lines = []
    for line in txt.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#") or s.startswith("---") or s.startswith("|"):
            continue
        if s.lower().startswith(("name:", "description:", "author:", "version:")):
            continue
        lines.append(s)
        if sum(len(x) for x in lines) > max_len * 2:
            break
    desc = " ".join(lines)[:max_len].rsplit(" ", 1)[0].rstrip(",.")
    return desc


def enrich_from_repo(full_name: str, name: str, desc: str, tags: list[str]) -> dict:
    """Fetch README and distill long_description + fallback short_description."""
    readme = http_get(GH_README.format(full_name=full_name)) or {}
    content_b64 = readme.get("content", "") if isinstance(readme, dict) else ""
    try:
        import base64
        content = base64.b64decode(content_b64).decode("utf-8", errors="ignore") if content_b64 else ""
    except Exception:
        content = ""
    long_desc = extract_description(content, 420)
    short = desc or extract_description(content, 160)
    return {
        "long_description": long_desc,
        "short_description": short,
    }


def search_topic(topic: str) -> list[dict]:
    q = urllib.parse.quote(f"topic:{topic}")
    data = http_get(GH_SEARCH.format(q=q))
    if not isinstance(data, dict):
        return []
    return data.get("items", []) or []


def search_query(query: str) -> list[dict]:
    q = urllib.parse.quote(query)
    data = http_get(GH_SEARCH.format(q=q))
    if not isinstance(data, dict):
        return []
    return data.get("items", []) or []


def enumerate_monorepo(full_name: str) -> list[dict]:
    """Treat each top-level directory of a monorepo as a separate skill.

    Fetches the repo's default branch, lists root tree, and for each dir
    pulls its SKILL.md / README.md to build a skill record.
    """
    repo = http_get(GH_REPO.format(full_name=full_name))
    if not isinstance(repo, dict):
        return []
    branch = repo.get("default_branch") or "main"
    tree = http_get(GH_TREE.format(full_name=full_name, branch=branch))
    if not isinstance(tree, dict):
        return []

    top_dirs = sorted({
        item["path"].split("/")[0]
        for item in (tree.get("tree") or [])
        if item.get("type") == "tree" and "/" not in item["path"]
        and not item["path"].startswith(".")
    })

    results = []
    html_base = f"https://github.com/{full_name}/tree/{branch}"
    for d in top_dirs:
        # Try SKILL.md then README.md
        readme = (http_get(GH_CONTENT.format(full_name=full_name, path=f"{d}/SKILL.md"))
                  or http_get(GH_CONTENT.format(full_name=full_name, path=f"{d}/README.md"))
                  or {})
        content_b64 = readme.get("content", "") if isinstance(readme, dict) else ""
        try:
            import base64
            text = base64.b64decode(content_b64).decode("utf-8", errors="ignore") if content_b64 else ""
        except Exception:
            text = ""
        desc = extract_description(text, 160) or f"Claude skill from {full_name}"
        long_desc = extract_description(text, 400) or desc
        results.append({
            "name": d,
            "full_name": f"{full_name}/{d}",
            "slug_hint": d,
            "html_url": f"{html_base}/{d}",
            "description": desc,
            "long_description": long_desc,
            "topics": [full_name.split("/")[0]],
            "stargazers_count": repo.get("stargazers_count") or 0,
            "updated_at": repo.get("updated_at") or "",
            "author": full_name.split("/")[0],
        })
        time.sleep(0.3)
    return results


def monorepo_entry_to_skill(entry: dict) -> dict:
    name = entry["name"]
    return {
        "slug": slugify(name),
        "name": name.replace("-", " ").title(),
        "author": entry["author"],
        "author_url": f"https://github.com/{entry['author']}",
        "repo_url": entry["html_url"],
        "category": guess_category(entry.get("topics", []), name, entry.get("description", "")),
        "tags": entry.get("topics", []),
        "short_description": entry.get("description", ""),
        "long_description": entry.get("long_description", ""),
        "triggers": [],
        "price": "free",
        "stars": entry.get("stargazers_count", 0),
        "updated_at": (entry.get("updated_at") or "")[:10],
        "difficulty": "beginner",
        "featured": False,
    }


def repo_to_skill(repo: dict) -> dict | None:
    name = repo.get("name") or ""
    full_name = repo.get("full_name") or ""
    if not full_name:
        return None
    desc = repo.get("description") or ""
    tags = repo.get("topics") or []
    enriched = enrich_from_repo(full_name, name, desc, tags)
    return {
        "slug": slugify(name),
        "name": name.replace("-", " ").title(),
        "author": full_name.split("/")[0],
        "author_url": f"https://github.com/{full_name.split('/')[0]}",
        "repo_url": repo.get("html_url"),
        "category": guess_category(tags, name, desc),
        "tags": tags,
        "short_description": enriched["short_description"] or desc[:160],
        "long_description": enriched["long_description"] or desc,
        "triggers": [],
        "price": "free",
        "stars": repo.get("stargazers_count") or 0,
        "updated_at": (repo.get("updated_at") or "")[:10],
        "difficulty": "intermediate",
        "featured": False,
    }


ADDED_BASELINE = "2026-11-22"  # skills indexed before this date count as launch stock


def main() -> int:
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    by_slug: dict[str, dict] = {s["slug"]: s for s in seed}

    print(f"[seed] {len(seed)} hand-curated")

    # 1) Topic search
    for topic in TOPICS:
        print(f"[topic] {topic}")
        for repo in search_topic(topic):
            s = repo_to_skill(repo)
            if not s:
                continue
            if s["slug"] in by_slug:
                by_slug[s["slug"]]["stars"] = max(by_slug[s["slug"]].get("stars", 0), s["stars"])
                continue
            by_slug[s["slug"]] = s
            print(f"  + {s['slug']} ({s['stars']} stars)")
            time.sleep(0.3)

    # 2) Keyword search (catches un-tagged repos)
    for q in KEYWORD_QUERIES:
        print(f"[query] {q}")
        for repo in search_query(q):
            s = repo_to_skill(repo)
            if not s:
                continue
            if s["slug"] in by_slug:
                continue
            by_slug[s["slug"]] = s
            print(f"  + {s['slug']} ({s['stars']} stars)")
            time.sleep(0.3)

    # 3) Enumerate known monorepos
    for mono in MONOREPOS:
        print(f"[mono] {mono}")
        for entry in enumerate_monorepo(mono):
            s = monorepo_entry_to_skill(entry)
            if s["slug"] in by_slug:
                # Keep seed/first discovery; just bump stars
                by_slug[s["slug"]]["stars"] = max(by_slug[s["slug"]].get("stars", 0), s["stars"])
                continue
            by_slug[s["slug"]] = s
            print(f"  + {s['slug']} (mono: {entry['full_name']})")

    all_skills = sorted(
        by_slug.values(),
        key=lambda s: (not s.get("featured"), -s.get("stars", 0), s["slug"]),
    )
    # Remember when each skill first entered the index (drives the /new/ page)
    today = time.strftime("%Y-%m-%d", time.gmtime())
    prev_added: dict[str, str] = {}
    if OUT.exists():
        try:
            for p in json.loads(OUT.read_text(encoding="utf-8")):
                prev_added[p["slug"]] = p.get("added_at") or ADDED_BASELINE
        except (ValueError, KeyError, TypeError):
            prev_added = {}
    for s in all_skills:
        s["added_at"] = prev_added.get(s["slug"]) or (today if prev_added else ADDED_BASELINE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(all_skills, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[done] {len(all_skills)} skills → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
