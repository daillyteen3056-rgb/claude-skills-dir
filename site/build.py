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

SITE_NAME = os.environ.get("SITE_NAME", "Claude Skills")
SITE_URL = os.environ.get("SITE_URL", "https://claude-skills.pages.dev").rstrip("/")
SITE_TAGLINE = "The directory for Claude Code skills, plugins, and agents"

# Search engine verification tokens (safe to be public — they only prove ownership)
GOOGLE_VERIFY = os.environ.get("GOOGLE_VERIFY", "_tu33hAptmiDtcn1xUiAldSyNKXh0X5iY3rWDHwvHEc")
BING_VERIFY = os.environ.get("BING_VERIFY", "")
YANDEX_VERIFY = os.environ.get("YANDEX_VERIFY", "")

# Monetization — Gumroad pack (sponsored CTA across the site)
GUMROAD_URL = os.environ.get("GUMROAD_URL", "https://daillyteen.gumroad.com/l/wapct")
GUMROAD_TITLE = "Claude Code Skills Pack"
GUMROAD_PRICE = "$19"
GUMROAD_PITCH = "Curated, battle-tested pack of production Claude Code skills. One-time buy, lifetime updates."


def gumroad_url(placement: str) -> str:
    """Append UTM params for attribution."""
    sep = "&" if "?" in GUMROAD_URL else "?"
    return f"{GUMROAD_URL}{sep}utm_source=claude-skills&utm_medium=directory&utm_campaign={placement}"
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
<p>{esc(GUMROAD_TITLE)} — curated, production-ready. {esc(GUMROAD_PRICE)}.</p>
<span class="btn">View on Gumroad →</span>
</a>"""


def render_home(skills: list[dict]) -> str:
    featured = [s for s in skills if s.get("featured")][:6]
    all_skills = skills
    categories = sorted({s.get("category", "other") for s in skills})
    tags = sorted({t for s in skills for t in (s.get("tags") or [])})

    featured_html = "\n".join(skill_card(s) for s in featured)
    all_html = "\n".join(skill_card(s) for s in all_skills)
    cats_html = " ".join(
        f'<a href="/category/{esc(c)}/">{esc(c.replace("-", " ").title())}</a>'
        for c in categories
    )
    tags_html = " ".join(f'<a href="/tag/{esc(t)}/">{esc(t)}</a>' for t in tags[:40])

    body = f"""<div class="wrap">
<section class="hero">
<h1>Every Claude Code skill,<br><span>one search away.</span></h1>
<p>{esc(SITE_DESC)}</p>
<div class="stats">
<div><b>{len(skills)}</b>skills indexed</div>
<div><b>{len(categories)}</b>categories</div>
<div><b>{len(tags)}</b>tags</div>
</div>
{promo_block_full()}
</section>

<section>
<h2>Featured</h2>
<div class="grid">{featured_html}</div>
</section>

<section>
<h2>Categories</h2>
<div class="tag-cloud">{cats_html}</div>
</section>

<section>
<h2>All skills ({len(skills)})</h2>
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
    )


def render_skill(s: dict, all_skills: list[dict]) -> str:
    related = [
        x for x in all_skills
        if x["slug"] != s["slug"] and x.get("category") == s.get("category")
    ][:3]
    related_html = "\n".join(skill_card(r) for r in related) or "<p>No related skills.</p>"

    triggers = s.get("triggers") or []
    triggers_html = (
        "<ul>" + "".join(f"<li><code>{esc(t)}</code></li>" for t in triggers) + "</ul>"
        if triggers else "<p>No specific triggers listed.</p>"
    )

    install_block = (
        f"<pre><code># In your Claude Code session\n"
        f"/plugin install {esc(s['slug'])}</code></pre>"
    )

    jsonld = jsonld_software_app(s)
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
{promo_block_compact()}
</aside>
</div>
</div>"""
    return layout(
        title=f"{s['name']} — Claude Code skill",
        description=s.get("short_description", ""),
        body=body,
        canonical=f"/skills/{s['slug']}/",
        extra_head=jsonld,
    )


def render_listing(title: str, description: str, skills: list[dict], canonical: str) -> str:
    cards = "\n".join(skill_card(s) for s in skills) or "<p>No skills in this group yet.</p>"
    body = f"""<div class="wrap">
<section class="hero" style="padding:50px 0 30px">
<h1>{esc(title)}</h1>
<p>{esc(description)}</p>
</section>
<section>
<div class="grid">{cards}</div>
</section>
</div>"""
    return layout(title=f"{title} — {SITE_NAME}", description=description, body=body, canonical=canonical)


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
<p>Built a Claude Code skill? Open a PR on our GitHub repo or email <code>hi@claude-skills.dev</code>. Include: name, GitHub URL, short description, category, tags.</p>
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


def write_sitemap(urls: list[str]) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    items = "\n".join(
        f"<url><loc>{SITE_URL}{u}</loc><lastmod>{now}</lastmod></url>"
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


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    skills = json.loads(DATA.read_text(encoding="utf-8"))
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
                title=f"{cat.replace('-', ' ').title()} skills",
                description=f"Claude Code skills in the {cat} category — {len(items)} indexed.",
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
            title=f'Skills tagged "{tag}"',
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
    for a, b in itertools.combinations(top[:12], 2):
        key = tuple(sorted([a["slug"], b["slug"]]))
        if key in seen_pairs or a["slug"] == b["slug"]:
            continue
        seen_pairs.add(key)
        write_file(f"compare/{a['slug']}-vs-{b['slug']}/index.html", render_compare(a, b))
        urls.append(f"/compare/{a['slug']}-vs-{b['slug']}/")
        compare_count += 1

    # Submit
    write_file("submit/index.html", render_submit())
    urls.append("/submit/")

    # Data endpoint
    write_file("data/skills.json", DATA.read_text(encoding="utf-8"))

    # Sitemap, robots, RSS
    write_sitemap(urls)
    write_robots()
    write_rss(skills)

    # Cloudflare Pages config + 404
    write_file("_headers", CF_HEADERS)
    write_file("404.html", NOT_FOUND)

    print(f"[gen] skill pages:    {len(skills)}")
    print(f"[gen] category pages: {len(cats)}")
    print(f"[gen] tag pages:      {len(tags)}")
    print(f"[gen] compare pages:  {compare_count}")
    print(f"[gen] total URLs:     {len(urls)}")
    print(f"[gen] output:         {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
