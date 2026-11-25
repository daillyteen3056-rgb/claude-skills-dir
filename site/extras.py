"""Skill-page enrichment, author badge, public API, new-skills feed and troubleshooting guides.

Imported by build.py; every function takes what it needs as arguments so this module
has no import-time dependency on build.py.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OFFICIAL_OWNERS = {
    "anthropics", "vercel-labs", "vercel", "microsoft", "openai", "google", "google-gemini", "firebase",
    "supabase", "stripe", "cloudflare", "huggingface", "getsentry", "expo", "remotion-dev", "github",
    "aws", "awslabs", "hashicorp", "heygen-com", "figma", "get-convex", "netlify", "prisma", "neondatabase",
}


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def load_meta(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def repo_parts(s: dict) -> tuple[str, str, str]:
    m = re.match(r"https?://github\.com/([^/]+)/([^/#?]+)(?:/tree/[^/]+/(.+))?", (s.get("repo_url") or "").rstrip("/"))
    if not m:
        return "", "", ""
    return m.group(1), m.group(2).removesuffix(".git"), (m.group(3) or "").strip("/")


def is_official(s: dict) -> bool:
    return repo_parts(s)[0].lower() in OFFICIAL_OWNERS


def skill_md_url(s: dict) -> str:
    owner, repo, sub = repo_parts(s)
    m = s.get("meta") or {}
    path = m.get("skill_md_path") or sub
    return f"https://github.com/{owner}/{repo}/blob/HEAD/{path + '/' if path else ''}SKILL.md"


def skills_cli_cmd(s: dict) -> str:
    m = s.get("meta") or {}
    if not m.get("skill_md"):
        return ""
    owner, repo, sub = repo_parts(s)
    path = sub
    name = (m["skill_md"].get("name") or (path.rsplit("/", 1)[-1] if path else "")).strip()
    if path and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", name or ""):
        return f"npx skills add {owner}/{repo} --skill {name}"
    return f"npx skills add {owner}/{repo}"


def marketplace_cmd(s: dict) -> str:
    owner, repo, _ = repo_parts(s)
    return f"/plugin marketplace add {owner}/{repo}" if (s.get("meta") or {}).get("has_marketplace") else ""


COPY_BTN = ('<button type="button" data-cmd="{cmd}" style="font-size:12px;padding:4px 10px;border-radius:6px;'
            'border:1px solid rgba(127,127,127,.45);background:transparent;color:inherit;cursor:pointer">Copy</button>')


def _inst(title: str, cmd: str, note: str = "") -> str:
    return (f'<div class="inst"><div class="inst-h"><strong>{title}</strong> {COPY_BTN.format(cmd=esc(cmd))}</div>'
            f"<pre><code>{esc(cmd)}</code></pre>{note}</div>")


def install_html(s: dict, git_cmd: str) -> str:
    out = [_inst("Claude Code — copy the folder", git_cmd,
                 "<p>Claude Code picks up new skills automatically (run <code>/reload-skills</code> if your "
                 "skills folder is brand new). Codex CLI: copy the same folder to "
                 f"<code>~/.codex/skills/{esc(s['slug'])}</code>.</p>")]
    cli = skills_cli_cmd(s)
    if cli:
        out.append(_inst("Any agent — skills CLI", cli,
                         "<p>The open-source <code>skills</code> CLI asks which agents to install for "
                         "(Claude Code, Cursor, Codex, Gemini CLI and others) and links the skill into each one.</p>"))
    mk = marketplace_cmd(s)
    if mk:
        out.append(_inst("Claude Code plugin marketplace", mk,
                         "<p>This repo ships a <code>.claude-plugin/</code> marketplace. After adding it, run "
                         "<code>/plugin</code> in Claude Code to pick what to install.</p>"))
    return "\n".join(out)


def glance_html(s: dict) -> str:
    m = s.get("meta") or {}
    chips = []
    if is_official(s):
        chips.append('<span class="chip" style="background:#16351f;color:#86efac">✓ Official publisher</span>')
    if m.get("archived"):
        chips.append('<span class="chip" style="background:#3b1d1d;color:#fca5a5">Archived repo</span>')
    if m.get("license"):
        chips.append(f'<span class="chip">License: {esc(m["license"])}</span>')
    if m.get("pushed_at"):
        chips.append(f'<span class="chip">Last commit {esc(m["pushed_at"])}</span>')
    if "has_scripts" in m:
        chips.append('<span class="chip">Includes scripts</span>' if m["has_scripts"]
                     else '<span class="chip">Instructions only</span>')
    if m.get("skill_count", 0) > 1:
        chips.append(f'<span class="chip">Collection of {m["skill_count"]} skills</span>')
    if m.get("has_marketplace"):
        chips.append('<span class="chip">Plugin marketplace</span>')
    return f'<div class="meta" style="display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 4px">{"".join(chips)}</div>' if chips else ""


def trigger_desc(s: dict) -> str:
    return ((s.get("meta") or {}).get("skill_md") or {}).get("description", "")


def skillmd_html(s: dict) -> str:
    md = (s.get("meta") or {}).get("skill_md")
    if not md:
        return ""
    m = s["meta"]
    rows = []
    if md.get("name"):
        rows.append(f"<li><code>name</code>: {esc(md['name'])}</li>")
    extra = [k for k in md.get("keys", []) if k not in ("name", "description")]
    if extra:
        rows.append("<li>Other frontmatter fields: " + ", ".join(f"<code>{esc(k)}</code>" for k in extra) + "</li>")
    rows.append(f"<li>Length: about {int(md.get('lines') or 0):,} lines"
                + (" (over the 500-line guideline)" if (md.get("lines") or 0) > 500 else "") + "</li>")
    if m.get("skill_count", 0) > 1:
        rows.append(f"<li>The repo holds {m['skill_count']} skill folders; the preview shows "
                    f"<code>{esc(m.get('skill_md_path', ''))}</code>.</li>")
    outline = ""
    if md.get("outline"):
        outline = ("<p style='margin-top:12px'><strong>Sections:</strong> "
                   + " · ".join(esc(h) for h in md["outline"]) + "</p>")
    excerpt = ""
    if md.get("excerpt"):
        excerpt = (f"<details style='margin-top:10px'><summary style='cursor:pointer'>Preview the start of SKILL.md</summary>"
                   f"<pre style='white-space:pre-wrap'><code>{esc(md['excerpt'])}</code></pre></details>")
    return (f'<div class="section-h">Inside SKILL.md</div>\n<ul>{"".join(rows)}</ul>{outline}{excerpt}'
            f'<p style="margin-top:10px"><a href="{esc(skill_md_url(s))}" rel="noopener">Read the full SKILL.md on GitHub →</a></p>')


def triggers_html(s: dict, fallback: str) -> str:
    d = trigger_desc(s)
    if not d:
        return fallback
    return ("<p>Claude decides when to load a skill from its <code>description</code>. This one says:</p>"
            f"<blockquote style='border-left:3px solid var(--accent);padding:6px 14px;margin:10px 0;color:var(--fg)'>{esc(d)}</blockquote>"
            + (fallback if "<ul>" in fallback else ""))


def sidebar_rows(s: dict) -> str:
    m = s.get("meta") or {}
    out = ""
    if m.get("license"):
        out += f'<div class="row"><span>License</span><span>{esc(m["license"])}</span></div>'
    if m.get("pushed_at"):
        out += f'<div class="row"><span>Last commit</span><span>{esc(m["pushed_at"])}</span></div>'
    return out


# ---------- badge ----------

BADGE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="142" height="20" role="img" aria-label="SkillNest: listed">
<title>SkillNest: listed</title>
<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
<clipPath id="r"><rect width="142" height="20" rx="3" fill="#fff"/></clipPath>
<g clip-path="url(#r)"><rect width="83" height="20" fill="#1e1e2a"/><rect x="83" width="59" height="20" fill="#7c5cff"/><rect width="142" height="20" fill="url(#s)"/></g>
<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
<text x="42.5" y="14">⬢ SkillNest</text><text x="111.5" y="14">listed</text></g>
</svg>
"""


def badge_md(site_url: str, slug: str) -> str:
    return f"[![Listed on SkillNest]({site_url}/badge.svg)]({site_url}/skills/{slug}/)"


def badge_box(s: dict, site_url: str) -> str:
    """Ready-to-copy README badge snippet with the skill's slug pre-filled.

    Shown on every skill page so the author can grab their own embed code in one
    click, instead of hand-editing a placeholder slug on a separate page.
    """
    slug = s["slug"]
    skill_url = f"{site_url}/skills/{slug}/"
    badge_src = f"{site_url}/badge.svg"
    md = f"[![Listed on SkillNest]({badge_src})]({skill_url})"
    html_snip = (
        f'<a href="{skill_url}">'
        f'<img src="{badge_src}" alt="Listed on SkillNest" width="142" height="20">'
        '</a>'
    )
    md_disp = md.replace("<", "&lt;").replace(">", "&gt;")
    html_disp = html_snip.replace("<", "&lt;").replace(">", "&gt;")
    return (
        '<div class="section-h">Maintain this skill?</div>\n'
        '<div class="badge-box">\n'
        f'  <p>Add this badge to your README — it links back to <a href="{skill_url}">your SkillNest page</a>, so visitors of your repo can grab the install command and see related skills.</p>\n'
        f'  <p><img src="{badge_src}" alt="Listed on SkillNest" width="142" height="20" style="vertical-align:middle"></p>\n'
        '  <div class="snippet"><label>Markdown (GitHub README)</label>\n'
        f'    <pre><code>{md_disp}</code></pre>\n'
        '    <button type="button" class="copy-btn">Copy</button>\n'
        '  </div>\n'
        '  <div class="snippet"><label>HTML</label>\n'
        f'    <pre><code>{html_disp}</code></pre>\n'
        '    <button type="button" class="copy-btn">Copy</button>\n'
        '  </div>\n'
        '  <p class="muted"><a href="/badge/">More badge options →</a></p>\n'
        '</div>\n'
        '<script>document.querySelectorAll(".badge-box .copy-btn").forEach(function(b){b.addEventListener("click",function(){var c=b.closest(".snippet").querySelector("code");navigator.clipboard.writeText(c.textContent).then(function(){var o=b.textContent;b.textContent="Copied!";setTimeout(function(){b.textContent=o;},1500);});});});</script>'
    )

def render_badge_page(layout, site_url: str, site_name: str) -> str:
    md = badge_md(site_url, "YOUR-SKILL-SLUG")
    htm = f'<a href="{site_url}/skills/YOUR-SKILL-SLUG/"><img src="{site_url}/badge.svg" alt="Listed on SkillNest" width="142" height="20"></a>'
    body = f"""<div class="wrap" style="max-width:820px">
<section class="hero" style="padding:50px 0 20px">
<h1>Add a SkillNest badge to your skill</h1>
<p>Is your Claude Code skill listed on {esc(site_name)}? Show it in your README so people can find the install command, alternatives and related skills.</p>
</section>
<p><img src="/badge.svg" alt="Listed on SkillNest" width="142" height="20"></p>
<h2 style="margin-top:30px">Markdown (GitHub README)</h2>
<p>Replace <code>YOUR-SKILL-SLUG</code> with the last part of your skill's URL here, for example <code>{site_url}/skills/<strong>my-skill</strong>/</code>. Every skill page also shows its own ready-made snippet near the bottom.</p>
<pre style="white-space:pre-wrap"><code>{esc(md)}</code></pre>{COPY_BTN.format(cmd=esc(md))}
<h2 style="margin-top:30px">HTML</h2>
<pre style="white-space:pre-wrap"><code>{esc(htm)}</code></pre>{COPY_BTN.format(cmd=esc(htm))}
<h2 style="margin-top:30px">Not listed yet?</h2>
<p>The index rescans GitHub every week. To be picked up, put a <code>SKILL.md</code> in your repo and add the <code>claude-code-skill</code> or <code>agent-skills</code> topic, or <a href="/submit/">submit it</a>. Check your file first with the <a href="/tools/skill-md-validator/">SKILL.md validator</a>.</p>
</div>"""
    return layout(title=f"SkillNest README Badge for Claude Code Skill Authors — {site_name}",
                  description="Copy a 'Listed on SkillNest' badge for your Claude Code skill's README, in Markdown or HTML.",
                  body=body, canonical="/badge/")


# ---------- API + feeds ----------

def api_json(skills: list[dict], site_url: str, install_cmd) -> str:
    out = []
    for s in skills:
        m = s.get("meta") or {}
        out.append({
            "slug": s["slug"], "name": s["name"], "author": s.get("author"),
            "url": f"{site_url}/skills/{s['slug']}/", "repo_url": s.get("repo_url"),
            "category": s.get("category"), "tags": s.get("tags") or [],
            "description": s.get("short_description", ""), "trigger_description": trigger_desc(s),
            "stars": s.get("stars") or 0, "license": m.get("license") or None,
            "last_commit": m.get("pushed_at") or None, "official": is_official(s),
            "includes_scripts": m.get("has_scripts"),
            "install": {"claude_code": install_cmd(s), "skills_cli": skills_cli_cmd(s) or None,
                        "plugin_marketplace": marketplace_cmd(s) or None},
        })
    doc = {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "count": len(out), "license_note": "Facts about public GitHub repos; each skill keeps its own license.",
           "skills": out}
    return json.dumps(doc, ensure_ascii=False, indent=1)


def new_feed(items: list[dict], site_url: str, site_name: str) -> str:
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    rows = []
    for s in items[:50]:
        d = (s.get("added_at") or "")[:10]
        try:
            pub = datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 GMT")
        except ValueError:
            pub = now
        rows.append(f"<item><title>{esc(s['name'])} — by {esc(s.get('author'))}</title>"
                    f"<link>{site_url}/skills/{esc(s['slug'])}/</link><guid>{site_url}/skills/{esc(s['slug'])}/</guid>"
                    f"<pubDate>{pub}</pubDate><description>{esc(s.get('short_description', ''))}</description></item>")
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>New Claude Code skills — {esc(site_name)}</title><link>{site_url}/new/</link>"
            f"<description>Claude Code skills newly found on GitHub, updated weekly.</description>"
            f"<lastBuildDate>{now}</lastBuildDate>{''.join(rows)}</channel></rss>\n")


def llms_extra(site_url: str) -> list[str]:
    return ["", "## Tools and data",
            f"- [SKILL.md validator]({site_url}/tools/skill-md-validator/): check frontmatter and naming in the browser",
            f"- [Public API]({site_url}/api/v1/skills.json): every skill with install commands, license, last commit and trigger description",
            f"- [New skills RSS]({site_url}/new/feed.xml): skills added in the weekly GitHub scan",
            f"- [Author badge]({site_url}/badge/): README badge for listed skills"]
