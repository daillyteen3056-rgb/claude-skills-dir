# SkillNest — Claude Code skills directory

Source for **[skillnest.dev](https://skillnest.dev)**: a searchable directory of Claude Code skills, with copy-paste install commands, category and tag pages, side-by-side comparisons and "best of" guides.

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
