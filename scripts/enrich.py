#!/usr/bin/env python3
"""Enrich data/skills.json with facts read straight from each skill's GitHub repo.

Writes data/skill_meta.json keyed by slug:
  license, pushed_at, archived, skill_path, skill_md (frontmatter + outline + excerpt),
  has_scripts, skill_count (for collections), has_marketplace (.claude-plugin/ at repo root).

Uses the GitHub GraphQL API in batches (one query covers ~20 skills), so a full run
costs a few dozen requests. Needs GH_TOKEN (the Actions GITHUB_TOKEN is enough).
Existing entries are kept when a repo can't be read this run.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data" / "skills.json"
META = PROJECT / "data" / "skill_meta.json"
API = "https://api.github.com/graphql"
BATCH = 20
CODE_EXT = (".py", ".sh", ".js", ".mjs", ".ts", ".ps1", ".rb", ".go", ".bash")
CODE_DIRS = {"scripts", "bin", "tools", "src"}


def split_repo(url: str) -> tuple[str, str, str] | None:
    m = re.match(r"https?://github\.com/([^/]+)/([^/#?]+)(?:/tree/[^/]+/(.+))?", (url or "").rstrip("/"))
    if not m:
        return None
    return m.group(1), m.group(2).removesuffix(".git"), (m.group(3) or "").strip("/")


def gql(query: str, token: str) -> dict:
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
        "User-Agent": "skillnest-enrich/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:  # noqa: BLE001
            print(f"[warn] graphql attempt {attempt + 1}: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
    return {}


TREE = "... on Tree { entries { name type } }"
BLOB = "... on Blob { text byteSize }"


def obj(alias: str, expr: str, frag: str) -> str:
    return f"{alias}: object(expression: {json.dumps(expr)}) {{ {frag} }}"


def repo_block(alias: str, owner: str, name: str, parts: list[str]) -> str:
    return (f"{alias}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) {{ "
            f"licenseInfo {{ spdxId name }} pushedAt isArchived " + " ".join(parts) + " }")


def first_pass_parts(sub: str) -> list[str]:
    parts = [obj("root", "HEAD:", TREE)]
    if sub:
        parts += [obj("md", f"HEAD:{sub}/SKILL.md", BLOB), obj("dir", f"HEAD:{sub}", TREE)]
    else:
        parts += [obj("md", "HEAD:SKILL.md", BLOB),
                  obj("skills", "HEAD:skills", TREE),
                  obj("cskills", "HEAD:.claude/skills", TREE)]
    return parts


def parse_skill_md(text: str) -> dict:
    text = (text or "").replace("\r\n", "\n")
    fm: dict[str, str] = {}
    body = text
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if m:
        body = m.group(2)
        key = None
        for line in m.group(1).split("\n"):
            km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if km:
                key = km.group(1)
                val = km.group(2).strip()
                fm[key] = "" if val in ("|", ">", "|-", ">-") else val.strip("\"'")
            elif key and line.startswith((" ", "\t")):
                fm[key] = (fm[key] + " " + line.strip()).strip()
    outline = [re.sub(r"[*`_]", "", h).strip()
               for h in re.findall(r"^#{1,3}\s+(.+)$", body, re.M)][:12]
    clean = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    clean = re.sub(r"<[^>]+>", "", clean).strip()
    excerpt = clean[:900]
    if len(clean) > 900:
        excerpt = excerpt[: excerpt.rfind("\n")] if "\n" in excerpt[400:] else excerpt
        excerpt = excerpt.rstrip() + "\n…"
    return {
        "name": fm.get("name", "")[:80],
        "description": fm.get("description", "")[:1024],
        "keys": sorted(fm)[:12],
        "outline": outline,
        "excerpt": excerpt,
        "lines": body.count("\n") + 1,
    }


def has_code(entries: list[dict] | None) -> bool:
    for e in entries or []:
        n = e.get("name", "").lower()
        if e.get("type") == "tree" and n in CODE_DIRS:
            return True
        if e.get("type") == "blob" and n.endswith(CODE_EXT):
            return True
    return False


def tree_dirs(node: dict | None) -> list[str]:
    return [e["name"] for e in (node or {}).get("entries", []) if e.get("type") == "tree" and not e["name"].startswith(".")]


def main() -> int:
    token = os.environ.get("GH_TOKEN", "").strip()
    if not token:
        print("[enrich] no GH_TOKEN, skipping")
        return 0
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    skills = raw if isinstance(raw, list) else raw.get("skills", [])
    meta: dict = json.loads(META.read_text(encoding="utf-8")) if META.exists() else {}

    jobs = []
    for s in skills:
        sp = split_repo(s.get("repo_url", ""))
        if sp:
            jobs.append((s["slug"], *sp))
    print(f"[enrich] {len(jobs)} skills")

    second: list[tuple[str, str, str, str, list[str]]] = []
    found: dict[str, dict] = {}
    for i in range(0, len(jobs), BATCH):
        chunk = jobs[i:i + BATCH]
        q = "query { " + " ".join(repo_block(f"r{k}", o, n, first_pass_parts(sub))
                                  for k, (_, o, n, sub) in enumerate(chunk)) + " rateLimit { remaining } }"
        res = gql(q, token)
        data = res.get("data") or {}
        for k, (slug, o, n, sub) in enumerate(chunk):
            r = data.get(f"r{k}")
            if not r:
                continue
            root = (r.get("root") or {}).get("entries") or []
            m = {
                "license": ((r.get("licenseInfo") or {}).get("spdxId") or "").replace("NOASSERTION", "Other"),
                "pushed_at": (r.get("pushedAt") or "")[:10],
                "archived": bool(r.get("isArchived")),
                "has_marketplace": any(e["name"] == ".claude-plugin" and e["type"] == "tree" for e in root),
                "skill_path": sub,
            }
            md = (r.get("md") or {}).get("text")
            if md is not None:
                m["skill_md"] = parse_skill_md(md)
                m["has_scripts"] = has_code((r.get("dir") or {}).get("entries") if sub else root)
            else:
                for base, node in (("skills", r.get("skills")), (".claude/skills", r.get("cskills"))):
                    dirs = tree_dirs(node)
                    if dirs:
                        m["skill_count"] = len(dirs)
                        pick = next((d for d in dirs if d.lower() in (slug.lower(), n.lower())), dirs[0])
                        second.append((slug, o, n, f"{base}/{pick}", dirs))
                        break
            found[slug] = m
        print(f"[enrich] batch {i // BATCH + 1}: ok={sum(1 for k in range(len(chunk)) if data.get(f'r{k}'))} "
              f"remaining={(data.get('rateLimit') or {}).get('remaining')} errors={len(res.get('errors') or [])}")

    for i in range(0, len(second), BATCH):
        chunk = second[i:i + BATCH]
        q = "query { " + " ".join(
            repo_block(f"r{k}", o, n, [obj("md", f"HEAD:{p}/SKILL.md", BLOB), obj("dir", f"HEAD:{p}", TREE)])
            for k, (_, o, n, p, _) in enumerate(chunk)) + " }"
        data = gql(q, token).get("data") or {}
        for k, (slug, o, n, p, dirs) in enumerate(chunk):
            r = data.get(f"r{k}") or {}
            md = (r.get("md") or {}).get("text")
            if md is not None:
                found[slug]["skill_md"] = parse_skill_md(md)
                found[slug]["skill_md_path"] = p
                found[slug]["has_scripts"] = has_code((r.get("dir") or {}).get("entries"))

    for slug, m in found.items():
        meta[slug] = m
    live = {j[0] for j in jobs}
    meta = {k: v for k, v in sorted(meta.items()) if k in live}
    META.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with_md = sum(1 for v in meta.values() if v.get("skill_md"))
    print(f"[enrich] wrote {len(meta)} entries, {with_md} with SKILL.md, {len(found)} refreshed this run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
