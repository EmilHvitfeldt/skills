---
name: fix-quarto-extension-repos
description: >
  Prepare a single Quarto extension repo for submission to the quarto-extensions registry
  (https://github.com/mcanouil/quarto-extensions) and register it on emilhvitfeldt.com.
  Checks and fixes missing GitHub description, topics, and releases — the three things the
  registry bot flags — then opens a PR to mcanouil/quarto-extensions and adds the extension
  to the appropriate page on emilhvitfeldt.com. Use this skill when creating a new Quarto
  extension, before submitting to the registry, or when the bot check summary flags issues
  for a specific repo.
---

# Prepare a Quarto Extension Repo for the Registry

This skill works through one extension repo end-to-end:

1. Fix GitHub metadata (description, topics)
2. Add Quarto Wizard support (`_schema.yml` and `_snippets.json`)
3. Create the release tag (so it points to a commit that includes the Wizard files)
4. Open a PR to [mcanouil/quarto-extensions](https://github.com/mcanouil/quarto-extensions)
5. Add the extension to [emilhvitfeldt.com](https://github.com/emilhvitfeldt/emilhvitfeldt.com)

Run this skill once per new extension, or any time the registry bot flags issues.

---

## Step 1: Gather upfront information

Before doing anything, collect what you need. Ask everything you can't reliably infer in
one go — don't drip-feed questions throughout the session.

> **Ask (if not already clear from context):**
> 1. Which repo? (just the name is fine, e.g. `quarto-timeline` — owner defaults to `emilhvitfeldt`)
> 2. Is this a RevealJS extension or a general/multi-format extension? (infer from the repo name if obvious — `revealjs` in the name = RevealJS — but confirm if ambiguous)

Then fetch the README to understand what the extension does — you'll need it to suggest a description:

```bash
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d | head -40
```

---

## Step 2: Check current GitHub metadata

```bash
gh api repos/OWNER/REPO --jq '{description: .description, topics: .topics}'
gh release list --repo OWNER/REPO --limit 1
```

Note exactly which of the three things are missing. Only fix what's actually absent.

---

## Step 3: Confirm and apply metadata changes

Based on what's missing, draft the proposed changes and **ask the user to confirm all of them
in a single message** before making any changes. Don't ask about description, then separately
about topics — bundle them.

Draft the following as needed:

- **Description:** a one-sentence description inferred from the README. Should say what the
  extension *does*, not just what it is. E.g. "Row-based layout extension for Quarto RevealJS slides."
- **Topics:** always `quarto`, `quarto-extension`; add `revealjs` for RevealJS extensions.
  Merge with any existing topics so nothing is dropped.

> **Ask:**
> "Here's what I'm going to set — let me know if you'd like to change anything before I apply it:
> - **Description:** `<suggested description>`
> - **Topics:** proposed merged list, e.g.:
>   - RevealJS extension: `quarto`, `quarto-extension`, `revealjs`
>   - RevealJS theme: `quarto`, `quarto-extension`, `revealjs`, `revealjs-theme`
>   - Shortcode extension: `quarto`, `quarto-extension`, `shortcodes`
>   - General extension: `quarto`, `quarto-extension`
>
> Good to go, or any changes?"

Wait for confirmation, then apply both.

### Apply description

```bash
gh api repos/OWNER/REPO -X PATCH -f description="Confirmed description here"
```

### Apply topics

Topic strategy — always include the base set, then add kind-specific tags:

**Base (all extensions):** `quarto`, `quarto-extension`

**Add by type:**
- RevealJS extensions: `revealjs`
- RevealJS themes: `revealjs`, `revealjs-theme`
- Shortcode extensions: `shortcodes`

Drop any `quartopub` / `quarto-pub` tags if present — these are legacy and add no value.

Fetch existing topics first, then merge so nothing is dropped:

```bash
# Get current topics as a starting point
gh api repos/OWNER/REPO/topics --jq '.names'

# Build the merged list (add required tags, drop legacy ones, keep the rest)
# Then apply:
gh api repos/OWNER/REPO/topics -X PUT \
  --input - <<'EOF'
{"names": ["quarto", "quarto-extension", "revealjs"]}
EOF
```

---

## Step 4: Quarto Wizard support

Quarto Wizard is a VS Code / Positron extension that provides autocompletion, hover docs, and
code snippets for Quarto extensions. Support requires two files placed inside the extension
folder alongside `_extension.yml` (e.g. `_extensions/REPO-NAME/_schema.yml`).

First, read the extension's structure to understand what to document:

```bash
gh api repos/OWNER/REPO/contents/_extension.yml --jq '.content' | base64 -d
gh api repos/OWNER/REPO/readme --jq '.content' | base64 -d
```

Also check if these files already exist (skip if so):

```bash
gh api repos/OWNER/REPO/contents/_extensions/REPO-NAME/_schema.yml 2>/dev/null
gh api repos/OWNER/REPO/contents/_extensions/REPO-NAME/_snippets.json 2>/dev/null
```

### `_schema.yml`

Documents the extension's options, shortcodes, and attributes for validation and IDE support.
See the full spec: https://m.canouil.dev/quarto-wizard/reference/schema-specification.html

Only include sections relevant to this extension (options, shortcodes, attributes, classes).
Always start with the `$schema` reference line.

### `_snippets.json`

VS Code snippet format. Provide one snippet per main use case.
See the full spec: https://m.canouil.dev/quarto-wizard/reference/snippet-specification.html

Prefix convention: `<extension-name>:<trigger>` (e.g. `iconify:icon`).

### Ask before creating

> **Ask:**
> "I'll create `_schema.yml` and `_snippets.json` for Quarto Wizard support. Here's what I'm
> planning to include:
> - `_schema.yml`: [list the sections — options / shortcodes / attributes / classes]
> - `_snippets.json`: [list the snippets by name]
>
> Does this look right, or anything to add/change?"

After confirmation, clone the repo locally if not already present, add the files, commit, and push:

```bash
# Clone if not already present
if [ ! -d ~/Github/REPO-NAME ]; then
  gh repo clone emilhvitfeldt/REPO-NAME ~/Github/REPO-NAME
fi

cd ~/Github/REPO-NAME
# Create the files at _extensions/REPO-NAME/_schema.yml and _snippets.json
git add _extensions/REPO-NAME/_schema.yml _extensions/REPO-NAME/_snippets.json
git commit -m "feat: add Quarto Wizard support"
git push
```

---

## Step 5: Create release tag

Create the release tag **after** the Wizard files are pushed, so the tag points to a commit
that already includes them. Only do this if no release exists (checked in step 2).

```bash
# Tags HEAD of the default branch
gh release create v0.1.0 \
  --repo OWNER/REPO \
  --title "v0.1.0" \
  --notes "Initial release." \
  --latest
```

---

## Step 6: PR to mcanouil/quarto-extensions

The registry is a plain-text file (`extensions/quarto-extensions.csv`) where each line is
`owner/repo-name`, sorted alphabetically. Adding an extension = inserting one line in the
right position.

Before opening the PR, tell the user what you're about to do and ask to proceed:

> **Ask:**
> "I'm about to open a PR to [mcanouil/quarto-extensions](https://github.com/mcanouil/quarto-extensions) adding `emilhvitfeldt/REPO-NAME`. Proceed?"

The PR title is standardized.

```bash
# Fork and clone if not already at ~/Github/quarto-extensions
if [ ! -d ~/Github/quarto-extensions ]; then
  gh repo fork mcanouil/quarto-extensions --clone --remote --clone-dir ~/Github/quarto-extensions
fi

cd ~/Github/quarto-extensions
git checkout main && git pull

git checkout -b add-REPO-NAME

# Insert the entry in alphabetical order among the emilhvitfeldt/ lines
# Check current position:
grep -n "emilhvitfeldt/" extensions/quarto-extensions.csv

# Edit the file to insert: emilhvitfeldt/REPO-NAME
# Then commit and push:
git add extensions/quarto-extensions.csv
git commit -m "chore: add emilhvitfeldt/REPO-NAME"
git push -u origin add-REPO-NAME

gh pr create \
  --repo mcanouil/quarto-extensions \
  --title "chore: add emilhvitfeldt/REPO-NAME" \
  --body "Adding emilhvitfeldt/REPO-NAME to the registry."
```

Print the PR URL when done.

---

## Step 7: Add to emilhvitfeldt.com

The repo lives at `~/Github/emilhvitfeldt.com`. Which file to update depends on extension type.

**First, check if the extension is already present** before asking any questions or making changes:

```bash
# For RevealJS extensions:
grep -n "REPO-NAME" ~/Github/emilhvitfeldt.com/project/slidecraft-101/index.qmd

# For general extensions:
grep -n "REPO-NAME" ~/Github/emilhvitfeldt.com/project/quarto-work/index.md
```

> **IMPORTANT — edit source files, not freeze caches.** The slidecraft-101 page has both
> `index.qmd` (the real source) and `index.html.md` (a Quarto *freeze cache* that is regenerated
> from the `.qmd`). Always edit `index.qmd`, then re-render so the cache regenerates correctly
> (see "Commit and push" below). Do **not** hand-edit `index.html.md`. The `quarto-work` page
> has only `index.md`, which *is* the source, so edit it directly.

If the entry is already there, skip this step entirely.

Before making changes, ask the questions relevant to the type:

### For RevealJS extensions → `project/slidecraft-101/index.qmd`

Cards in the `## Quarto Extensions` grid use a short friendly display name (e.g. "Rows",
"Transitions", "Tegaki") and a preview image (800×500px webp).

> **Ask:**
> 1. What should the display name be for the card? (e.g. "Rows" for `quarto-revealjs-rows`)
> 2. What is the preview image filename? (e.g. `rows.webp` — must be 800×500px webp, placed in `project/slidecraft-101/`)

Wait for both answers before proceeding. Do not add the card without an image.

Card format:

```
::: {.slidecraft-card}
[![](image-name.webp){fig-alt="DISPLAY NAME extension" loading="lazy"}](https://github.com/EmilHvitfeldt/REPO-NAME)

**[DISPLAY NAME](https://github.com/EmilHvitfeldt/REPO-NAME)**
:::
```

Add the card inside the `## Quarto Extensions` grid, keeping it grouped with the other cards.

### For general extensions → `project/quarto-work/index.md`

> **Ask:**
> What should the display name be for the list entry? (e.g. "quarto-arrows" → "quarto-arrows",
> or something friendlier if preferred)

Add under `## Extensions`:

```markdown
- [DISPLAY NAME](https://github.com/EmilHvitfeldt/REPO-NAME): One-sentence description
```

### Re-render (RevealJS / slidecraft-101 only)

After editing `index.qmd`, re-render so the freeze cache (`index.html.md`) regenerates and stays
consistent with the source:

```bash
cd ~/Github/emilhvitfeldt.com
quarto render project/slidecraft-101/index.qmd
```

Then `git status` to confirm both `index.qmd` and the regenerated `index.html.md` are staged.
(The `quarto-work` page is plain Markdown and needs no render.)

### Commit and push

Always commit directly to `main`:

```bash
cd ~/Github/emilhvitfeldt.com
# RevealJS: stage the source AND the regenerated freeze cache
git add project/slidecraft-101/index.qmd project/slidecraft-101/index.html.md project/slidecraft-101/IMAGE.webp
# General: just the markdown source
git add project/quarto-work/index.md
git commit -m "add REPO-NAME extension"
git push
```

---

## Step 8: Summary

Print a short recap of everything that was done:

- GitHub metadata: what was set (description / topics / release)
- Quarto Wizard: files added, or already present
- quarto-extensions PR: link
- emilhvitfeldt.com: what was updated and where

Everything should be complete at this point. If anything is missing, go back and handle it before summarising.
