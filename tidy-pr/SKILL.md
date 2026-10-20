---
name: tidy-pr
description: >
  Take whatever state the working tree is in — unstaged edits, staged changes, a pile of
  uncommitted work — and turn it into a clean set of logical commits on a proper branch,
  then open a GitHub pull request describing the change. Use this skill whenever the
  user says "tidy-pr", "make a PR", "turn this into a PR", "open a pull request", or otherwise
  asks to wrap up their current work into a reviewable PR. It handles branching, splitting
  changes into meaningful commits, pushing, and creating the PR via the gh CLI.
---

# tidy-pr

Turn the current working state into a clean branch, logical commits, and a GitHub PR. The user invokes this when they've been hacking and now want their work packaged for review. Do the mechanical git/gh work for them, but make good judgment calls about commit boundaries and messaging so the result reads like it was done deliberately.

## Workflow

Work through these in order. Narrate briefly as you go so the user can follow along, but don't stop to ask permission at each step unless something is genuinely ambiguous or risky (see "When to pause").

### 1. Survey the state

Run these together to understand where things stand:

```bash
git status
git branch --show-current
git log --oneline -10
git diff --stat
```

From this figure out: the current branch, whether it's the default branch, what's changed (staged + unstaged + untracked), and what the repo's commit style looks like. Read the actual diffs (`git diff` and `git diff --staged`) so your commits and PR description describe what really changed, not a guess.

### 2. Get on the right branch

- **If already on a feature branch** (not `main`/`master`/default): stay there and commit onto it. This is the common case when the user has already branched.
- **If on the default branch**: create a new branch automatically. Name it descriptively from the change (kebab-case, e.g. `add-retry-logic`, `fix-null-check-in-parser`). Announce the name you chose. No need to ask first — just pick a sensible one.

Determine the default branch rather than assuming `main`:

```bash
git remote show origin | sed -n '/HEAD branch/s/.*: //p'
```

### 3. Commit in logical units

Group the changes into separate, meaningful commits rather than one dump. Related edits belong together, and unrelated concerns (a bug fix, a docs tweak, a refactor) belong in separate commits. If the whole change is small and cohesive, one commit is fine, don't split for the sake of splitting.

Lean toward a handful of commits rather than a coarse one or two. A feature usually has natural seams worth separating even when everything is "related": the core logic, the layer that exposes it, the tests, and any generated or mechanical output. Splitting along those seams makes the branch readable commit-by-commit, which is the whole point. Two commits for a substantial new feature is usually too few. As a rough feel, a new feature often lands as three to five commits; a small fix as one or two. Don't pad past what the change naturally contains, but don't collapse distinct layers together just because they ship together.

For example, a new function in an R package might split as: the internal implementation, then the user-facing step/wrapper that calls it, then its tests, then the regenerated docs and registration (`NAMESPACE`, `man/`, `NEWS.md`, `_pkgdown.yml`). Generated or mechanical output (regenerated docs, formatting-only churn, lockfile bumps) is especially worth isolating into its own commit so it doesn't drown the substantive diff.

Use `git add -p` or stage specific paths to build each commit deliberately. Include untracked files that are part of the change.

**Commit messages: plain imperative, no prefix.** Write the subject as a command describing the effect, capitalized, no trailing period, no `feat:`/`fix:` conventional-commit prefix.

- Good: `Add retry logic to the upload client`
- Good: `Fix off-by-one in the pagination cursor`
- Avoid: `feat: add retry logic`, `added retry logic`, `Updates.`

Keep the subject under ~72 chars. Add a body only when the *why* isn't obvious from the diff; otherwise the subject alone is enough.

Never use `git commit --amend`, `git rebase`, `git push --force`, or `git reset --hard` on existing history unless the user explicitly asks. This skill builds on top of what's there.

### 4. Push and open the PR

Push the branch (set upstream on first push):

```bash
git push -u origin <branch>
```

Then create the PR with the `gh` CLI. **If the repo has a `PULL_REQUEST_TEMPLATE`** (check `.github/`, `.github/PULL_REQUEST_TEMPLATE/`, or repo root), fill that out instead of the default structure below.

Otherwise keep the body lean: a short paragraph of prose explaining what changed and why, and that's it. No `## Summary` heading (the PR already has a title, so the heading just repeats itself).

Aim for two or three sentences, and err on the side of too short. The body's job is to orient a reviewer before they open the diff: what capability or fix this adds and why it's being done. It is not a narration of the implementation. Resist listing which functions or methods you added, which internal helper you tweaked, or the step-by-step of how it works, that's exactly what the diff shows, and repeating it in prose is the main way these bodies bloat. A design decision only belongs in the body when it's genuinely non-obvious and a reviewer would otherwise wonder "why did they do it this way?" (for example, choosing one algorithm over another the issue implied). When in doubt, cut it.

Don't enumerate changes as a bullet list either, the commits already do that. Reach for a short bullet list only when the change genuinely splits into a few distinct threads that are clearer separated than as prose.

Only add a `## Test plan` section when it genuinely helps a reviewer: when there's a non-obvious way to verify the change, a specific command worth calling out, or manual steps a reviewer would otherwise have to guess. For routine changes where the tests speak for themselves, skip it. Don't add a test-plan heading just to restate "run the tests" (see "When a test plan earns its place" below).

Create it, targeting the default branch:

```bash
gh pr create --base <default-branch> --title "<imperative title>" --body "$(cat <<'EOF'
<two or three sentences of summary prose: what changed and why>
EOF
)"
```

Use the same imperative style for the PR title as for commits. When there's a single commit, the title can mirror its subject.

### 5. Report

Give the user the PR URL that `gh pr create` prints, and a one-line recap of the branch name and commits you made.

## When a test plan earns its place

A test plan is worth adding only when it tells a reviewer something they couldn't easily infer. Ask yourself: would a reviewer look at this and think "how do I check this?" If the answer is obvious (the change adds tests that run in CI, or it's a docs tweak), leave it out. Including a section that just says "run the tests" adds noise, not signal.

When it does earn its place, make it real and specific:

- A particular test file or command that exercises the change, when the full suite would be overkill (e.g. `Rscript -e "devtools::test_active_file('R/foo.R')"` for an R package, `pytest tests/test_foo.py` for Python, a specific `npm run` script for Node).
- Manual verification steps the reviewer would otherwise have to reverse-engineer (render a vignette and check a section, hit an endpoint, reproduce a bug that's now fixed).
- Anything about the change that can't be caught by automated tests and needs a human to eyeball.

If you can't name something more useful than "the tests pass," that's the signal to omit the section entirely.

## When to pause and ask

Default to just doing the work. Only stop to check with the user when:

- The working tree mixes clearly unrelated efforts and you're unsure they belong in the same PR.
- There are changes that look accidental or sensitive (secrets, large binaries, `.env` files, unrelated generated output).
- No `origin` remote exists, or the repo isn't a GitHub repo (so `gh` won't work) — surface this instead of guessing.
- The user is on the default branch of a repo they may not own (e.g. a fork/upstream mismatch).

## Notes

- This skill assumes `git` and the `gh` CLI are installed and authenticated. If `gh auth status` fails, tell the user rather than falling back to a half-finished state.
- Don't invent changes or touch files outside what's already modified. Your job is to package existing work, not extend it.
