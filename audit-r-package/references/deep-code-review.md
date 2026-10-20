# Deep code review: finding the bugs a skim misses

This is the heart of a serious audit. R CMD check can be spotless and every test can pass while the package computes the wrong answer, because check validates *structure* and most test suites assert on *shape* (dimensions, class counts) rather than *values*. The bugs that matter live below that line. This file describes how to go deep enough to find them.

The governing mindset: a linear read finds the obvious 20%. To find the rest you must be **systematic** (account for every function/method, not just the interesting ones), **prioritize shared internals** (one bug there is many bugs), **probe edge cases deliberately**, and **verify by running**, not by eyeballing.

## 1. Enumerate, then account for everything

Before reviewing, build the inventory:

- Every **exported function** (from NAMESPACE) and every **internal function** of substance (helpers in `*_impl.R`, `utils.R`, `misc.R`).
- Every **named method / algorithm / formula / standard** the package claims to implement, and where (map each to its file and to the reference that defines it: a paper, an RFC, a textbook formula, or R's own `stats::` implementation).
- The **generics** and their methods (S3/S4), and which methods exist for which classes.

You will produce a verdict for **each** item: buggy (with a finding) or **verified correct against its reference**. This is what separates an audit from a spot-check. If you only report the handful of functions that looked off and stay silent on the rest, the reader can't tell whether you checked them or skipped them.

## 2. Audit shared internal machinery first and hardest

Find the choke points that many functions route through, and verify them line by line before touching leaf functions. Typical choke points:

- distance / similarity / kernel computations
- input validation and coercion helpers
- core numeric routines (whitening, normalization, weighting, aggregation, resampling)
- anything copy-pasted into several files

Two reasons this is highest-leverage. First, a bug here is a bug in every caller at once (the themis Mahalanobis wrong-Cholesky bug lived in one helper and corrupted every method offering that distance). Second, **duplicated machinery is a bug magnet**: when the same logic is pasted into 5 files, fixes and correctness drift apart across copies. Flag significant duplication itself as a maintainability finding (`Suggestion`, or `Warning` if the copies have already diverged in behavior), and check each copy separately because they may not match.

## 3. Verify named methods against their reference

For every algorithm/formula/standard, do not settle for "looks plausible". Check it against the definition:

- Reproduce the formula term by term: normalization, denominators, degrees of freedom, `n` vs `n-1`, `<` vs `<=` at boundaries, off-by-one in neighbor/self counts, sign/polarity, sort direction.
- Confirm it matches the method the **documentation claims** (a function documented as Welch's t-test must not compute Student's; a "majority vote" must actually take the mode over the right set).
- Distinguish **index/ordering consumers** from **magnitude consumers** of a computation. A transform can be monotonic (so ranking/neighbor selection stays correct) yet return wrong magnitudes (so any code that averages or thresholds the values is wrong). Check both kinds of consumer.
- Where feasible, sanity-check against a known-correct oracle: R's built-in equivalent, a tiny hand-computed example, or a second implementation inside the same package (siblings that do the same thing correctly are gold: use them as the reference and diff the logic).

## 4. Run the edge-case matrix against each function

These inputs expose silent data loss and cryptic errors, and they are exactly what the existing tests tend to omit. For each function, ask what happens with:

- empty input; a single row/element; length-0 and length-1 vectors (beware `sample(x)` treating a length-1 integer as `1:x`)
- unused / empty factor levels in the outcome or predictors (do targets computed from `table()` or `min(table())` go to zero? is `droplevels()` missing?)
- `NA` / `NaN` / `Inf`; all-missing columns
- zero variance; perfectly separable or degenerate groups; singular / collinear covariance
- duplicate rows (breaks "the point is its own nearest neighbor" assumptions)
- fractional, zero, negative, or out-of-range arguments (silently truncated? `round()` missing?)
- case weights / grouped data / other special columns the package might not handle but silently passes through (are they dropped, `NA`-filled, or errored on? does that match the docs?)
- ordering: does the result wrongly depend on input row order? (a classic `order()`-where-`rank()`-is-needed tell)

When a function guards against a bad input, confirm the guard fires *before* the code that would crash, and that the message is informative rather than a raw internal error.

## 5. Verify before reporting; tag the status

A correctness claim is only as good as its evidence. Before putting a bug in the must-fix track, confirm it and record how:

- **Confirmed** - reproduced directly (you ran it, or traced an unambiguous logic error to a specific line).
- **Confirmed via repro** - reproduced with concrete numbers (a small input, the wrong output, and the correct output side by side).
- **Suspected** - a strong code or paper-based argument you have not yet executed. Keep these clearly labeled and, if they'd be Critical/Warning, say the maintainer should confirm.

When R is available, prefer to actually run the exposing case: call internal functions with `pkg:::fn`, compare to a `stats::` oracle, print the disagreeing rows. Reproductions with numbers are far more convincing (and far less likely to be false positives) than prose.

## 6. Also sweep cross-cutting quality

Beyond individual functions, look across the whole surface:

- **API consistency.** Same concept, same argument name and default everywhere (e.g. don't have some functions take `k` and their siblings take `neighbors` for the same thing; don't let defaults silently differ). Argument order consistent across a family. Tunable/parameter declarations consistent across analogous functions.
- **Behavioral consistency across a family.** Functions that do analogous things should handle the same edge cases, validate the same way, and support the same features (if 9 of 10 samplers accept an `indicator_column` and one doesn't, that's likely an oversight, not a design choice).
- **Performance foot-guns.** O(n^2) work where an indexed/approximate path exists for the default but not for a non-default option; recomputation inside loops; dense matrices built for large inputs. Report as `Suggestion` unless egregious.
- **Dead / unreachable code**, no-op lines, constants that can never change, guards that never trigger.
- **Committed junk**: stray `testthat-problems.rds`, `.RData`, `.Rhistory`, editor backups, build artifacts checked into git. Flag and recommend removing + gitignoring.

## 7. Fan out for anything but a tiny package

One agent reading dozens of files in a single pass cannot go as deep as many focused reviews. Delegate if your agent supports sub-agents or parallel tasks (otherwise work through the same units one at a time, each with the same brief). Spawn parallel sub-agents, one per `*_impl.R` file, per method family, or per generic-plus-methods, each with this brief:

> Deep-review `<file/function>`. Identify the method/algorithm it implements and the reference that defines it. Verify the implementation against that reference term by term. Run the edge-case matrix (empty, single-row, length-1, unused factor levels, NA/Inf, zero-variance, duplicates, separable, fractional args, case weights). For any bug, reproduce it with concrete numbers (run the code; compare to a `stats::` oracle or a correct sibling) and tag it Confirmed / Confirmed via repro / Suspected. Also report anything you verified as correct. Return findings with `file:line`, evidence, severity, and a specific fix.

Then aggregate: de-duplicate overlapping findings, reconcile status tags, and assemble the per-method verdict table (including the verified-correct entries) for the report.
