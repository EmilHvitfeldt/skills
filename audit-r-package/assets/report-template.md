# Audit report: {package} {version}

_Audited {date} against r-pkgs (2e), the tidyverse style guide, and CRAN policy._

## Executive summary

{One paragraph: what the package is, overall health, and the headline. Then the counts.}

| Severity | Correctness & CRAN | Conventions & polish |
|----------|-------------------:|---------------------:|
| Critical | 0 | - |
| Warning | 0 | 0 |
| Note | 0 | 0 |
| Suggestion | - | 0 |

**Tooling run:** R {version} · R CMD check: {n errors / n warnings / n notes} · tests: {n pass / n fail / n skip} · coverage: {xx%} · urlchecker: {clean/n issues}. {Note anything that could NOT be run and why.}

## Top priorities

1. {The single most important thing to fix, with location.}
2. {...}
3. {...}

---

## Track A — Correctness & CRAN (must-fix)

_Things that are wrong, will break for users, or block a CRAN submission. Ordered most-severe first._

### [Critical · Confirmed] {Short title}
- **Where:** `path/to/file.R:42`
- **Problem:** {What's wrong and why it matters.}
- **Evidence:** {The repro (small input -> wrong output vs correct output), or the reference/formula checked against. Required for correctness findings.}
- **Fix:** {Specific, actionable fix.}

### [Warning · Suspected] {Short title}
- **Where:** ...
- **Problem:** ...
- **Evidence:** {What argues for it; note it is not yet reproduced and the maintainer should confirm.}
- **Fix:** ...

_(Correctness findings carry a status: Confirmed / Confirmed via repro / Suspected. Continue: Warnings, then Notes. Group by area — metadata/deps, code, tests, docs, checks/infra — if there are many.)_

---

## Track B — Conventions & polish (recommended)

_tidyverse / r-pkgs idioms and quality improvements. Optional, but they make the package easier to maintain and more idiomatic._

### [Suggestion] {Short title}
- **Where:** ...
- **Rationale:** {Why this is the convention / what it buys you.}
- **Suggested change:** ...

---

## Method / function verdict table

Proof the code review was systematic: every method/algorithm and every exported function, with a verdict. Include the clean ones.

| Method / function | File | Reference checked | Verdict |
|-------------------|------|-------------------|---------|
| {e.g. borderline-SMOTE} | `R/bsmote_impl.R` | Han, Wang, Mao 2005 | **Bug — see Track A #1** |
| {e.g. SMOTE} | `R/smote_impl.R` | Chawla 2002 | Verified correct |
| ... | ... | ... | ... |

### Verified correct (no issue needed)

State what you checked and cleared, so nobody re-litigates it: {list the methods/functions confirmed correct against their references, and any notable edge cases you tested and found handled properly}.

---

## Area coverage

Confirm every area was inspected, so the reader knows nothing was skipped.

- **Metadata, dependencies, license:** {1-line status}
- **R source code:** {status; note how many R files read}
- **Tests:** {status; coverage}
- **Documentation (roxygen, vignettes, README, NEWS, pkgdown):** {status}
- **Checks & infrastructure (R CMD check, Git, CI, lifecycle, CRAN):** {status}

## Appendix: raw tooling output

<details>
<summary>R CMD check</summary>

```
{verbatim check output, or "not run — R not available"}
```
</details>

<details>
<summary>Test / coverage summaries</summary>

```
{summarized output}
```
</details>
