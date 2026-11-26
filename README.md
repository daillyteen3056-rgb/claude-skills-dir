# SkillNest — Claude Code Skills Directory

[![Website](https://img.shields.io/badge/website-skillnest.dev-a78bfa)](https://skillnest.dev) [![Skills](https://img.shields.io/badge/skills-560%2B-blue)](https://skillnest.dev) [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**[skillnest.dev](https://skillnest.dev)** is a free, searchable directory of 560+ Claude Code skills (`SKILL.md`), with copy-paste install commands, category and tag pages, side-by-side comparisons and "best of" guides. This repository is the open-source scraper and static site generator behind it.

## Browse Claude Code skills by topic

| | | | |
|---|---|---|---|
| [SEO](https://skillnest.dev/best/seo/) | [Marketing](https://skillnest.dev/best/marketing/) | [Writing](https://skillnest.dev/best/writing/) | [Humanizing AI text](https://skillnest.dev/best/humanizer/) |
| [Video](https://skillnest.dev/best/video/) | [UI design](https://skillnest.dev/best/design/) | [PDF & documents](https://skillnest.dev/best/documents/) | [Obsidian & notes](https://skillnest.dev/best/obsidian/) |
| [Research](https://skillnest.dev/best/research/) | [Data analysis](https://skillnest.dev/best/data/) | [Python](https://skillnest.dev/best/python/) | [TypeScript](https://skillnest.dev/best/typescript/) |
| [React & Next.js](https://skillnest.dev/best/react/) | [Rust](https://skillnest.dev/best/rust/) | [APIs & backend](https://skillnest.dev/best/api/) | [Databases](https://skillnest.dev/best/database/) |
| [Testing](https://skillnest.dev/best/testing/) | [Debugging](https://skillnest.dev/best/debugging/) | [Refactoring](https://skillnest.dev/best/refactoring/) | [Git & GitHub](https://skillnest.dev/best/git/) |
| [Docker & DevOps](https://skillnest.dev/best/docker/) | [Security](https://skillnest.dev/best/security/) | [Automation](https://skillnest.dev/best/automation/) | [MCP](https://skillnest.dev/best/mcp/) |
| [AI & machine learning](https://skillnest.dev/best/ai-ml/) | [Mobile](https://skillnest.dev/best/mobile/) | [Game development](https://skillnest.dev/best/game-dev/) | [Beginners](https://skillnest.dev/best/beginners/) |

All guides: [skillnest.dev/best](https://skillnest.dev/best/) · Newest skills: [skillnest.dev/new](https://skillnest.dev/new/)

## How to install a Claude Code skill

A skill is a folder containing a `SKILL.md` file. Claude Code loads skills from two places:

- **Global** (every project): `~/.claude/skills/<skill-name>/`
- **One project only**: `.claude/skills/<skill-name>/` inside that repo

```bash
git clone https://github.com/<author>/<repo> ~/.claude/skills/<skill-name>
```

To check it loaded, type `/` in Claude Code: the skill appears in the slash-command menu under its folder name. Every skill page on SkillNest shows the exact install command for that skill.

## How it works

1. `scraper/scrape.py` collects public Claude Code skills from GitHub. A GitHub Actions workflow runs it every week and commits the result to `data/skills.json`.
2. `site/build.py` turns that file into a static HTML site (no JavaScript build step) in `site/dist/`.
3. Cloudflare Pages rebuilds and deploys the site on every push to `main`.

## Build locally

```bash
python3 site/build.py          # output: site/dist/
```

Set `SITE_URL` to change the canonical URL (default: `https://skillnest.dev`).

## Add or update a skill

Use the form at [skillnest.dev/submit](https://skillnest.dev/submit/) or open an issue in this repo.

## License & attribution

The code in this repository (scraper, site generator, workflows) is [MIT-licensed](LICENSE).

SkillNest is an index, not a mirror: it does not copy or redistribute any skill's files. For each listed skill, `data/skills.json` stores only metadata — name, author (with a link to their profile), a short description, trigger phrases, category, tags and star count — plus the URL of the upstream repository. Every skill page credits the author and links back to that repository. Each skill stays under its own upstream license and belongs to its authors. If you maintain a listed skill and want it changed or removed, open an issue or email hi@skillnest.dev.
