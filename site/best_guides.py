"""Hand-written intros and example prompts for the /best/<topic>/ guide pages (used by build.py)."""

BEST_GUIDES = {
    "seo": (
        "SEO skills turn Claude Code into an on-page and technical SEO assistant that works directly on your files. "
        "Instead of pasting pages into a chat, you point Claude at a build folder or a list of URLs and the skill supplies "
        "the checklist: titles and meta descriptions, canonical tags, structured data, internal links, sitemaps and robots rules. "
        "The best ones return a prioritized list of fixes and can edit your templates for you. They work best on static sites "
        "and frameworks where the HTML lives in your repo. Treat their output as an audit, not a promise of rankings: rankings "
        "still depend on content quality, links and time. Check which files a skill may change before running it on a production repo.",
        ["Run a technical SEO audit on my build folder and list fixes by priority",
         "Write a title and meta description for every page in /blog"],
    ),
    "marketing": (
        "Marketing skills package repeatable marketing work, such as landing-page copy, conversion reviews, email sequences, "
        "ad variations and launch checklists, into instructions Claude Code loads when you ask for that task. Because they run "
        "inside your project, they can read your real product pages, README or docs instead of a summary you paste in, which "
        "makes the output more specific. Most are pure prompt skills: no API keys and nothing to configure beyond copying the "
        "folder. Use them for first drafts and structured reviews, then edit for your own voice. Generated copy still needs a "
        "human pass for claims, pricing and legal wording. If a skill bundles many sub-skills, install it once and call each task by name.",
        ["Review my landing page for conversion problems and suggest a stronger headline",
         "Draft a 3-email launch sequence for this product"],
    ),
    "writing": (
        "Writing skills give Claude Code a house style: how to structure a blog post, tighten a draft, write release notes or "
        "documentation, or remove the tell-tale patterns of AI-generated text. A good writing skill states its rules concretely, "
        "such as sentence length, banned phrases and heading structure, so results stay consistent across sessions instead of "
        "depending on how you phrase each request. They are especially useful in docs repos and content sites where the Markdown "
        "lives next to the code. Combine one structural skill (outlines, docs format) with one editing skill (clarity, humanizing) "
        "rather than stacking several with conflicting rules. As with any generated text, fact-check names, numbers and quotes before publishing.",
        ["Edit this draft for clarity and cut it by 20 percent",
         "Rewrite these release notes so they read naturally, not like AI"],
    ),
    "video": (
        "Video skills cover the parts of video work that can be expressed as code or text: scripts and storyboards, cutting long "
        "recordings into short clips, subtitles, and programmatic videos built with tools such as Remotion or FFmpeg. Claude Code "
        "runs these steps in your terminal, so a skill can chain commands (transcribe, pick highlights, render) that would otherwise "
        "be manual. Many video skills depend on local tools like FFmpeg, Node or Python packages, or on third-party APIs, so read "
        "each README for prerequisites before installing. Rendering is CPU-heavy; test on a short clip first. For anything you "
        "publish, review captions and cuts by hand, because automatic transcription and highlight detection still make mistakes.",
        ["Cut this recording into three 60-second clips with subtitles",
         "Write a script and shot list for a 90-second product demo"],
    ),
    "design": (
        "UI design skills give Claude Code design judgment it lacks by default: spacing and type scales, color contrast, component "
        "patterns, and ways to avoid the generic look of AI-generated interfaces. They are most useful when Claude writes frontend "
        "code in React, Vue, Tailwind or plain HTML and CSS, because the skill's rules apply directly to the components it produces. "
        "Some focus on visual taste and art direction, others on accessibility or on matching an existing design system. Pick one "
        "primary design skill so rules don't conflict, and give it a reference such as a screenshot, a brand color or an existing "
        "page. Always check the result in a browser at several screen sizes before shipping it.",
        ["Redesign this pricing page so it looks less generic, keeping our brand colors",
         "Audit these components for spacing, contrast and accessibility issues"],
    ),
    "python": (
        "Python skills encode the conventions an experienced Python developer applies: project layout, type hints, docstrings, "
        "pytest structure, packaging and dependency management. With a skill installed, asking Claude Code to add tests or refactor "
        "a module into a package follows the same steps every time instead of varying with your wording. The most useful ones read "
        "your existing configuration, such as pyproject.toml, conftest.py and linter settings, and follow it rather than imposing "
        "their own. Check whether a skill assumes a tool you don't use, such as uv, Poetry, ruff or black. Testing and code-review "
        "skills make a good first install, because their output is easy to verify by running your test suite.",
        ["Write pytest tests for utils.py covering edge cases and errors",
         "Add type hints and Google-style docstrings to this module"],
    ),
    "react": (
        "React and Next.js skills give Claude Code framework-specific rules: component structure, hooks, server versus client "
        "components, data fetching, routing and performance patterns. They matter because React advice changes quickly between "
        "versions, and a skill can pin the conventions your project actually uses. Prefer skills that state the versions they target "
        "and that read your setup (package.json, App Router or Pages Router, your styling approach) instead of rewriting it. Pair one "
        "framework skill with a design or testing skill rather than installing several overlapping React skills. After generating "
        "components, run your type checker, linter and tests, and check the page in a browser: generated UI can compile and still behave wrongly.",
        ["Convert this page to a server component and move data fetching to the server",
         "Find unnecessary re-renders in this component tree and fix them"],
    ),
    "testing": (
        "Testing skills make Claude Code write tests the way a careful engineer would: cover the happy path, edge cases and error "
        "cases, isolate side effects with fixtures and mocks, then run the suite to confirm everything passes. Without a skill, "
        "generated tests often assert trivial things or copy the implementation into the expected values. Good testing skills tell "
        "Claude to read your existing test setup first and follow its conventions, and to report real bugs instead of weakening a "
        "test until it passes. There are skills for unit tests (pytest, Jest, Vitest), browser end-to-end tests (Playwright) and "
        "test-driven workflows. Their output is easy to verify: run the tests and read a few assertions before you merge.",
        ["Write unit tests for the payment module and run them",
         "Add a Playwright test for the signup flow"],
    ),
    "git": (
        "Git and GitHub skills standardize the small, frequent version-control tasks: commit messages written from the staged diff, "
        "pull request descriptions, change reviews, branch management and release notes. Because Claude Code can run git commands "
        "itself, a skill can read the real diff and history instead of relying on your description. Look for skills that follow a "
        "convention you already use, such as Conventional Commits, and that say what they will run before running it. Be careful "
        "with skills that rewrite history, force-push or delete branches; keep those manual or require confirmation. A commit-message "
        "or PR-description skill is a low-risk first install with an immediate payoff.",
        ["Write a Conventional Commit message for my staged changes",
         "Draft a pull request description for this branch with a test plan"],
    ),
    "docker": (
        "Docker and DevOps skills help Claude Code write and review Dockerfiles, Compose files, CI pipelines and deployment configs. "
        "Typical wins are smaller images from multi-stage builds, better layer caching, running as a non-root user, pinned base images "
        "and health checks. Because these files affect production, prefer skills that explain each change and keep behavior the same "
        "unless you ask otherwise. Skills that deploy or change cloud resources should ask for confirmation and should not get "
        "production credentials by default. Check which tools a skill assumes (GitHub Actions, Kubernetes, Terraform) and validate every "
        "change by building the image and running the pipeline on a branch before merging.",
        ["Optimize this Dockerfile for size and caching without changing behavior",
         "Write a GitHub Actions workflow that runs tests on every pull request"],
    ),
    "security": (
        "Security skills turn Claude Code into a reviewer that looks for injection flaws, hard-coded secrets, vulnerable dependencies, "
        "weak authentication and risky shell commands. Some audit your code; others guard Claude itself, for example by blocking "
        "destructive commands or by scanning other skills for malicious instructions before you install them. That second group matters "
        "because a skill is instructions plus optional scripts, and a malicious one can tell the agent to run anything. Consider "
        "installing a guard or scanner before trying many third-party skills. Treat audit findings as leads to verify, not proof: automated "
        "reviews produce false positives and miss logic flaws. Only run penetration-testing skills against systems you own or are authorized to test.",
        ["Review this API for injection, auth and secrets issues",
         "Scan the skills in ~/.claude/skills for risky instructions"],
    ),
    "data": (
        "Data analysis skills guide Claude Code through the whole loop of working with data: loading CSV, Excel or database tables, "
        "cleaning them, writing SQL or pandas code, and producing charts or dashboards. Because the work happens in your project, "
        "Claude runs the code and checks the numbers instead of estimating them in prose. Good data skills insist on inspecting the "
        "data first (columns, types, missing values) and on showing the query or code behind every figure. Some specialize in "
        "visualization style, others in a particular warehouse or BI tool. Keep sensitive data local, check which libraries a skill "
        "expects, and spot-check results against a source you trust before sharing them.",
        ["Clean sales.csv, then chart monthly revenue by region",
         "Write a SQL query for 30-day retention and explain the result"],
    ),
    "research": (
        "Research skills structure how Claude Code gathers and synthesizes information: searching several sources, reading papers "
        "or long documents, tracking citations and writing a report with the evidence attached. Some focus on academic work such as "
        "literature reviews, paper summaries and a draft, review and revise cycle. Others scan recent discussion on sites like Reddit, "
        "Hacker News or X to see what people are saying about a topic. Many need web access or API keys for specific sources, so check "
        "the README before installing. The value of a research skill is consistency: the same method, the same output structure and "
        "sources you can check. Open the cited sources yourself before relying on a conclusion.",
        ["Research what developers said about this library in the last 30 days",
         "Summarize these five papers and compare their methods"],
    ),
    "documents": (
        "Document skills let Claude Code create and edit real files instead of describing them: Word documents, PDFs, PowerPoint "
        "decks, spreadsheets and Markdown. Anthropic's own skills repository includes skills for docx, pdf, pptx and xlsx, and the "
        "community has added converters, form fillers, report generators and slide builders. These skills usually rely on Python or "
        "Node libraries for each format, so check the prerequisites in each README. They shine at repeatable paperwork: turning data "
        "into a formatted report, filling a template, or pulling tables out of PDFs. Open the generated file before sending it, because "
        "layout, fonts and page breaks are the parts most likely to need a manual fix.",
        ["Turn report.md into a formatted Word document with a table of contents",
         "Extract the tables from invoice.pdf into a spreadsheet"],
    ),
    "obsidian": (
        "Obsidian and note-taking skills help Claude Code work with a Markdown knowledge base: creating notes with consistent "
        "frontmatter, linking related notes, building indexes and maps of content, and summarizing or reorganizing folders. Because an "
        "Obsidian vault is simply a folder of Markdown files, Claude Code can work on it directly when you open the vault as a project. "
        "Look for skills that respect your existing conventions (tags, link style, folder structure, templates) instead of imposing new "
        "ones. Back up or commit the vault before running a skill that renames or moves many files. Note skills pair well with research "
        "and writing skills for capturing sources and turning notes into drafts.",
        ["Create a map-of-content note linking everything tagged #project",
         "Find orphan notes in my vault and suggest where to link them"],
    ),
    "automation": (
        "Automation skills let Claude Code drive tools beyond your codebase: controlling a browser, scraping or crawling websites, "
        "filling forms, calling APIs and chaining steps into repeatable workflows. The skill supplies the procedure (which pages to "
        "visit, what to extract, how to handle errors), so a task you run every week behaves the same each time. Many depend on browser "
        "automation tools such as Playwright or on external services, so check prerequisites and any API costs. Respect websites' terms "
        "of service and rate limits when scraping. For workflows that submit forms, send messages or spend money, keep a confirmation "
        "step in the skill instead of letting it run unattended from start to finish.",
        ["Scrape the changelog pages of these three tools into one Markdown file",
         "Build a script that checks our pricing page every day and reports changes"],
    ),
    "mcp": (
        "Skills and MCP servers solve different problems, and many projects in this list combine them. An MCP server gives Claude Code "
        "new tools, such as access to a database, an API or an app, while a skill gives it instructions for doing a task well. The "
        "skills here help you build MCP servers, wire them into your workflow or use specific MCP tools effectively. MCP servers are "
        "added with <code>claude mcp add</code> or a shared <code>.mcp.json</code> file in your project; skills are folders copied into "
        "<code>~/.claude/skills/</code> or <code>.claude/skills/</code>. Before connecting a server, check what data it can read and "
        "write and which credentials it needs. Not sure which you need? Read "
        "<a href=\"/blog/claude-code-skills-vs-mcp-servers/\">Claude Code skills vs MCP servers</a>.",
        ["Scaffold an MCP server in TypeScript that exposes our REST API",
         "Explain which MCP tools are connected and what each one can access"],
    ),
    "game-dev": (
        "Game development skills help Claude Code work with game engines and asset pipelines: scaffolding projects in engines such as "
        "Godot or Unity, writing gameplay scripts, generating sprites and effects, and organizing an agent workflow for a small game "
        "team. Game projects mix code with large binary assets, so check whether a skill expects a particular engine version or asset "
        "tool before installing it. Agent-team skills split the work across roles such as designer, programmer and QA, which helps on "
        "larger prototypes but adds overhead to small ones. As with any generated code, run the game and play through the parts that "
        "changed: engines often accept scripts that still misbehave at runtime.",
        ["Scaffold a 2D platformer in Godot with a player controller",
         "Add a pause menu and save system to this game"],
    ),
}
