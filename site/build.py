"""Static site generator — pure HTML, zero JS build step.

Reads `../data/skills.json`, writes a complete static site into `dist/`:
- index.html          — homepage with featured + browse
- skills/<slug>/      — detail page per skill
- category/<cat>/     — category index
- tag/<tag>/          — tag index
- compare/<a>-vs-<b>/ — pSEO compare pages (top N)
- sitemap.xml         — all URLs
- robots.txt          — crawl rules
- rss.xml             — feed
- data/skills.json    — mirrored for public API use

Run: `python build.py`
"""
from __future__ import annotations

import html
from collections import Counter
import itertools
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
PROJECT = ROOT.parent
DATA = PROJECT / "data" / "skills.json"
OUT = ROOT / "dist"
MIN_TAG_INDEX = 3  # tags with fewer skills get noindex + stay out of sitemap

SITE_NAME = os.environ.get("SITE_NAME", "SkillNest")
SITE_URL = os.environ.get("SITE_URL", "https://skillnest.dev").rstrip("/")
SITE_TAGLINE = "The directory for Claude Code skills, plugins, and agents"

# Search engine verification tokens (safe to be public — they only prove ownership)
GOOGLE_VERIFY = os.environ.get("GOOGLE_VERIFY", "_tu33hAptmiDtcn1xUiAldSyNKXh0X5iY3rWDHwvHEc")
BING_VERIFY = os.environ.get("BING_VERIFY", "")
YANDEX_VERIFY = os.environ.get("YANDEX_VERIFY", "")

# Monetization — Gumroad pack (sponsored CTA across the site)
GUMROAD_URL = os.environ.get("GUMROAD_URL", "https://daillyteen.gumroad.com/l/wapct")
GUMROAD_TITLE = "Claude Code Skills Pack"
GUMROAD_PRICE = "$19"
GUMROAD_PITCH = "6 ready-to-use Claude Code skills for tests, commits, PR write-ups, docstrings, .env files and Dockerfiles. One-time buy, free updates through Nov 2027."


def gumroad_url(placement: str) -> str:
    """Append UTM params for attribution."""
    sep = "&" if "?" in GUMROAD_URL else "?"
    return f"{GUMROAD_URL}{sep}utm_source=skillnest&utm_medium=directory&utm_campaign={placement}"
SITE_DESC = (
    "Discover 100+ open-source skills, plugins, and agents for Claude Code. "
    "Browse by category — document processing, charts, research, automation, security. "
    "Install any skill in one command."
)

CSS = """
:root{--bg:#0a0a0f;--fg:#e8eaed;--muted:#9aa0a6;--accent:#a78bfa;--card:#14141c;--border:#22222e;--chip:#1e1e2a}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--fg)}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
nav{background:#0a0a0f;border-bottom:1px solid var(--border);padding:16px 0;position:sticky;top:0;z-index:10;backdrop-filter:blur(8px)}
nav .wrap{display:flex;gap:22px;align-items:center}
nav .brand{font-weight:800;color:#fff;font-size:17px}
nav a{color:var(--muted);font-weight:500}
nav a:hover{color:#fff;text-decoration:none}
nav .spacer{flex:1}
.hero{padding:80px 0 50px}
.hero h1{font-size:clamp(32px,5vw,56px);line-height:1.08;letter-spacing:-.02em;font-weight:800;color:#fff;margin-bottom:18px}
.hero h1 span{background:linear-gradient(135deg,#7dd3fc,#a78bfa,#f472b6);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{font-size:18px;color:var(--muted);max-width:640px;margin-bottom:28px}
.hero .stats{display:flex;gap:28px;color:var(--muted);font-size:14px;flex-wrap:wrap}
.hero .stats b{color:#fff;font-size:22px;display:block}
.search{margin:24px 0 0;display:flex;gap:10px}
.search input{flex:1;background:var(--card);border:1px solid var(--border);color:var(--fg);padding:14px 16px;border-radius:10px;font-size:15px}
.search input:focus{outline:none;border-color:var(--accent)}
section{padding:40px 0}
h2{font-size:28px;font-weight:700;color:#fff;margin-bottom:20px;letter-spacing:-.01em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--accent);transform:translateY(-2px)}
.card h3{font-size:17px;color:#fff;margin-bottom:6px;font-weight:600}
.card h3 a{color:inherit}
.card h3 a:hover{color:var(--accent);text-decoration:none}
.card p{color:var(--muted);font-size:14px;margin-bottom:12px;min-height:40px}
.card .meta{display:flex;gap:12px;font-size:12px;color:var(--muted);align-items:center;flex-wrap:wrap}
.chip{display:inline-block;padding:3px 10px;background:var(--chip);border-radius:20px;font-size:12px;color:var(--muted)}
.chip.featured{background:#3a2c56;color:#c8b3ff}
.breadcrumb{color:var(--muted);font-size:13px;margin-bottom:16px}
.breadcrumb a{color:var(--muted)}
.breadcrumb a:hover{color:var(--accent);text-decoration:none}
.detail{display:grid;grid-template-columns:1fr 280px;gap:40px;padding:40px 0}
@media(max-width:800px){.detail{grid-template-columns:1fr}}
.detail h1{font-size:40px;color:#fff;margin-bottom:10px;letter-spacing:-.02em}
.detail .short{font-size:18px;color:var(--muted);margin-bottom:28px}
.detail .long{font-size:16px;color:var(--fg);line-height:1.7;margin-bottom:28px}
.detail .section-h{font-size:14px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin:28px 0 10px;font-weight:600}
.detail code{background:var(--card);padding:2px 6px;border-radius:4px;font-size:14px;color:#f472b6}
.detail pre{background:var(--card);padding:16px;border-radius:8px;overflow-x:auto;border:1px solid var(--border);margin:8px 0}
.detail pre code{background:none;padding:0;color:var(--fg)}
.sidebar{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;height:fit-content;position:sticky;top:80px}
.sidebar .row{display:flex;justify-content:space-between;padding:8px 0;font-size:14px;border-bottom:1px solid var(--border)}
.sidebar .row:last-child{border-bottom:none}
.sidebar .row span:first-child{color:var(--muted)}
.sidebar .row span:last-child{color:#fff;font-weight:500}
.sidebar .cta{display:block;background:#fff;color:#000;padding:12px 16px;border-radius:8px;font-weight:600;margin-top:16px;text-align:center;font-size:14px}
.sidebar .cta:hover{background:#eee;text-decoration:none}
.related{margin-top:48px}
footer{border-top:1px solid var(--border);padding:40px 0;color:var(--muted);font-size:14px;margin-top:60px}
footer .wrap{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}
.tag-cloud{display:flex;flex-wrap:wrap;gap:8px}
.tag-cloud a{display:inline-block;padding:6px 12px;background:var(--card);border:1px solid var(--border);border-radius:20px;font-size:13px;color:var(--muted)}
.tag-cloud a:hover{color:#fff;border-color:var(--accent);text-decoration:none;background:var(--chip)}
.promo{background:linear-gradient(135deg,#1e1033,#2a1a4a);border:1px solid #4a2e7a;border-radius:14px;padding:28px;margin:28px 0;display:flex;align-items:center;gap:24px;flex-wrap:wrap}
.promo .body{flex:1;min-width:260px}
.promo .tag{display:inline-block;padding:3px 10px;background:#4a2e7a;color:#d6c3ff;border-radius:20px;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;margin-bottom:10px}
.promo h3{font-size:20px;color:#fff;margin-bottom:6px;font-weight:700}
.promo p{color:#b8a8d8;font-size:14px;margin:0}
.promo .btn{display:inline-block;background:#fff;color:#000;padding:12px 24px;border-radius:10px;font-weight:700;white-space:nowrap}
.promo .btn:hover{background:#eee;text-decoration:none}
.promo .btn b{color:#000;margin-left:6px}
.promo.compact{padding:18px;margin:16px 0;flex-direction:column;align-items:flex-start;text-align:left}
.promo.compact .btn{width:100%;text-align:center;margin-top:12px}
"""


def esc(s: str | None) -> str:
    return html.escape(s or "", quote=True)


def layout(title: str, description: str, body: str, canonical: str, extra_head: str = "") -> str:
    desc = esc(description[:160])
    canon = f"{SITE_URL}{canonical}"
    year = datetime.now().year
    verify_tags = []
    if GOOGLE_VERIFY:
        verify_tags.append(f'<meta name="google-site-verification" content="{esc(GOOGLE_VERIFY)}">')
    if BING_VERIFY:
        verify_tags.append(f'<meta name="msvalidate.01" content="{esc(BING_VERIFY)}">')
    if YANDEX_VERIFY:
        verify_tags.append(f'<meta name="yandex-verification" content="{esc(YANDEX_VERIFY)}">')
    verify_html = "\n".join(verify_tags)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="index,follow,max-image-preview:large">
{verify_html}
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary_large_image">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta name="twitter:image" content="{SITE_URL}/og.png">
<meta name="theme-color" content="#0a0a0f">
<link rel="icon" type="image/svg+xml" href='data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="%23a78bfa"/><text x="32" y="44" font-family="sans-serif" font-size="32" font-weight="800" fill="white" text-anchor="middle">C</text></svg>'>
<style>{CSS}</style>
{extra_head}
</head>
<body>
<nav><div class="wrap">
<a class="brand" href="/">⬢ {SITE_NAME}</a>
<a href="/">Browse</a>
<a href="/category/development/">Categories</a>
<a href="/best/">Best skills</a>
<a href="/blog/">Blog</a>
<a href="/submit/">Submit a skill</a>
<div class="spacer"></div>
<a href="https://github.com/anthropics/skills" rel="noopener">GitHub</a>
</div></nav>
{body}
<footer><div class="wrap">
<div>© {year} {SITE_NAME} · Community directory, not affiliated with Anthropic</div>
<div><a href="/sitemap.xml">Sitemap</a> · <a href="/rss.xml">RSS</a></div>
</div></footer>
</body>
</html>
"""


def skill_card(s: dict) -> str:
    featured = '<span class="chip featured">★ Featured</span>' if s.get("featured") else ""
    return f"""<article class="card">
<h3><a href="/skills/{esc(s['slug'])}/">{esc(s['name'])}</a></h3>
<p>{esc(s.get('short_description', ''))}</p>
<div class="meta">
  <span class="chip">{esc(s.get('category', 'other'))}</span>
  <span>{s.get('stars', 0)}★</span>
  <span>by {esc(s['author'])}</span>
  {featured}
</div>
</article>"""


def jsonld_software_app(s: dict) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": s["name"],
        "description": s.get("long_description") or s.get("short_description", ""),
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Cross-platform",
        "author": {"@type": "Person", "name": s["author"], "url": s.get("author_url")},
        "offers": {"@type": "Offer", "price": "0" if s.get("price") == "free" else "0", "priceCurrency": "USD"},
    }
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def promo_block_full() -> str:
    return f"""<a class="promo" href="{esc(gumroad_url('home'))}" target="_blank" rel="noopener sponsored" style="text-decoration:none">
<div class="body">
<span class="tag">Sponsored</span>
<h3>{esc(GUMROAD_TITLE)} — {esc(GUMROAD_PRICE)}</h3>
<p>{esc(GUMROAD_PITCH)}</p>
</div>
<span class="btn">Get the pack<b>→</b></span>
</a>"""


def promo_block_compact() -> str:
    return f"""<a class="promo compact" href="{esc(gumroad_url('skill-sidebar'))}" target="_blank" rel="noopener sponsored" style="text-decoration:none">
<span class="tag">Sponsored</span>
<h3 style="font-size:16px">Need the full pack?</h3>
<p>6 dev skills that auto-trigger in Claude Code. {esc(GUMROAD_PRICE)}.</p>
<span class="btn">View on Gumroad →</span>
</a>"""


def render_home(skills: list[dict]) -> str:
    featured = [s for s in skills if s.get("featured")][:6]
    all_skills = sorted(skills, key=lambda x: -(x.get("stars") or 0))[:30]
    categories = sorted({s.get("category", "other") for s in skills})
    tags = sorted({t for s in skills for t in (s.get("tags") or [])})

    featured_html = "\n".join(skill_card(s) for s in featured)
    all_html = "\n".join(skill_card(s) for s in all_skills)
    cats_html = " ".join(
        f'<a href="/category/{esc(c)}/">{esc(c.replace("-", " ").title())}</a>'
        for c in categories
    )
    tags_html = " ".join(f'<a href="/tag/{esc(t)}/">{esc(t)}</a>' for t in [t for t, _n in Counter(t for s in skills for t in (s.get("tags") or [])).most_common(40)])

    body = f"""<div class="wrap">
<section class="hero">
<h1>Every Claude Code skill,<br><span>one search away.</span></h1>
<p>{esc(SITE_DESC)}</p>
<div class="stats">
<div><b>{len(skills)}</b>skills indexed</div>
<div><b>{len(categories)}</b>categories</div>
<div><b>{len(tags)}</b>tags</div>
</div>
{SEARCH_HTML}
{promo_block_full()}
</section>

<section>
<h2>Featured</h2>
<div class="grid">{featured_html}</div>
</section>

<section>
<h2>From the blog</h2>
<div class="tag-cloud">{blog_cloud()}</div>
</section>

<section>
<h2>Guides</h2>
<div class="tag-cloud">{guides_cloud(skills)}</div>
</section>

<section>
<h2>Categories</h2>
<div class="tag-cloud">{cats_html}</div>
</section>

<section>
<h2>Top 30 skills <span style="font-size:15px;color:var(--muted);font-weight:400">of {len(skills)} — browse the categories above for the rest</span></h2>
<div class="grid">{all_html}</div>
</section>

<section>
<h2>Popular tags</h2>
<div class="tag-cloud">{tags_html}</div>
</section>
</div>"""
    return layout(
        title=f"{SITE_NAME} — {SITE_TAGLINE}",
        description=SITE_DESC,
        body=body,
        canonical="/",
        extra_head=website_jsonld(),
    )


def render_skill(s: dict, all_skills: list[dict]) -> str:
    related = [
        x for x in sorted(all_skills, key=lambda y: -(y.get("stars") or 0))
        if x["slug"] != s["slug"] and x.get("category") == s.get("category")
    ][:3]
    related_html = "\n".join(skill_card(r) for r in related) or "<p>No related skills.</p>"

    triggers = s.get("triggers") or []
    triggers_html = (
        "<ul>" + "".join(f"<li><code>{esc(t)}</code></li>" for t in triggers) + "</ul>"
        if triggers else "<p>No specific triggers listed.</p>"
    )

    cmd = install_cmd(s)
    install_block = (
        f"<pre><code>{esc(cmd)}</code></pre>\n"
        f'<p>Claude Code picks up new skills automatically (run <code>/reload-skills</code> if your skills folder is brand new). See the <a href="{esc(s.get("repo_url", "#"))}" rel="noopener">README</a> for skill-specific setup.</p>'
        f'<p>Using Codex CLI? Copy the same folder to <code>~/.codex/skills/{esc(s["slug"])}</code> instead.</p>'
        "<p>On Windows? Follow the <a href='/blog/install-claude-code-skills-windows/'>Windows install guide</a>. New to skills? Read the <a href='/blog/claude-code-skills-beginners-guide/'>beginner's guide</a> or <a href='/blog/claude-code-skills-vs-mcp-servers/'>Claude Code skills vs MCP servers</a>.</p>"
    )
    faq, faq_jsonld = faq_block(s, cmd)

    jsonld = jsonld_software_app(s) + faq_jsonld + breadcrumb_jsonld(s)
    body = f"""<div class="wrap">
<div class="detail">
<main>
<div class="breadcrumb">
<a href="/">Home</a> › <a href="/category/{esc(s.get('category', 'other'))}/">{esc(s.get('category', 'other').replace('-', ' ').title())}</a> › {esc(s['name'])}
</div>
<h1>{esc(s['name'])}</h1>
<p class="short">{esc(s.get('short_description', ''))}</p>

<p class="long">{esc(s.get('long_description', ''))}</p>

<div class="section-h">Install</div>
{install_block}

<div class="section-h">When it triggers</div>
{triggers_html}

<div class="section-h">Tags</div>
<div class="tag-cloud">
{''.join(f'<a href="/tag/{esc(t)}/">{esc(t)}</a>' for t in (s.get('tags') or []))}
</div>

{faq}

<div class="related">
<h2>Related skills</h2>
<div class="grid">{related_html}</div>
</div>
</main>

<aside class="sidebar">
<div class="row"><span>Author</span><span><a href="{esc(s.get('author_url', '#'))}">{esc(s['author'])}</a></span></div>
<div class="row"><span>Category</span><span>{esc(s.get('category', 'other'))}</span></div>
<div class="row"><span>Difficulty</span><span>{esc(s.get('difficulty', 'beginner'))}</span></div>
<div class="row"><span>Price</span><span>{esc(s.get('price', 'free'))}</span></div>
<div class="row"><span>Stars</span><span>{s.get('stars', 0)}</span></div>
<div class="row"><span>Updated</span><span>{esc(s.get('updated_at', ''))}</span></div>
<a class="cta" href="{esc(s.get('repo_url', '#'))}" rel="noopener">View on GitHub →</a>
{sidebar_promo(s)}
</aside>
</div>
</div>"""
    return layout(
        title=f"{s['name']} — Claude Code Skill: Install & Usage",
        description=f"{s.get('short_description', '').rstrip('.')}. Install command, FAQ and alternatives. {s.get('stars', 0)}★ on GitHub.",
        body=body,
        canonical=f"/skills/{s['slug']}/",
        extra_head=jsonld,
    )


def render_listing(title: str, description: str, skills: list[dict], canonical: str) -> str:
    cards = "\n".join(skill_card(s) for s in sorted(skills, key=lambda x: -(x.get("stars") or 0))) or "<p>No skills in this group yet.</p>"
    body = f"""<div class="wrap">
<section class="hero" style="padding:50px 0 30px">
<h1>{esc(title)}</h1>
<p>{esc(description)}</p>
</section>
<section>
<div class="grid">{cards}</div>
</section>
</div>"""
    ranked = sorted(skills, key=lambda x: -(x.get("stars") or 0))[:50]
    item_list = {
        "@context": "https://schema.org", "@type": "ItemList", "name": title,
        "numberOfItems": len(skills),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": f"{SITE_URL}/skills/{x['slug']}/", "name": x.get("name") or x["slug"]}
            for i, x in enumerate(ranked)
        ],
    }
    extra = '<script type="application/ld+json">' + json.dumps(item_list, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    return layout(title=f"{title} — {SITE_NAME}", description=description, body=body, canonical=canonical, extra_head=extra)


def render_compare(a: dict, b: dict) -> str:
    def row(label: str, va, vb) -> str:
        return (f"<tr><td>{esc(label)}</td>"
                f"<td>{esc(str(va))}</td><td>{esc(str(vb))}</td></tr>")
    body = f"""<div class="wrap">
<div class="breadcrumb"><a href="/">Home</a> › Compare</div>
<section class="hero" style="padding:40px 0 20px">
<h1>{esc(a['name'])} vs {esc(b['name'])}</h1>
<p>Side-by-side comparison of two Claude Code skills. Which fits your workflow?</p>
</section>
<section>
<table style="width:100%;border-collapse:collapse" cellpadding="10">
<thead><tr style="border-bottom:1px solid var(--border)">
<th align="left" style="color:var(--muted);font-weight:500">Field</th>
<th align="left" style="color:#fff">{esc(a['name'])}</th>
<th align="left" style="color:#fff">{esc(b['name'])}</th>
</tr></thead>
<tbody>
{row("Category", a.get("category"), b.get("category"))}
{row("Author", a["author"], b["author"])}
{row("Price", a.get("price"), b.get("price"))}
{row("Difficulty", a.get("difficulty"), b.get("difficulty"))}
{row("Stars", a.get("stars", 0), b.get("stars", 0))}
{row("Short description", a.get("short_description", ""), b.get("short_description", ""))}
</tbody></table>
</section>
<section>
<div class="grid">
{skill_card(a)}
{skill_card(b)}
</div>
</section>
</div>"""
    return layout(
        title=f"{a['name']} vs {b['name']} — {SITE_NAME}",
        description=f"Compare {a['name']} and {b['name']} as Claude Code skills — features, price, difficulty.",
        body=body,
        canonical=f"/compare/{a['slug']}-vs-{b['slug']}/",
    )


def render_submit() -> str:
    body = """<div class="wrap">
<section class="hero">
<h1>Submit a skill</h1>
<p>Built a Claude Code skill? Open a PR on our GitHub repo or email <code>hi@skillnest.dev</code>. Include: name, GitHub URL, short description, category, tags.</p>
</section>
</div>"""
    return layout(
        title=f"Submit a skill — {SITE_NAME}",
        description="Submit your Claude Code skill, plugin, or agent to the directory.",
        body=body,
        canonical="/submit/",
    )


def write_file(rel: str, content: str) -> None:
    p = OUT / rel.lstrip("/")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def write_sitemap(urls: list[str], lastmods: dict | None = None) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    items = "\n".join(
        f"<url><loc>{SITE_URL}{u}</loc><lastmod>{(lastmods or {}).get(u) or now}</lastmod></url>"
        for u in urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>"""
    write_file("sitemap.xml", xml)


def write_robots() -> None:
    txt = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    write_file("robots.txt", txt)


def write_rss(skills: list[dict]) -> None:
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    items = []
    for s in skills[:50]:
        items.append(f"""<item>
<title>{esc(s['name'])}</title>
<link>{SITE_URL}/skills/{esc(s['slug'])}/</link>
<guid>{SITE_URL}/skills/{esc(s['slug'])}/</guid>
<description>{esc(s.get('short_description', ''))}</description>
</item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>{SITE_NAME}</title>
<link>{SITE_URL}</link>
<description>{SITE_TAGLINE}</description>
<lastBuildDate>{now}</lastBuildDate>
{''.join(items)}
</channel>
</rss>"""
    write_file("rss.xml", rss)


CF_HEADERS = """# Cloudflare Pages custom headers
/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: geolocation=(), microphone=(), camera=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

/*.html
  Cache-Control: public, max-age=300, s-maxage=3600

/*.xml
  Cache-Control: public, max-age=3600, s-maxage=86400

/data/*
  Cache-Control: public, max-age=3600
  Access-Control-Allow-Origin: *
"""

CF_REDIRECTS = """# Cloudflare Pages redirects
/*    /404.html    404
"""

NOT_FOUND = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>404 — """ + SITE_NAME + """</title><meta name="robots" content="noindex">
<style>body{font:16px/1.5 ui-sans-serif,system-ui,sans-serif;background:#0a0a0f;color:#e8eaed;min-height:100vh;display:flex;align-items:center;justify-content:center;margin:0;text-align:center;padding:20px}.b{max-width:420px}h1{font-size:56px;color:#a78bfa;margin:0 0 10px}h2{color:#fff;font-weight:600;margin:0 0 16px;font-size:20px}p{color:#9aa0a6;margin:0 0 24px}a{color:#a78bfa;text-decoration:none;font-weight:600;border:1px solid #a78bfa;padding:10px 20px;border-radius:8px;display:inline-block}a:hover{background:#a78bfa;color:#000}</style>
</head><body><div class="b"><h1>404</h1><h2>Skill not found</h2>
<p>This skill may have been removed, renamed, or never existed.</p>
<a href="/">← Browse all skills</a></div></body></html>"""


# --- Data cleanup at build time (scraper output stays untouched) ---------------
import re as _re

FAKE_SEEDS = {"claude-api", "code-review", "dataviz", "deep-research", "docs",
              "google-workspace", "loop", "plugin-authoring", "schedule"}
LEAKED = {"claude-code", "free-claude-code", "system-prompts-leaks"}
# Curated lists, tutorials and templates: useful repos, but not installable skills.
NON_SKILL_RX = _re.compile(
    r"github\.com/[^/]+/awesome[-_]|github\.com/f/prompts\.chat|github\.com/shareAI-lab/learn-claude-code"
    r"|github\.com/anthropics/skills/tree/main/(spec|template)/?$",
    _re.I,
)
SEED_URLS = {s: f"https://github.com/anthropics/skills/tree/main/skills/{s}"
             for s in ("docx", "pdf", "pptx", "xlsx", "skill-creator")}
SEED_URLS["security-review"] = "https://github.com/anthropics/claude-code-security-review"
SKILL_RX = _re.compile(r"claude|skill|\bmcp\b|anthropic|codex|agent", _re.I)
CATEGORY_OVERRIDES = {slug: cat for cat, slugs in {
    "game-dev": ["godogen", "godotmaker"],
    "design": ["oil-ui", "motion-dev-animations-skill"],
    "content-creation": ["narrator-ai-cli-skill", "nano-banana-pro-prompts-recommend-skill", "banana-claude",
                         "video-fetcher-to-markdown", "claude-shorts", "humanizer-skill", "html-explainer",
                         "claude-repurpose", "khan-explainer"],
    "business": ["court-skill", "hiring-panel-skill", "hormozi-skills", "on-page-seo",
                 "product-manager-skills", "orangeo-ai-visibility-skill"],
    "meta": ["one-skill-to-rule-them-all", "soul-md", "skillcompass", "attention-control"],
    "development": ["pinme", "chisle", "antivibe", "claude-skill-web-clone", "abide", "ai-agent-team",
                    "claude-code-rails-upgrade-skill", "building-with-typesafe-jev", "dex"],
    "research": ["answer-me-with-html", "llm-council-skill", "grazer-skill"],
    "document-processing": ["ai-doc-gen"],
    "reference": ["claude-code-for-beginners"],
    "integrations": ["application-skills", "vast-cli", "aelf-skills"],
    "automation": ["job-application-agent"],
    "lifestyle": ["qingsheng-skill"],
}.items() for slug in slugs}
CATEGORY_RULES = [(c, _re.compile(p)) for c, p in [
    ("game-dev", r"godot|\bgame|unity|bevy|unreal"),
    ("security", r"security|pentest|vulnerab|audit|\bctf\b"),
    ("design", r"\bui\b|ui-ux|design|figma|tailwind|animation|frontend"),
    ("content-creation", r"video|image|tts|youtube|tiktok|podcast|writing|content|copywrit|humaniz"),
    ("business", r"\bseo\b|marketing|sales|business|\bads\b|resume|\bjob|career|product-manager|startup"),
    ("research", r"research|paper|arxiv|literature|scholar"),
    ("document-processing", r"\bpdf\b|docx|markdown|document|obsidian|notes|excel|pptx"),
    ("charts", r"chart|analytics|\bsql\b|visualiz|dashboard|\bdata\b"),
    ("automation", r"automat|workflow|cron|browser|scrap|crawl"),
    ("integrations", r"\bmcp\b|integration|slack|notion|api\b|telegram|discord"),
    ("meta", r"skill-manag|prompt|memory|context|meta-skill|skills? (hub|collection|library)|awesome"),
    ("development", r"code|coding|dev|refactor|test|git|programming|framework|react|python|rust|typescript"),
]]


def clean_skills(raw: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for s in raw:
        slug = s.get("slug", "")
        if slug in FAKE_SEEDS or slug in LEAKED:
            continue
        if NON_SKILL_RX.search(s.get("repo_url") or ""):
            continue  # curated list / tutorial / template, not a skill
        text = " ".join([s.get("name") or "", slug, s.get("short_description") or "",
                         " ".join(s.get("tags") or [])]).lower()
        if slug in SEED_URLS:
            s["repo_url"] = s["author_url"] = SEED_URLS[slug]
        elif not SKILL_RX.search(text):
            continue  # not a Claude skill (generic awesome-lists etc.)
        if slug in CATEGORY_OVERRIDES:
            s["category"] = CATEGORY_OVERRIDES[slug]
        elif s.get("category", "other") == "other":
            for cat, rx in CATEGORY_RULES:
                if rx.search(text):
                    s["category"] = cat
                    break
        if not s.get("short_description"):
            s["short_description"] = f"{s.get('name', slug)} — a Claude Code skill by {s.get('author', 'unknown')}."
        if slug in ("skills", "claude-skills"):
            m = _re.search(r"github\.com/([^/]+)/([^/#?]+)", s.get("repo_url") or "")
            if m:
                s["slug"] = f"{m.group(1)}-{m.group(2)}".lower()
        if s["slug"] in seen:
            continue
        seen.add(s["slug"])
        s["featured"] = False
        out.append(s)
    claude_tagged = [x for x in out if any("claude" in t for t in (x.get("tags") or []))]
    for s in sorted(claude_tagged, key=lambda x: -(x.get("stars") or 0))[:6]:
        s["featured"] = True
    return out


# --- SEO helpers ---------------------------------------------------------------


def install_cmd(s: dict) -> str:
    slug = s["slug"]
    repo = (s.get("repo_url") or "").rstrip("/")
    base, _, sub = repo.partition("/tree/")
    if sub and "/" in sub:
        path = sub.split("/", 1)[1]
        return (f"git clone --depth 1 {base}.git /tmp/{slug}-src\n"
                f"cp -r /tmp/{slug}-src/{path} ~/.claude/skills/{slug}")
    return f"git clone --depth 1 {repo}.git ~/.claude/skills/{slug}"


def faq_block(s: dict, cmd: str) -> tuple[str, str]:
    name, author = s["name"], s.get("author", "its author")
    cat = s.get("category", "other")
    desc = s.get("long_description") or s.get("short_description") or ""
    stars = s.get("stars") or 0
    qa = [
        (f"What is {name}?", desc or f"{name} is a Claude Code skill by {author}."),
        (f"How do I install {name} in Claude Code?",
         f"Clone it into your personal skills folder: {cmd.replace(chr(10), ' && ')} — Claude Code picks it up automatically."),
        (f"Is {name} free?",
         f"{name} is open source on GitHub ({stars} stars at last check) and published by {author}."),
        (f"What are alternatives to {name}?",
         f"Browse other {cat.replace('-', ' ')} skills in the {cat.replace('-', ' ').title()} category of this directory."),
    ]
    items = "".join(f"<h3 style=\"font-size:16px;color:#fff;margin:18px 0 6px\">{esc(q)}</h3><p>{esc(a)}</p>" for q, a in qa)
    html_block = f'<div class="section-h">FAQ</div>\n<div class="faq">{items}</div>'
    data = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}
    return html_block, f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def compare_pairs(skills: list[dict], per_cat: int = 5, limit: int = 120) -> list[tuple[dict, dict]]:
    by_cat: dict[str, list[dict]] = {}
    for s in skills:
        by_cat.setdefault(s.get("category", "other"), []).append(s)
    pairs: list[tuple[dict, dict]] = []
    for cat, items in sorted(by_cat.items()):
        if cat == "other":
            continue
        top = sorted(items, key=lambda x: -(x.get("stars") or 0))[:per_cat]
        pairs.extend(itertools.combinations(top, 2))
    return pairs[:limit]


# --- SEO round 2 ---------------------------------------------------------------
CAT_TOPIC = {
    "automation": "automating workflows, browsers and recurring tasks",
    "business": "marketing, SEO, sales, hiring and product work",
    "charts": "data analysis, SQL, dashboards and visualization",
    "content-creation": "video, images, writing and social content",
    "design": "UI/UX, frontend design and animation",
    "development": "coding, refactoring, testing and shipping software",
    "document-processing": "PDF, Word, Excel, Markdown and notes",
    "game-dev": "building games with Godot, Unity, Bevy and the web",
    "integrations": "MCP servers, APIs and third-party apps",
    "lifestyle": "everyday life and personal use",
    "meta": "managing prompts, memory, context and other skills",
    "reference": "learning Claude Code and reference material",
    "research": "research, papers and multi-source synthesis",
    "security": "security audits, pentesting and code review",
}


def by_stars(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda x: -(x.get("stars") or 0))


def category_desc(cat: str, items: list[dict]) -> str:
    top = ", ".join(s["name"] for s in by_stars(items)[:3])
    topic = CAT_TOPIC.get(cat, cat.replace("-", " "))
    return (f"{len(items)} open-source Claude Code skills for {topic}, ranked by GitHub stars "
            f"with one-line install commands. Top picks: {top}.")


def breadcrumb_jsonld(s: dict) -> str:
    cat = s.get("category", "other")
    data = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
        {"@type": "ListItem", "position": 2, "name": cat.replace("-", " ").title(), "item": f"{SITE_URL}/category/{cat}/"},
        {"@type": "ListItem", "position": 3, "name": s["name"], "item": f"{SITE_URL}/skills/{s['slug']}/"},
    ]}
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


def website_jsonld() -> str:
    data = {"@context": "https://schema.org", "@type": "WebSite", "name": SITE_NAME, "url": f"{SITE_URL}/",
            "potentialAction": {"@type": "SearchAction", "target": f"{SITE_URL}/?q={{search_term_string}}",
                                "query-input": "required name=search_term_string"}}
    return f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'


SEARCH_HTML = """<div class="search"><input id="q" type="search" placeholder="Search skills by name, tag or use case…" aria-label="Search skills" autocomplete="off"></div>
<div id="results" class="grid" style="margin-top:16px"></div>
<script>
(function(){
  var q=document.getElementById('q'),out=document.getElementById('results'),data=null;
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function card(s){return '<article class="card"><h3><a href="/skills/'+esc(s.slug)+'/">'+esc(s.name)+'</a></h3><p>'+esc(s.short_description)+'</p><div class="meta"><span class="chip">'+esc(s.category)+'</span><span>'+(s.stars||0)+'\\u2605</span><span>by '+esc(s.author)+'</span></div></article>';}
  function run(){
    var v=q.value.trim().toLowerCase();
    if(!v){out.innerHTML='';return;}
    var terms=v.split(/\\s+/);
    var hits=data.filter(function(s){var t=[s.name,s.slug,s.short_description,(s.tags||[]).join(' '),s.category].join(' ').toLowerCase();return terms.every(function(w){return t.indexOf(w)>-1;});});
    hits.sort(function(a,b){return (b.stars||0)-(a.stars||0);});
    out.innerHTML=hits.length?hits.slice(0,24).map(card).join(''):'<p style="color:var(--muted)">No skills match \\u201c'+esc(v)+'\\u201d.</p>';
  }
  function load(cb){if(data)return cb();fetch('/data/skills.json').then(function(r){return r.json();}).then(function(d){data=d;cb();});}
  q.addEventListener('input',function(){load(run);});
  var p=new URLSearchParams(location.search).get('q');
  if(p){q.value=p;load(run);}
})();
</script>"""


# --- Round 3: best-of guides, llms.txt, IndexNow --------------------------------
INDEXNOW_KEY = "e33b9eaee844da66f9e785d5f65d9cbe"
BEST_TOPICS = [
    ("seo", "SEO", r"\bseo\b|search engine|serp|backlink|ai-visibility"),
    ("marketing", "Marketing", r"marketing|\bads\b|copywrit|growth|social media"),
    ("writing", "Writing", r"writing|blog|humaniz|copy|essay"),
    ("video", "Video", r"video|youtube|tiktok|remotion|shorts"),
    ("design", "UI Design", r"\bui\b|ui-ux|design|figma|tailwind|frontend"),
    ("python", "Python", r"python|pytest|django|fastapi"),
    ("react", "React & Next.js", r"\breact\b|nextjs|next\.js"),
    ("testing", "Testing", r"\btests?\b|testing|playwright|e2e|\bqa\b"),
    ("git", "Git & GitHub", r"\bgit\b|github|commit|pull request"),
    ("docker", "Docker & DevOps", r"docker|kubernetes|devops|ci/cd|deploy"),
    ("security", "Security", r"security|pentest|vulnerab|audit"),
    ("data", "Data Analysis", r"\bdata\b|analytics|\bsql\b|dashboard|chart"),
    ("research", "Research", r"research|paper|arxiv|literature"),
    ("documents", "PDF & Documents", r"\bpdf\b|docx|document|markdown"),
    ("obsidian", "Obsidian & Notes", r"obsidian|note-taking|\bnotes\b"),
    ("automation", "Automation", r"automat|workflow|browser|scrap|crawl"),
    ("mcp", "MCP", r"\bmcp\b"),
    ("game-dev", "Game Development", r"godot|\bgame|unity|bevy"),
]


def skill_text(s: dict) -> str:
    return " ".join([s.get("name") or "", s.get("slug") or "", s.get("short_description") or "",
                     " ".join(s.get("tags") or [])]).lower()


def best_pages(skills: list[dict], min_items: int = 5, top: int = 20) -> list[tuple[str, str, list[dict]]]:
    out = []
    for slug, label, pattern in BEST_TOPICS:
        rx = _re.compile(pattern)
        items = [s for s in skills if rx.search(skill_text(s))]
        if len(items) >= min_items:
            out.append((slug, label, by_stars(items)[:top]))
    return out


def render_best(slug: str, label: str, items: list[dict]) -> str:
    year = datetime.now().year
    title = f"Best {label} Claude Code Skills ({year})"
    desc = (f"The top {len(items)} open-source Claude Code skills for {label}, ranked by GitHub stars, "
            f"with what each one does and a one-line install command.")
    rows = []
    for i, s in enumerate(items, 1):
        rows.append(
            f'<li style="margin:0 0 22px"><h3 style="font-size:19px;color:#fff;margin-bottom:4px">{i}. '
            f'<a href="/skills/{esc(s["slug"])}/">{esc(s["name"])}</a></h3>'
            f'<p style="color:var(--muted);margin-bottom:6px">{esc(s.get("short_description", ""))}</p>'
            f'<p style="font-size:13px;color:var(--muted)">{s.get("stars", 0)}★ · by {esc(s.get("author", ""))} · '
            f'<a href="/category/{esc(s.get("category", "other"))}/">{esc(s.get("category", "other"))}</a></p>'
            f'<pre style="margin-top:8px"><code>{esc(install_cmd(s))}</code></pre></li>')
    others = " ".join(f'<a href="/best/{b}/">{esc(lb)}</a>' for b, lb, _ in best_pages_cache if b != slug)
    body = f"""<div class="wrap">
<div class="breadcrumb" style="margin-top:24px"><a href="/">Home</a> › <a href="/best/">Best skills</a> › {esc(label)}</div>
<section class="hero" style="padding:30px 0 20px">
<h1>{esc(title)}</h1>
<p>{esc(desc)} Skills use the open SKILL.md format, so most also work in Codex CLI and other agents that support it.</p>
</section>
{seo_promo_full('best-' + slug) if slug in SEO_PROMO_TOPICS else ''}
<section class="detail" style="display:block;padding-top:0">
<ol style="list-style:none;padding:0">{''.join(rows)}</ol>
<p style="color:var(--muted);font-size:14px">Ranking is by GitHub stars at the last update. Always review a skill's code before installing it.</p>
</section>
<section><h2>More guides</h2><div class="tag-cloud">{others}</div></section>
</div>"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": title, "itemListElement": [
        {"@type": "ListItem", "position": i, "url": f"{SITE_URL}/skills/{s['slug']}/", "name": s["name"]}
        for i, s in enumerate(items, 1)]}
    return layout(title=f"{title} — {SITE_NAME}", description=desc, body=body, canonical=f"/best/{slug}/",
                  extra_head=f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


def render_best_index(bests: list[tuple[str, str, list[dict]]]) -> str:
    cards = "\n".join(
        f'<article class="card"><h3><a href="/best/{b}/">Best {esc(lb)} skills</a></h3>'
        f'<p>Top {len(items)} picks, led by {esc(items[0]["name"])}.</p></article>' for b, lb, items in bests)
    body = f"""<div class="wrap">
<section class="hero" style="padding:50px 0 30px">
<h1>Best Claude Code skills by topic</h1>
<p>Topic guides: the most-starred open-source skills for each use case, ranked by GitHub stars, with install commands.</p>
</section>
<section><div class="grid">{cards}</div></section>
</div>"""
    return layout(title=f"Best Claude Code skills by topic — {SITE_NAME}",
                  description="Topic guides to the best open-source Claude Code skills: SEO, Python, testing, design, video and more.",
                  body=body, canonical="/best/")


def guides_cloud(skills: list[dict]) -> str:
    return " ".join(f'<a href="/best/{b}/">Best {esc(lb)} skills</a>' for b, lb, _ in best_pages(skills))


def write_llms(skills: list[dict], bests: list[tuple[str, str, list[dict]]]) -> None:
    cats = sorted({s.get("category", "other") for s in skills})
    lines = [f"# {SITE_NAME}", "",
             f"> {SITE_NAME} is an independent directory of {len(skills)} open-source Claude Code skills "
             "(SKILL.md format), with categories, topic guides, install commands and a public JSON feed. "
             "Not affiliated with Anthropic.", "",
             "## Key pages", f"- [Home]({SITE_URL}/): top skills and search",
             f"- [Best skills by topic]({SITE_URL}/best/): topic guides ranked by GitHub stars",
             f"- [All skills as JSON]({SITE_URL}/data/skills.json): name, description, category, tags, stars, repo",
             f"- [Sitemap]({SITE_URL}/sitemap.xml)", "", "## Topic guides"]
    lines += [f"- [Best {lb} skills]({SITE_URL}/best/{b}/)" for b, lb, _ in bests]
    lines += ["", "## Blog"] + [f"- [{p['title']}]({SITE_URL}/blog/{p['slug']}/)" for p in BLOG_POSTS]
    lines += ["", "## Categories"]
    lines += [f"- [{c.replace('-', ' ').title()}]({SITE_URL}/category/{c}/)" for c in cats]
    lines += ["", "## Top skills"]
    lines += [f"- [{s['name']}]({SITE_URL}/skills/{s['slug']}/): {s.get('short_description', '')}" for s in by_stars(skills)[:50]]
    write_file("llms.txt", "\n".join(lines) + "\n")


def indexnow_ping(urls: list[str]) -> None:
    if os.environ.get("CF_PAGES_BRANCH") != "main":
        print("[indexnow] skipped (not a production build)")
        return
    import urllib.request
    host = SITE_URL.split("://", 1)[1]
    payload = json.dumps({"host": host, "key": INDEXNOW_KEY, "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
                          "urlList": [f"{SITE_URL}{u}" for u in urls][:10000]}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=payload,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"[indexnow] submitted {len(urls)} URLs, HTTP {r.status}")
    except Exception as e:  # never fail the build because of a ping
        print(f"[indexnow] ping failed: {e}")


best_pages_cache: list[tuple[str, str, list[dict]]] = []


# --- SEO pack promo ---------------------------------------------------------------
SEO_PACK_URL = "https://daillyteen.gumroad.com/l/rxwob"
SEO_PROMO_TOPICS = {"seo", "marketing", "writing"}
SEO_SKILL_RX = _re.compile(r"\bseo\b|marketing|backlink|\bserp\b|ai-visibility|\bgeo\b|\baeo\b")


def seo_url(placement: str) -> str:
    return f"{SEO_PACK_URL}?utm_source=skillnest&utm_medium=directory&utm_campaign={placement}"


def seo_promo_full(placement: str) -> str:
    return f"""<a class="promo" href="{esc(seo_url(placement))}" target="_blank" rel="noopener sponsored" style="text-decoration:none">
<div class="body">
<span class="tag">Sponsored</span>
<h3>SEO &amp; Programmatic-SEO Skills Pack — $9</h3>
<p>6 Claude Code skills to audit, fix and scale SEO, plus the real case study of fixing this directory. One-time buy.</p>
</div>
<span class="btn">Get the pack<b>→</b></span>
</a>"""


def seo_promo_compact() -> str:
    return f"""<a class="promo compact" href="{esc(seo_url('skill-sidebar-seo'))}" target="_blank" rel="noopener sponsored" style="text-decoration:none">
<span class="tag">Sponsored</span>
<h3 style="font-size:16px">Doing SEO with Claude?</h3>
<p>SEO &amp; pSEO Skills Pack — 6 skills + a real case study. $9.</p>
<span class="btn">View on Gumroad →</span>
</a>"""


def sidebar_promo(s: dict) -> str:
    if SEO_SKILL_RX.search(skill_text(s)):
        return seo_promo_compact()
    return promo_block_compact()


# --- Blog -----------------------------------------------------------------------------
BLOG_POSTS = [
    {
        "slug": "8-seo-bugs-programmatic-seo-site",
        "title": "8 SEO bugs Claude Code found in my programmatic-SEO site before launch",
        "description": "A redirect rule that could 404 a whole site, 529 thin tag pages, self-comparison pages and more: what an AI audit of a static pSEO directory found, and the rule for each.",
        "date": "2026-11-21",
        "html": """
<p>SkillNest is a programmatic-SEO directory: a Python script turns a JSON file of ~600 GitHub repositories into ~1,100 static pages on Cloudflare Pages. Programmatic SEO is great until it isn't &mdash; one wrong template rule is multiplied across every page.</p>
<p>Before submitting the sitemap, I asked Claude Code to audit the generated build folder the way a technical SEO would. Here is what it found, and the rule each fix turned into.</p>

<h2>1. A redirect rule that could 404 the whole site</h2>
<p>The generator wrote <code>/* /404.html 404</code> into <code>_redirects</code>. On Cloudflare Pages, redirects are evaluated before static assets, so a catch-all rule can shadow real pages.</p>
<p><strong>Rule:</strong> never use a catch-all rule for 404s on a host that already serves <code>404.html</code> automatically.</p>

<h2>2. Hundreds of one-item tag pages</h2>
<p>529 of 665 tag pages listed exactly one item &mdash; textbook thin content.</p>
<p><strong>Rule:</strong> group pages need at least 3 items to be indexable. Below that they get <code>noindex,follow</code> and stay out of the sitemap.</p>

<h2>3. Self-comparison pages</h2>
<p>The &ldquo;A vs B&rdquo; generator paired featured items with themselves, producing pages like <em>docs vs docs</em>.</p>
<p><strong>Rule:</strong> only compare items within the same category, never an item with itself, and cap the total.</p>

<h2>4. The same broken install command on every page</h2>
<p>Every skill page showed <code>/plugin install &lt;slug&gt;</code>, which does not work for most skills.</p>
<p><strong>Rule:</strong> generate per-item content from the data &mdash; here a real <code>git clone</code> command, with a different command when the skill lives in a sub-folder of a larger repository.</p>

<h2>5. lastmod was the build date</h2>
<p>Every URL in the sitemap had the same <code>&lt;lastmod&gt;</code>: the time of the build. Search engines learn to ignore that.</p>
<p><strong>Rule:</strong> use each record's real update date.</p>

<h2>6. Junk in the dataset</h2>
<p>The weekly scraper had pulled in generic &ldquo;awesome&rdquo; lists and even a repository of leaked proprietary source code.</p>
<p><strong>Rule:</strong> filter at build time, not by hand, so the next scrape cannot bring the junk back.</p>

<h2>7. Thin structured data</h2>
<p><strong>Rule:</strong> SoftwareApplication + FAQPage + BreadcrumbList on item pages and ItemList on &ldquo;best of&rdquo; pages &mdash; using only facts that are visible on the page.</p>

<h2>8. The domain move</h2>
<p>The site moved from a free <code>pages.dev</code> subdomain to <code>skillnest.dev</code>.</p>
<p><strong>Rule:</strong> 301 redirects that preserve path and query string, the new canonical host everywhere (sitemap, robots.txt, og:image), and Change of Address in Google Search Console.</p>

<h2>The takeaway</h2>
<p>Point the audit at the <strong>generator</strong>, not the generated HTML. Fix the HTML by hand and the next build quietly undoes your work.</p>
<p>The checks above are packaged as Claude Code skills in the <a href="https://daillyteen.gumroad.com/l/rxwob?utm_source=skillnest&amp;utm_medium=blog&amp;utm_campaign=8-seo-bugs" rel="noopener sponsored">SEO &amp; Programmatic-SEO Skills Pack</a> ($9) &mdash; but everything in this post works without it. If you are building something similar, the <a href="/best/seo/">best SEO skills</a> guide is a good place to start.</p>
""",
    },
]


def render_post(p: dict) -> str:
    url = f"/blog/{p['slug']}/"
    body = f"""<div class="wrap">
<div class="detail" style="display:block;max-width:760px">
<div class="breadcrumb"><a href="/">Home</a> › <a href="/blog/">Blog</a> › {esc(p['title'])}</div>
<h1>{esc(p['title'])}</h1>
<p class="short">{esc(p['description'])}</p>
<p style="color:var(--muted);font-size:14px;margin-bottom:28px">{SITE_NAME} · <time datetime="{p['date']}">{p['date']}</time></p>
<article class="long">{p['html']}</article>
</div>
</div>"""
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"],
          "description": p["description"], "datePublished": p["date"], "dateModified": p["date"],
          "mainEntityOfPage": f"{SITE_URL}{url}", "image": f"{SITE_URL}/og.png",
          "author": {"@type": "Organization", "name": SITE_NAME, "url": f"{SITE_URL}/"},
          "publisher": {"@type": "Organization", "name": SITE_NAME, "url": f"{SITE_URL}/"}}
    return layout(title=f"{p['title']} — {SITE_NAME}", description=p["description"], body=body,
                  canonical=url, extra_head=f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')


def render_blog_index() -> str:
    cards = "\n".join(
        f'<article class="card"><h3><a href="/blog/{p["slug"]}/">{esc(p["title"])}</a></h3>'
        f'<p>{esc(p["description"])}</p><div class="meta"><span>{p["date"]}</span></div></article>'
        for p in sorted(BLOG_POSTS, key=lambda x: x["date"], reverse=True))
    body = f"""<div class="wrap">
<section class="hero" style="padding:50px 0 30px">
<h1>Blog</h1>
<p>Notes on building with Claude Code skills, programmatic SEO and running this directory.</p>
</section>
<section><div class="grid">{cards}</div></section>
</div>"""
    return layout(title=f"Blog — {SITE_NAME}", description="Notes on Claude Code skills, programmatic SEO and building SkillNest.",
                  body=body, canonical="/blog/")


BLOG_POSTS += [
    {
        "slug": "install-claude-code-skills-windows",
        "title": "How to install Claude Code skills on Windows (and macOS/Linux)",
        "description": "Where Claude Code looks for skills on Windows, the exact PowerShell commands to install one from GitHub or a zip, and fixes for the most common reasons a skill does not show up.",
        "date": "2026-11-21",
        "html": """
<p>A Claude Code skill is just a folder with a <code>SKILL.md</code> file inside. Installing one means putting that folder where Claude Code looks for skills. Here is exactly where that is on Windows, and how to do it in a minute.</p>

<h2>Where Claude Code looks for skills</h2>
<ul>
<li><strong>Personal skills</strong> (available in every project): <code>~/.claude/skills/&lt;skill-name&gt;/SKILL.md</code>. On Windows <code>~</code> is your user folder, so the path is <code>C:\\Users\\&lt;you&gt;\\.claude\\skills\\&lt;skill-name&gt;\\SKILL.md</code>.</li>
<li><strong>Project skills</strong> (shared with your team through git): <code>.claude/skills/&lt;skill-name&gt;/SKILL.md</code> inside the project.</li>
</ul>
<p>The folder name matters: if the skill's <code>SKILL.md</code> has no <code>name</code> field, the folder name becomes the skill name.</p>

<h2>Install a skill from GitHub (PowerShell)</h2>
<p>Open PowerShell and run:</p>
<pre><code>New-Item -ItemType Directory -Force "$HOME\\.claude\\skills" | Out-Null
git clone --depth 1 https://github.com/OWNER/REPO.git "$HOME\\.claude\\skills\\my-skill"</code></pre>
<p>Replace <code>OWNER/REPO</code> and <code>my-skill</code>. Every skill page on SkillNest shows the exact command for that skill.</p>

<h3>When the skill is inside a bigger repository</h3>
<p>Many repositories hold several skills in sub-folders. Clone the repository somewhere temporary and copy only the folder you need:</p>
<pre><code>git clone --depth 1 https://github.com/anthropics/skills.git "$env:TEMP\\anthropic-skills"
Copy-Item -Recurse "$env:TEMP\\anthropic-skills\\skills\\pdf" "$HOME\\.claude\\skills\\pdf"</code></pre>

<h2>Install a skill from a zip file</h2>
<pre><code>Expand-Archive .\\my-skill.zip -DestinationPath "$env:TEMP\\my-skill"
Copy-Item -Recurse "$env:TEMP\\my-skill\\*" "$HOME\\.claude\\skills\\"</code></pre>
<p>Then check the result: the file must end up at <code>.claude\\skills\\&lt;name&gt;\\SKILL.md</code> &mdash; not one folder deeper.</p>

<h2>macOS and Linux</h2>
<pre><code>mkdir -p ~/.claude/skills
git clone --depth 1 https://github.com/OWNER/REPO.git ~/.claude/skills/my-skill</code></pre>

<h2>Check that it works</h2>
<p>You do not need to restart. Claude Code watches the skills folders and picks up added or edited skills during the session. The one exception: if the <code>skills</code> folder itself did not exist when the session started, run <code>/reload-skills</code>.</p>
<p>Then either describe the task the skill is for &mdash; Claude loads skills automatically when they are relevant &mdash; or call it directly with <code>/skill-name</code>.</p>

<h2>Troubleshooting</h2>
<ul>
<li><strong>The skill never triggers.</strong> Open <code>SKILL.md</code>: the opening <code>---</code> must be the very first line, otherwise the frontmatter (and its <code>description</code>) is not read.</li>
<li><strong>&ldquo;requires bash &hellip; Git Bash was not found&rdquo;.</strong> Some skills run shell commands with <code>shell: bash</code>. On Windows these need Git Bash, which comes with Git for Windows.</li>
<li><strong>Wrong folder depth.</strong> <code>skills\\my-skill\\my-skill\\SKILL.md</code> will not load &mdash; move the inner folder up one level.</li>
<li><strong>Two skills with the same name.</strong> Personal skills take precedence over project skills.</li>
</ul>
<p>Always read a skill's files before installing it &mdash; it is code and instructions you are giving your agent. Browse options by topic in the <a href="/best/">best skills guides</a>.</p>
""",
    },
    {
        "slug": "claude-code-skills-vs-mcp-servers",
        "title": "Claude Code skills vs MCP servers: what's the difference and when to use each",
        "description": "Skills teach Claude Code how to do a task; MCP servers give it access to outside tools and data. A plain-English comparison with examples and when to combine them.",
        "date": "2026-11-21",
        "html": """
<p>Skills and MCP servers both extend Claude Code, so they are easy to mix up. The short version: <strong>a skill is know-how, an MCP server is access.</strong></p>

<h2>What a skill is</h2>
<p>A skill is a folder with a <code>SKILL.md</code> file: instructions, conventions and examples, optionally with supporting files and scripts. Claude Code keeps every skill's short description in context and loads the full instructions only when a task matches &mdash; or when you call it with <code>/skill-name</code>. Custom slash commands have been merged into skills, so a skill is also how you build your own <code>/command</code>.</p>

<h2>What an MCP server is</h2>
<p>MCP (Model Context Protocol) is an open standard for connecting AI tools to external systems. An MCP server gives Claude Code new tools &mdash; access to a database, an issue tracker, a design tool, an API. You add one with <code>claude mcp add</code>, for example:</p>
<pre><code>claude mcp add --transport http notion https://mcp.notion.com/mcp</code></pre>
<p>Servers can be scoped to one project, to all your projects, or shared with a team through a <code>.mcp.json</code> file in the repository.</p>

<h2>Side by side</h2>
<table style="width:100%;border-collapse:collapse" cellpadding="8">
<thead><tr style="border-bottom:1px solid var(--border)"><th align="left"></th><th align="left">Skill</th><th align="left">MCP server</th></tr></thead>
<tbody>
<tr><td>Gives Claude</td><td>Instructions: how to do a task</td><td>Tools and data: what it can reach</td></tr>
<tr><td>Made of</td><td>Markdown (plus optional scripts)</td><td>A running server process or remote endpoint</td></tr>
<tr><td>Install</td><td>Copy a folder into <code>.claude/skills/</code></td><td><code>claude mcp add</code> or <code>.mcp.json</code></td></tr>
<tr><td>Typical examples</td><td>Commit-message rules, SEO audit checklist, test-writing conventions</td><td>Notion, GitHub, Postgres, browser automation</td></tr>
<tr><td>Best when</td><td>You keep repeating the same prompt or process</td><td>Claude needs to read or change something outside your files</td></tr>
</tbody></table>

<h2>When to use which</h2>
<ul>
<li>&ldquo;Every time I ask for a PR description I paste the same template&rdquo; &rarr; <strong>skill</strong>.</li>
<li>&ldquo;I want Claude to read tickets from our tracker&rdquo; &rarr; <strong>MCP server</strong>.</li>
<li>&ldquo;I want Claude to triage tickets our way&rdquo; &rarr; <strong>both</strong>: the MCP server provides access, the skill describes the triage process and which tools to use.</li>
</ul>

<h2>Combining them</h2>
<p>The most useful setups pair the two. A skill can tell Claude which MCP tools to call, in what order and with what checks &mdash; turning raw access into a repeatable workflow. Skills can also pre-approve the specific tools they need with the <code>allowed-tools</code> field.</p>
<p>Looking for skills that work well alongside MCP? See the <a href="/best/mcp/">best MCP-related skills</a>, or browse all <a href="/best/">topic guides</a>.</p>
""",
    },
    {
        "slug": "claude-code-skills-beginners-guide",
        "title": "Claude Code skills for beginners: what they are, how to install one and how to write your own",
        "description": "A beginner-friendly guide to Claude Code skills: what a SKILL.md is, how Claude decides to use it, how to install a skill and how to write your first one in five minutes.",
        "date": "2026-11-21",
        "html": """
<p>If you keep typing the same instructions into Claude Code &mdash; &ldquo;write tests like this&rdquo;, &ldquo;format commits like that&rdquo; &mdash; a skill lets you write them down once.</p>

<h2>What is a skill?</h2>
<p>A skill is a folder containing a <code>SKILL.md</code> file. The file starts with a short frontmatter block and then plain instructions in Markdown. Claude Code always knows each skill's description, and loads the full instructions only when your request matches it &mdash; so you can install many skills without filling up the context.</p>

<h2>Install your first skill</h2>
<ol>
<li>Pick one from the <a href="/best/">topic guides</a> &mdash; each skill page shows its install command.</li>
<li>Run the command; it places the skill in <code>~/.claude/skills/&lt;name&gt;/</code>.</li>
<li>Back in Claude Code, just ask for the task. If the skills folder is brand new, run <code>/reload-skills</code> first.</li>
</ol>
<p>On Windows? Follow the <a href="/blog/install-claude-code-skills-windows/">Windows install guide</a>.</p>

<h2>Write your own in five minutes</h2>
<p>Create <code>~/.claude/skills/changelog-entry/SKILL.md</code>:</p>
<pre><code>---
name: changelog-entry
description: Write a CHANGELOG entry for the current changes. Use when the user asks for a changelog or release notes entry.
---

1. Read the staged diff (git diff --cached).
2. Group changes under Added / Changed / Fixed.
3. One line per change, user-facing language, no file names.
4. Show the entry; do not edit CHANGELOG.md unless asked.</code></pre>
<p>That is a complete skill. Only the <code>description</code> really matters for triggering: it tells Claude <em>what</em> the skill does and <em>when</em> to use it. If you leave out <code>name</code>, the folder name is used.</p>

<h2>Tips that make skills work better</h2>
<ul>
<li><strong>Be specific in the description.</strong> &ldquo;Use when the user asks for X&rdquo; triggers far more reliably than a vague summary.</li>
<li><strong>Say when not to use it.</strong> It prevents the skill from hijacking unrelated tasks.</li>
<li><strong>Give one short example</strong> of the output you want.</li>
<li><strong>Share with your team</strong> by putting the folder in the project's <code>.claude/skills/</code> and committing it.</li>
<li><strong>Review before installing</strong> anyone else's skill &mdash; you are giving instructions (and sometimes scripts) to your agent.</li>
</ul>

<h2>Where to find good skills</h2>
<p>SkillNest lists hundreds of open-source skills with install commands, organised by category and in topic guides such as <a href="/best/python/">Python</a>, <a href="/best/testing/">testing</a> and <a href="/best/seo/">SEO</a>. Curious how skills relate to MCP servers? Read <a href="/blog/claude-code-skills-vs-mcp-servers/">skills vs MCP servers</a>.</p>
""",
    },
]


def blog_cloud() -> str:
    return "".join(f'<a href="/blog/{p["slug"]}/">{esc(p["title"])}</a>' for p in BLOG_POSTS)


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    skills = clean_skills(json.loads(DATA.read_text(encoding="utf-8")))
    print(f"[gen] {len(skills)} skills")

    urls: list[str] = ["/"]

    # Home
    write_file("index.html", render_home(skills))

    # Skill detail
    for s in skills:
        write_file(f"skills/{s['slug']}/index.html", render_skill(s, skills))
        urls.append(f"/skills/{s['slug']}/")

    # Category pages
    cats: dict[str, list[dict]] = {}
    for s in skills:
        cats.setdefault(s.get("category", "other"), []).append(s)
    for cat, items in cats.items():
        write_file(
            f"category/{cat}/index.html",
            render_listing(
                title=f"Best {cat.replace('-', ' ').title()} Claude Code Skills ({len(items)})",
                description=category_desc(cat, items),
                skills=items,
                canonical=f"/category/{cat}/",
            ),
        )
        urls.append(f"/category/{cat}/")

    # Tag pages
    tags: dict[str, list[dict]] = {}
    for s in skills:
        for t in (s.get("tags") or []):
            tags.setdefault(t, []).append(s)
    for tag, items in tags.items():
        if len(items) < 1:
            continue
        page = render_listing(
            title=f'Claude Code skills tagged "{tag}"',
            description=f"All Claude Code skills tagged with {tag} — {len(items)} match{'es' if len(items) > 1 else ''}.",
            skills=items,
            canonical=f"/tag/{tag}/",
        )
        if len(items) < MIN_TAG_INDEX:
            page = page.replace('content="index,follow,max-image-preview:large"', 'content="noindex,follow"')
        write_file(f"tag/{tag}/index.html", page)
        if len(items) >= MIN_TAG_INDEX:
            urls.append(f"/tag/{tag}/")

    # Compare pages — top 12 featured × 12 other = ~50 cross pairs
    top = [s for s in skills if s.get("featured")] + skills
    seen_pairs = set()
    compare_count = 0
    for a, b in compare_pairs(skills):
        key = tuple(sorted([a["slug"], b["slug"]]))
        if key in seen_pairs or a["slug"] == b["slug"]:
            continue
        seen_pairs.add(key)
        write_file(f"compare/{a['slug']}-vs-{b['slug']}/index.html", render_compare(a, b))
        urls.append(f"/compare/{a['slug']}-vs-{b['slug']}/")
        compare_count += 1

    # Best-of guides
    bests = best_pages(skills)
    best_pages_cache[:] = bests
    for slug, label, items in bests:
        write_file(f"best/{slug}/index.html", render_best(slug, label, items))
        urls.append(f"/best/{slug}/")
    write_file("best/index.html", render_best_index(bests))
    urls.append("/best/")

    # Blog
    for p in BLOG_POSTS:
        write_file(f"blog/{p['slug']}/index.html", render_post(p))
        urls.append(f"/blog/{p['slug']}/")
    write_file("blog/index.html", render_blog_index())
    urls.append("/blog/")

    # Submit
    write_file("submit/index.html", render_submit())
    urls.append("/submit/")

    # Data endpoint
    write_file("data/skills.json", json.dumps(skills, ensure_ascii=False, indent=2))

    # Sitemap, robots, RSS
    write_sitemap(urls, {f"/skills/{s['slug']}/": (s.get("updated_at") or "")[:10] for s in skills})
    write_robots()
    write_rss(skills)
    write_llms(skills, bests)
    write_file(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY)

    # Cloudflare Pages config + 404
    write_file("_headers", CF_HEADERS)
    write_file("404.html", NOT_FOUND)
    if (ROOT / "og.png").exists():
        shutil.copy(ROOT / "og.png", OUT / "og.png")

    print(f"[gen] skill pages:    {len(skills)}")
    print(f"[gen] category pages: {len(cats)}")
    print(f"[gen] tag pages:      {len(tags)}")
    print(f"[gen] compare pages:  {compare_count}")
    print(f"[gen] total URLs:     {len(urls)}")
    print(f"[gen] output:         {OUT}")
    indexnow_ping(urls)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
