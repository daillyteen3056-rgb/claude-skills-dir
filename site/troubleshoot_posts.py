"""Troubleshooting guides, appended to BLOG_POSTS by build.py."""

TROUBLESHOOT_POSTS = [
    {
        "slug": "claude-code-skill-not-loading",
        "title": "Claude Code skill not loading? 10 causes and how to fix each",
        "description": "Your skill does not show up in /skills or never runs. Check these 10 causes in order: wrong folder, frontmatter that is not on line 1, a new top-level skills folder, name clashes, cloud sessions and more.",
        "date": "2026-11-24",
        "html": """
<p>You copied a skill into place, typed <code>/</code> and it is not there. Or it is listed but Claude never uses it. Work down this list in order: the first causes are the most common.</p>
<p><strong>First, look at what actually loaded.</strong> Run <code>/skills</code> inside Claude Code. It lists every skill the session can see. If yours is missing, the problem is the folder or the file. If it is listed but never used, skip to cause 8.</p>

<h2>1. The folder is in the wrong place</h2>
<p>Claude Code reads skills from <code>~/.claude/skills/&lt;skill-name&gt;/SKILL.md</code> (personal, every project) and <code>.claude/skills/&lt;skill-name&gt;/SKILL.md</code> inside a project. A very common mistake is one folder too many or too few:</p>
<pre><code>~/.claude/skills/my-skill/SKILL.md            correct
~/.claude/skills/SKILL.md                     wrong: no skill folder
~/.claude/skills/my-skill/my-skill/SKILL.md   wrong: nested once too often (common after unzipping)</code></pre>
<p>When you clone a repository that holds several skills, copy the individual skill folder, not the whole repository. Every skill page on SkillNest shows a command that does this for you.</p>

<h2>2. The file is not called SKILL.md</h2>
<p>The file name is <code>SKILL.md</code>. Watch for <code>skill.md</code>, <code>Skill.md</code>, <code>SKILL.md.txt</code> (Windows hides known extensions by default) or a README that was never renamed.</p>

<h2>3. The frontmatter does not start on line 1</h2>
<p>Claude Code only reads the frontmatter if the opening <code>---</code> is the very first line of the file. A blank line, a title or a byte-order mark above it means the whole file, markers included, is treated as plain body text: the skill loads with no <code>name</code> and no <code>description</code>.</p>

<h2>4. The YAML does not parse</h2>
<p>If the frontmatter is not valid YAML the skill still loads, but with no fields set, so it has no description for Claude to match. The usual culprit is an unquoted colon in the description:</p>
<pre><code>description: Use this for: commit messages      # breaks YAML
description: "Use this for: commit messages"    # fine</code></pre>
<p>Paste your file into the <a href="/tools/skill-md-validator/">SKILL.md validator</a> to catch this and the next two causes in a second.</p>

<h2>5. The skills folder is brand new</h2>
<p>Adding, editing or removing a skill takes effect without a restart. The exception: if the top-level skills folder (for example <code>~/.claude/skills/</code>) did not exist when the session started, run <code>/reload-skills</code> after creating it.</p>

<h2>6. The name has characters Claude Code refuses</h2>
<p>Names and folder names with control or zero-width characters, leading or trailing spaces, or <code>&lt;</code> and <code>&gt;</code> do not load. Stick to the Agent Skills convention: lowercase letters, digits and hyphens, matching the folder name. <code>synced</code> is reserved as a folder name.</p>

<h2>7. Another skill with the same name wins</h2>
<p>When two skills share a name, enterprise beats personal and personal beats project. A personal skill also replaces a bundled command of the same name. If your project skill is "missing", check <code>~/.claude/skills/</code> for a twin.</p>

<h2>8. It loads but Claude never uses it</h2>
<p>Claude decides whether to load a skill from its <code>description</code>. A vague description ("helps with code") rarely matches a request. Start with what the skill does and the words a user would actually type, and keep it short: the description plus <code>when_to_use</code> is cut off at 1,536 characters in the skill listing. Two settings also stop automatic use on purpose: <code>disable-model-invocation: true</code> (only you can call it) and <code>skillOverrides</code> in settings. More in <a href="/blog/claude-code-skill-not-triggering/">why a skill doesn't trigger</a>.</p>

<h2>9. You are in a cloud or Cowork session</h2>
<p>Cloud and Cowork sessions do not read <code>~/.claude/skills/</code> on your computer. Put the skill in the project's <code>.claude/skills/</code> folder (committed to the repo) so it travels with the code.</p>

<h2>10. A nested skill has not been discovered yet</h2>
<p>Skills in a subfolder's own <code>.claude/skills/</code> (for example in a monorepo package) only load once Claude reads or edits a file in that subfolder. Until then they do not appear in <code>/</code>.</p>

<h2>Still stuck?</h2>
<p>Start Claude Code with <code>claude --debug</code> and search the log for the skill's name. Then compare your file against a skill that works, such as one from the <a href="/best/">best skills by topic</a>.</p>
""",
    },
    {
        "slug": "claude-code-skill-not-triggering",
        "title": "Why your Claude Code skill doesn't trigger (and how to write a description that does)",
        "description": "Claude picks skills by their description. How matching works, the 1,536-character cut-off, settings that switch auto-use off, and before/after examples of descriptions that trigger reliably.",
        "date": "2026-11-24",
        "html": """
<p>A skill that shows up in <code>/skills</code> but never runs on its own almost always has a description problem. Here is how Claude chooses, and how to write a description it can match.</p>

<h2>How Claude picks a skill</h2>
<p>Every turn, Claude sees a short listing of available skills: each skill's name and <code>description</code> (plus <code>when_to_use</code> if you set it). The full <code>SKILL.md</code> only loads once Claude decides a skill fits the request. So the description is the only thing Claude reads when choosing. If you leave it out, Claude Code falls back to the first non-empty line of the body, which is usually a title such as "# My Skill" and matches nothing.</p>

<h2>Rules for a description that triggers</h2>
<ul>
<li><strong>Lead with the job.</strong> The text is cut off at 1,536 characters in the listing, so the key use case goes first.</li>
<li><strong>Use the words people type.</strong> Name the file types, tools and verbs: "pytest", "Dockerfile", "commit message", "PDF form".</li>
<li><strong>Say when.</strong> "Use when the user asks to…" gives Claude a clear match condition.</li>
<li><strong>One skill, one job.</strong> Two skills with overlapping descriptions compete; split or merge them.</li>
</ul>

<h2>Before and after</h2>
<pre><code># Before: too vague to match anything
description: Helps with testing.

# After: says what, with which tools, and when
description: Write and fix pytest unit tests for Python code. Use when the user
  asks to add tests, raise coverage, or debug a failing pytest run.</code></pre>

<h2>Settings that switch automatic use off</h2>
<ul>
<li><code>disable-model-invocation: true</code> in the frontmatter: only you can run the skill with <code>/name</code>; Claude never picks it, and its description is left out of context.</li>
<li><code>skillOverrides</code> in settings can set a skill to <code>"user-invocable-only"</code>, <code>"name-only"</code> or <code>"off"</code>.</li>
<li><code>user-invocable: false</code> does the opposite: it hides the skill from the <code>/</code> menu but Claude can still use it.</li>
</ul>

<h2>Test it</h2>
<p>Ask for the task in plain words, the way a user would, without naming the skill. If Claude doesn't use it, add the missing words to the description and try again; edits to <code>SKILL.md</code> take effect without a restart. You can always force it with <code>/skill-name</code>.</p>
<p>Check the frontmatter itself with the <a href="/tools/skill-md-validator/">SKILL.md validator</a>, and see <a href="/blog/claude-code-skill-not-loading/">10 reasons a skill doesn't load</a> if it doesn't appear in <code>/skills</code> at all.</p>
""",
    },
    {
        "slug": "install-agent-skills-cursor-codex-claude-code",
        "title": "Install one skill in Claude Code, Codex and Cursor: 3 ways",
        "description": "Skills follow the open Agent Skills format, so one SKILL.md folder can serve several coding agents. Copy the folder, use the skills CLI, or add a plugin marketplace.",
        "date": "2026-11-24",
        "html": """
<p>Claude Code skills follow the open Agent Skills format: a folder with a <code>SKILL.md</code> file. Because the format is shared, the same skill can serve several coding agents. There are three ways to install one, and every skill page on SkillNest shows the commands that apply to it.</p>

<h2>1. Copy the folder (works everywhere)</h2>
<p>Clone the repository and copy the skill folder to the agent's skills directory:</p>
<pre><code>git clone --depth 1 https://github.com/OWNER/REPO.git ~/.claude/skills/my-skill   # Claude Code
cp -r ~/.claude/skills/my-skill ~/.codex/skills/                                  # Codex CLI</code></pre>
<p>If the skill sits in a sub-folder of a bigger repository, clone to a temporary folder and copy only that sub-folder. Windows users: see the <a href="/blog/install-claude-code-skills-windows/">Windows install guide</a>.</p>

<h2>2. The skills CLI (several agents at once)</h2>
<p>The open-source <code>skills</code> command-line tool installs from a GitHub repository and asks which agents to set it up for, including Claude Code, Cursor, Codex and Gemini CLI:</p>
<pre><code>npx skills add OWNER/REPO                    # every skill in the repo
npx skills add OWNER/REPO --skill skill-name # just one</code></pre>
<p>It needs Node.js. It keeps one copy of the skill and links it into each agent's folder, so updates reach all of them.</p>

<h2>3. A Claude Code plugin marketplace</h2>
<p>Some repositories ship a <code>.claude-plugin/</code> folder. That makes them a plugin marketplace you can add from inside Claude Code:</p>
<pre><code>/plugin marketplace add OWNER/REPO</code></pre>
<p>Then run <code>/plugin</code> to choose what to install. Plugin skills are namespaced, so they show as <code>/plugin-name:skill-name</code>. SkillNest marks repos that ship a marketplace with a "Plugin marketplace" label.</p>

<h2>Which one should you use?</h2>
<ul>
<li><strong>One agent, one skill:</strong> copy the folder. Nothing to install, easy to edit.</li>
<li><strong>Several agents:</strong> the skills CLI.</li>
<li><strong>A bundle you want to keep updated in Claude Code:</strong> the plugin marketplace.</li>
</ul>
<p>Whichever you choose, check that it loaded with <code>/skills</code>. If it didn't, see <a href="/blog/claude-code-skill-not-loading/">10 reasons a skill doesn't load</a>.</p>
""",
    },
]
