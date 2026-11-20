# Claude Code Skills Directory

Programmatic-SEO directory of Claude Code skills, plugins, and agents. Each skill gets its own SEO-indexed page. Google indexes everything, long-tail traffic compounds over 3-6 months.

**Domain target:** `claude-skills.dev` (or whatever you buy)

## Architecture

```
claude-skills-dir/
├── scraper/               # weekly cron, pulls new skills from GitHub + Anthropic
│   ├── scrape.py          # GitHub topic:claude-code-skill + registry scan
│   ├── enrich.py          # README parsing, tag extraction
│   └── seed.json          # hand-curated 10 initial items
├── data/
│   └── skills.json        # single source of truth (built by scraper)
├── site/                  # Astro site — pSEO + static output
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.astro            # homepage: top skills, categories
│   │   │   ├── skills/[slug].astro    # dynamic — 1 page per skill
│   │   │   ├── tag/[tag].astro        # 1 page per tag ("python", "github", ...)
│   │   │   ├── compare/[a]-vs-[b].astro  # programmatic compare pages
│   │   │   └── sitemap.xml.ts         # auto-sitemap
│   │   ├── layouts/Base.astro
│   │   └── components/SkillCard.astro
│   ├── astro.config.mjs
│   └── package.json
└── deploy/                 # Cloudflare Pages or Vercel config
```

## Revenue model

1. **Featured listing** — $20/skill/month to pin at top
2. **Gumroad affiliate** — link to your paid skills-pack from category pages
3. **Email list** — "Weekly Claude Skills Digest" (Beehiiv free)
4. **Display ads** — Ezoic / Mediavine when traffic > 10k/month

## Milestones

- **Week 1-2:** scraper + 10 seed skills + homepage + skill detail template deploy
- **Week 3:** 50+ skills, submit sitemap to Google/Bing Search Console
- **Month 2-3:** 200 skills, pSEO tag pages indexed
- **Month 4-6:** 10-50k views/month organic, first featured listing sales
