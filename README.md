# skills

My personal agent skills. Each folder is a self-contained skill following the open [Agent Skills](https://agentskills.io) format: a `SKILL.md` with `name` and `description` frontmatter, plus optional `references/`, `assets/` and `scripts/`. Nothing here depends on a specific agent.

| Skill | What it does |
|---|---|
| `audit-r-package` | Read-only audit of an R package: dependencies, code correctness, tests, docs, CRAN readiness |
| `fix-quarto-extension-repos` | Prepare a Quarto extension repo for the quarto-extensions registry |
| `html-short-video` | Build a short vertical promo video from a script with HTML/JS animation and record it to a seamless-looping MP4 |
| `quarto-revealjs-showcase` | Build a looping Quarto revealjs deck and capture it as MP4 |
| `tidy-pr` | Turn a messy working tree into logical commits and a GitHub PR |

## Install

Copy or symlink the skill folders into your agent's skills directory. For example:

```bash
# Claude Code
ln -s "$PWD"/{audit-r-package,fix-quarto-extension-repos,html-short-video,quarto-revealjs-showcase,tidy-pr} ~/.claude/skills/

# Other agents that read ~/.agents/skills
ln -s "$PWD"/{audit-r-package,fix-quarto-extension-repos,html-short-video,quarto-revealjs-showcase,tidy-pr} ~/.agents/skills/
```

Check your agent's documentation for where it looks for skills.

## Conventions

- Skills describe behavior in plain language and avoid agent-specific tool names or paths. Where a skill refers to its own files (for example a script), it uses `<skill-dir>`, the folder containing that `SKILL.md`.
- Steps that need sub-agents or parallel tasks say what to do when the agent doesn't support them.
- Tools the skills call (`git`, `gh`, `R`, `quarto`, `ffmpeg`, `python3`) are ordinary command-line programs.
