---
name: audit-r-package
description: Perform a comprehensive, read-only audit of an R package covering absolutely everything - DESCRIPTION and dependencies, NAMESPACE, R/ source code, tests, documentation (roxygen, vignettes, README, NEWS, pkgdown), licensing, R CMD check results, test coverage, and development infrastructure (Git, CI, CRAN readiness). Goes beyond package hygiene to verify behavioral correctness: reads each function to confirm it actually does what its name and documentation claim, and checks that known algorithms/statistical methods are implemented correctly and consistently with their docs. Runs available tooling (R CMD check, tests, covr, urlchecker) when R is installed and falls back to static analysis otherwise. Produces a severity-tagged Markdown report that separates correctness/CRAN must-fixes from tidyverse-convention suggestions. Use this skill whenever the user asks to audit, review, assess, health-check, or "look at everything in" an R package, whether preparing for a CRAN release, taking over maintenance, evaluating a dependency, or hardening a package they wrote. Trigger it even when the user just says "review my R package" or points at a package directory and asks what could be improved.
---

# Audit an R package

This skill drives a thorough, **read-only** audit of an R package. The goal is to look at *everything* and report findings, not to change any files. Fixing is a separate, later decision for the user.

The standards here come from the r-pkgs book (2e), the tidyverse style guide, and CRAN policy. Findings are split into two tracks so the user can tell must-fix from nice-to-have:

- **Correctness & CRAN** - things that are wrong, will break, or block a CRAN submission.
- **Conventions & polish** - tidyverse / r-pkgs idioms and quality improvements that are recommended but not required.

## Guardrails

- **Never modify the package.** No edits, no `styler`, no `document()`, no writing into the package tree. The only file you create is the audit report, and it goes *outside* the package (or in a clearly ignored location) unless the user says otherwise.
- **Read absolutely everything.** Do not sample. Every `.R` file, every test file, every doc, the full `DESCRIPTION` and `NAMESPACE`. A partial audit that misses a whole file is a failed audit.
- **Prefer real tooling over guessing.** When R and a tool are installed, run it and report actual output. Only fall back to static reasoning when a tool is unavailable, and say so in the report.
- **Attribute severity honestly.** Do not inflate style nits into "critical". Do not bury a real bug under a pile of formatting notes.

## Workflow

### 1. Locate and identify the package

Find the package root (the directory containing `DESCRIPTION` with a `Package:` field). If the user didn't point at one, look in the current directory and immediate subdirectories. Confirm the target with the user only if it's ambiguous.

Read `DESCRIPTION` to get the package name, version, and declared dependencies. Note the lifecycle signal from the version number (e.g. a `.9000` dev suffix, or `< 1.0.0`).

### 2. Take inventory

List the full file tree (respecting that some dirs may be large). Build a checklist of what's present vs. what a healthy package would have:

`DESCRIPTION`, `NAMESPACE`, `R/`, `man/`, `tests/`, `vignettes/`, `data/`, `data-raw/`, `inst/`, `src/`, `README.md`/`README.Rmd`, `NEWS.md`, `LICENSE`/`LICENSE.md`, `.Rbuildignore`, `.gitignore`, `_pkgdown.yml`, `.github/workflows/`, `cran-comments.md`, `codemeta.json`.

Note conspicuous absences (e.g. no tests, no README) and conspicuous surprises (e.g. hand-edited `NAMESPACE`, files in `R/` that aren't `.R`, top-level scripts).

### 3. Detect the toolchain and run available tooling

Check what's available, then run what you can. Capture the real output; summarize it in the report.

```bash
# Is R available, and what version?
Rscript -e 'cat(R.version.string, "\n")'
# Which audit-relevant packages are installed?
Rscript -e 'installed <- rownames(installed.packages()); cat(intersect(c("devtools","roxygen2","testthat","covr","urlchecker","pkgdown","desc","pak"), installed), sep="\n")'
```

When the tools exist, run (from the package root; each is independent so batch them):

- **R CMD check** - the single most important signal. `Rscript -e 'devtools::check(document = FALSE, args = "--no-manual")'` (or `R CMD check` on a built tarball). Record every ERROR / WARNING / NOTE verbatim.
- **Tests** - `Rscript -e 'devtools::test()'` (or `testthat::test_local()`). Record pass/fail counts, warnings, and skips.
- **Coverage** - `Rscript -e 'covr::package_coverage()'` then per-file coverage. Flag untested files/functions.
- **URLs** - `Rscript -e 'urlchecker::url_check()'` for broken/redirecting links.
- **Spelling** - check it yourself while reading the docs, README, NEWS, and roxygen prose. Don't shell out to the `spelling` package; you catch real typos and awkward wording more reliably and without its wordlist false positives.
- **Dependency footprint** - `Rscript -e 'pak::pkg_deps_tree(".")'` or parse DESCRIPTION to characterize the dependency load.

If R is not installed, do all of the above statically as far as possible (e.g. read tests and reason about coverage gaps) and clearly mark in the report that tooling could not be run.

These runs can be slow. Launch the heavy ones (check, coverage, revdep) with a generous timeout, or in the background, and continue with static review while they run.

### 4. Walk every area against the checklists

Go area by area. For each, read the relevant reference file for the detailed checklist, then read the actual package files and record findings. Read the reference files as you reach each area, not all upfront.

| Area | What it covers | Reference |
|------|----------------|-----------|
| Metadata, dependencies, license | `DESCRIPTION`, `NAMESPACE`, Imports/Suggests/Depends, versioning, `person()`, license files | `references/description-deps-license.md` |
| R source code | `R/` organization, side effects, build-time vs run-time, error handling, style, `.onLoad` | `references/code.md` |
| **Code correctness (deep)** | **Systematic per-method verification against references, shared-machinery audit, edge-case matrix, API/behavioral consistency; the highest-value part, see step 4b** | `references/deep-code-review.md` |
| Tests | testthat setup & edition, structure, coverage, fixtures, flakiness, CRAN-safety | `references/testing.md` |
| Documentation | roxygen completeness, examples, `@returns`, vignettes/articles, README, NEWS, pkgdown | `references/documentation.md` |
| Checks & infrastructure | R CMD check triage, Git/GitHub, CI, lifecycle, CRAN readiness | `references/checks-infra-cran.md` |

### 4b. Go deep on code correctness (this is where the real bugs are)

A single linear read finds the bugs that jump out and misses the rest. The findings that matter most (a wrong formula in a shared helper, an edge case that deletes all rows) are usually *not* obvious on a skim.

**This step gets the majority of the audit's effort.** The five areas in step 4 are not equal peers: a wrong answer in the package's core methods matters far more than a stale badge, so weight your time accordingly. And treat the deep review as **unbounded, not a checklist to tick off**: the goal is not to complete a list of checks, it is to keep digging (function by function, edge case by edge case) until every method has been verified against its reference or found wanting. You are not done when the checklist is covered; you are done when there is nothing left to verify. See `references/deep-code-review.md` for the full method; the essentials:

- **Enumerate first, then account for everything.** List every exported function and every named method/algorithm the package implements. You will record a verdict for *each* one (buggy, or verified-correct-against-reference), so nothing is skipped opportunistically. An audit that reviews the 4 functions that looked interesting and ignores the other 20 is not done.
- **Audit shared internal machinery first, and hardest.** Helpers that many functions route through (distance/similarity code, input validation, resampling or aggregation cores, math utilities) are the highest-leverage place to look: one bug there is a bug in every caller. Find these choke points and verify them line by line before the leaf functions.
- **Run the edge-case matrix against each function.** Empty input, single row, length-0/length-1 vectors, unused factor levels, all-`NA`/`NaN`/`Inf`, zero variance, duplicate rows, separable/degenerate groups, fractional or out-of-range arguments, case weights. These are exactly the inputs that expose silent data loss and cryptic errors, and they rarely appear in the existing tests.
- **Verify, don't speculate.** Before reporting a correctness bug, confirm it: trace the exact failing case and, when R is available, run the function on a small input that exposes the discrepancy (compare against a reference like a `stats::` equivalent or the paper's formula). Tag each correctness finding with a status: **Confirmed** (reproduced here), **Confirmed via repro** (reproduced with concrete numbers), or **Suspected** (strong code/paper argument, not yet run). This keeps false positives out of the must-fix track.
- **For anything but a tiny package, fan out.** Delegate deep per-file or per-family review to parallel subagents (one per `*_impl.R` file, per method family, or per generic and its methods). Give each the same brief: identify the method implemented, verify it against its reference, run the edge-case matrix, reproduce any bug with numbers, and report findings with a status tag. Then aggregate and de-duplicate. This is the single biggest lever for matching a max-effort manual review; one agent reading 37 files in one pass cannot go as deep as 37 focused reviews.

Record what you verified as correct, not just what's broken. A "Verified correct" list proves the sweep was systematic and stops good code from being re-litigated later.

### 5. Compile the report

Write the report using `assets/report-template.md` as the structure. Save it **outside the package tree** by default (e.g. `../<pkg>-audit-report.md` or the scratchpad), and tell the user the path. If they want it inside the package, add it to `.Rbuildignore`.

Every finding gets:
- a **severity**: `Critical` (broken/blocks CRAN), `Warning` (likely problem), `Note` (minor/CRAN NOTE-level), `Suggestion` (convention/polish);
- a **track**: Correctness & CRAN, or Conventions & polish;
- for correctness findings, a **status**: `Confirmed` / `Confirmed via repro` / `Suspected` (see step 4b);
- a concrete **location** (`file:line` where possible), the **evidence** (the repro or reference checked), and a **specific fix**, not a vague gesture.

Order findings most-severe first within each track. Include the **Verified correct** list from step 4b so the reader can see what was checked and cleared. End with a short prioritized "what I'd fix first" list, and note anything left `Suspected` that the maintainer should confirm.

### 6. Summarize in chat

Give the user a short summary: package name/version, overall health, counts by severity, the top 3-5 things to address, and the report path. Keep the exhaustive detail in the file.

## Severity rubric

- **Critical**: R CMD check ERROR, failing tests, missing license, code that will error for users, undeclared dependency, a function that corrupts user state.
- **Warning**: R CMD check WARNING, missing `@returns` on exports, no tests for exported functions, `library()`/`require()` inside `R/`, broken examples.
- **Note**: R CMD check NOTE, spelling, minor doc gaps, missing `NEWS.md`, non-ASCII without escapes.
- **Suggestion**: style-guide deviations, file organization, dependency trimming, pkgdown niceties, badges.

When unsure whether something is required or merely recommended, put it under **Conventions & polish** and say why it's optional.
