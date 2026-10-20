# Checklist: R source code

Read **every** file in `R/`. The recurring theme: package code runs in unpredictable contexts and at surprising times, so it must be self-contained, side-effect-free, and namespace-clean.

## Behavioral correctness: does the code do what it claims?

> For the full systematic method (enumerate every function/method, audit shared internals first, run the edge-case matrix, verify by running, and fan out to sub-agents where supported), follow `references/deep-code-review.md`. The notes below are the per-function checks that method builds on.

This is the most valuable part of the audit and the part only a careful reader can do. Package hygiene (below) is necessary but a package can pass R CMD check with flying colors and still compute the wrong answer. For each function, actually reason about what it does and compare that to what it promises. Findings here go in the **Correctness & CRAN** track, usually `Critical` or `Warning`, because a function that silently returns the wrong result is worse than one that errors.

Read the function body, then check three sources of "what it's supposed to do" against it:

- **Name vs. behavior.** The name is a promise. `select_top_5_vals()` should return the top 5 values, not the top 10, not the bottom 5, not "roughly the largest." Trace the logic (and any tests) and confirm it delivers exactly that. Watch for off-by-one errors (`>` vs `>=`, `head(x, n)` vs `head(x, n-1)`), reversed comparisons/sort order, hard-coded constants that contradict the name (a `_5_` function taking an `n` argument, or ignoring it), and names that have drifted from the implementation as the code evolved.
- **Documentation vs. behavior.** The roxygen title, description, `@param` descriptions, `@details`, and `@returns` must match what the code actually does. Flag: a `@param` that describes a default or accepted range the code doesn't honor; a `@returns` that claims a type/shape/length the function doesn't produce; documented edge-case behavior ("returns `NA` for empty input") that the code doesn't implement; examples in `@examples` whose stated or implied output doesn't match what the code would produce. Documentation drift is a real bug: users rely on the docs, so a mismatch is a defect in one or the other, and you should say which side looks wrong.
- **Known methods vs. reference.** When a function implements a named algorithm, statistical method, formula, or standard (e.g. a specific distance metric, a p-value adjustment, a resampling scheme, an established numerical recipe, an RFC/spec), verify the implementation is actually correct against the definition, not just plausible. Check the formula term by term, the normalization/denominators, degrees-of-freedom, edge/boundary handling, and whether it matches the method the documentation *says* it implements (a function documented as "Welch's t-test" must not be computing Student's). Where feasible, sanity-check against a known result or R's built-in (`stats::`) equivalent. Cite the reference definition you checked against in the finding.

Also apply ordinary code-review judgment while reading: logic bugs, unhandled edge cases (empty input, length-0 vectors, `NA`/`NaN`/`Inf`, all-missing, single-row data, zero-variance), silent recycling, integer overflow, floating-point comparison with `==`, and results that depend on input order when they shouldn't. Prefer to confirm suspicions by pointing at the exact line and, when the tooling is available, by running the function on a small input that exposes the discrepancy.

## Organization

- Files group related functions sensibly - not one giant file, not one function per file. File names describe contents.
- No non-`.R` files in `R/`. No subdirectories in `R/` (they're ignored).
- Helper conventions: small utilities in `R/utils.R`, package-doc + imports in `R/{pkg}-package.R`, `.onLoad`/`.onAttach` in `R/zzz.R`, load-order-sensitive setup in `R/aaa.R`.

## The big correctness hazards

- **No top-level code that does real work.** Any code in `R/` outside a function runs at *build time* and is frozen into the binary. Flag `system.file()`, `Sys.time()`, `Sys.getenv()`, option reads, `<-` capturing system state, or function aliasing (`foo <- pkgB::blah`) at top level. These should move inside functions (or use a wrapper) so they evaluate at run time.
- **No `library()`, `require()`, or `source()` inside `R/`.** Dependencies come from DESCRIPTION + namespace, not attach calls. This is a Warning bordering on Critical.
- **State-modifying calls must be restored.** `options()`, `par()`, `setwd()`, `Sys.setenv()`, `Sys.setlocale()`, `set.seed()`, `sink()`, opening connections/devices - each needs `on.exit(..., add = TRUE)` or a `withr::local_*()`/`with_*()` wrapper. Unrestored global-state changes are a real bug for users.
- **No writing to arbitrary locations at run time.** User files, home dir, or the installed package dir. Persistent data belongs under `tools::R_user_dir()`; scratch belongs in `tempdir()`.
- **Mutable package state** (caches, tokens) lives in a dedicated internal environment (`new.env(parent = emptyenv())`), not in `<<-` to package bindings (which are locked).

## Dependency usage

- External functions are reached via `pkg::fun()` or an explicit `@importFrom` - never assumed to be on the search path.
- Suggested packages are used conditionally: `rlang::check_installed()` / `requireNamespace("pkg", quietly = TRUE)` guards, with a graceful path if absent. Direct use of a Suggests package with no guard is a Warning.
- Prefer `requireNamespace()` over `require()` (which fails silently and late).

## Robustness and style

- Errors/warnings use `stop()`/`warning()` with clear messages, or better, `cli::cli_abort()` / `rlang::abort()` with condition classes so callers can catch them programmatically. Flag bare `stop("...")` in a package that otherwise uses cli/rlang.
- Input is validated near the top of exported functions; failures are informative.
- No `T`/`F` (use `TRUE`/`FALSE`), no `1:length(x)` (use `seq_along`/`seq_len`), no `sapply()` where a type-stable `vapply()`/`purrr` call is safer, no `attach()`, no `<<-` for control flow, no `:::` into other packages' internals.
- NSE functions that read data-frame columns declare globals (`utils::globalVariables()`) or use `.data`/`.env` pronouns to avoid "no visible binding" NOTEs.
- Code follows the tidyverse style guide (naming, spacing, `<-` assignment, ~80 col). Assess this yourself by reading the code and report as `Suggestion` - group recurring patterns rather than listing every instance. Don't run `lintr`/`styler`; you judge intent and readability better than a linter and won't drown the report in mechanical nits.
- Very long functions worth flagging as maintainability suggestions.

## Package hooks

- `.onLoad()` used for setup (not `.onAttach()`); `.onAttach()` only for startup messages, and those via `packageStartupMessage()` (suppressible), never `cat()`/`message()` at load.
- `.onLoad`/`.onAttach` don't do slow or network work, and don't change RNG state (wrap in `withr::with_preserve_seed()` if unavoidable).
- `.onUnload()` cleans up anything `.onLoad()` set up (e.g. `library.dynam.unload` for compiled code).

## Encoding

- `.R` files are ASCII; non-ASCII characters use `\uXXXX` escapes. Detect with `tools::showNonASCIIfile()`. Raw non-ASCII in source is a CRAN NOTE/portability risk.
