# Deploy to Cloudflare Pages

Two paths. **Path A (GitHub integration)** is recommended for long-term — every push auto-rebuilds. **Path B (direct upload)** is faster for a one-time test.

---

## Path A — GitHub + CF Pages (recommended)

### 1. Create a GitHub repo

```powershell
cd C:\Users\admin\Desktop\seo\claude-skills-dir
git init
git add .
git commit -m "init: claude code skills directory"
```

Create a new empty repo on github.com, name it `claude-skills` (or whatever). Then:

```powershell
git remote add origin https://github.com/YOUR_USER/claude-skills.git
git branch -M main
git push -u origin main
```

### 2. Connect to Cloudflare Pages

1. Go to https://dash.cloudflare.com → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Authorize GitHub, pick `claude-skills` repo.
3. Build settings:
   - **Framework preset:** None
   - **Build command:** `python3 site/build.py`
   - **Build output directory:** `site/dist`
   - **Root directory:** (leave blank — project root)
4. Environment variables (optional): `PYTHON_VERSION = 3.12`
5. Click **Save and Deploy**.

First build ~1-2 min. You get a URL like `https://claude-skills.pages.dev`.

### 3. Auto-rebuild on every push

Every `git push` to `main` triggers a rebuild. To add new skills:

```powershell
python scraper/scrape.py     # optional — pulls new from GitHub
git add data/skills.json
git commit -m "add: 5 new skills"
git push
```

CF Pages rebuilds in ~60s.

### 4. Custom domain (optional)

- Buy domain (Namecheap/Cloudflare Registrar, ~$10/year for .dev)
- CF dashboard → your Pages project → **Custom domains** → **Set up a custom domain**
- CF handles SSL cert + CDN automatically

---

## Path B — Drag-and-drop (quick test)

### 1. Build locally

```powershell
cd C:\Users\admin\Desktop\seo\claude-skills-dir
python site\build.py
```

### 2. Zip the output

```powershell
Compress-Archive -Path site\dist\* -DestinationPath claude-skills-dist.zip -Force
```

### 3. Upload

1. https://dash.cloudflare.com → **Workers & Pages** → **Create** → **Pages** → **Upload assets**
2. Project name: `claude-skills`
3. Drop `claude-skills-dist.zip`
4. Click **Deploy site**

Live in ~30 seconds at `https://claude-skills.pages.dev`.

**Downside:** no auto-rebuild — every update is a manual re-zip + re-upload.

---

## Path C — Wrangler CLI (if you have Node)

```powershell
npm i -g wrangler
wrangler login
wrangler pages deploy site\dist --project-name=claude-skills
```

Wrangler reads `wrangler.toml` for config. First deploy creates the project.

---

## After deploy — SEO submission checklist

Once live, submit to search engines for faster indexing:

1. **Google Search Console** — https://search.google.com/search-console
   - Add property → paste domain → verify with DNS TXT record (CF makes this easy)
   - Submit `sitemap.xml` under **Sitemaps**

2. **Bing Webmaster Tools** — https://www.bing.com/webmasters
   - Same flow. Bing powers DuckDuckGo + Yahoo too.

3. **IndexNow** (optional, fast indexing) — one-shot ping to notify search engines of new URLs
   - Already scaffolded in `ping-indexnow.sh` style (you have one in the trump project)

4. **Submit to directories**:
   - https://awesome-claude.dev (if exists)
   - r/ClaudeAI (allowed as Show post, not spam)
   - Hacker News Show HN (Monday morning best)

---

## Monitoring

Cloudflare dashboard shows:
- Request count
- Bandwidth
- Cache hit ratio (should be > 90% for static site)
- Top URLs (= your top-ranking SEO pages)

Free tier: **unlimited requests + 500 builds/month**. For this scale, free tier covers 100k+ visits/month.
