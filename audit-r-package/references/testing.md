# Checklist: Tests

Read every file in `tests/`. Correlate tests with `R/`: which functions have tests, which don't. Use `covr` output when available; otherwise reason about coverage from reading.

## Setup and structure

- `tests/testthat/` exists with a `tests/testthat.R` runner, and the runner is the standard boilerplate (not hand-modified).
- **testthat edition 3** is enabled (`Config/testthat/edition: 3` in DESCRIPTION). Older editions are a Suggestion to upgrade.
- testthat is in **Suggests**.
- Test files are named `test-*.R` and mirror `R/` files (`R/foofy.R` -> `tests/testthat/test-foofy.R`). Flag orphaned or catch-all test files.
- Each `test_that()` has a clear description and tests one behavior. Overly broad "kitchen sink" tests are harder to diagnose.

## `test_that()` descriptions

The description string is what a developer reads when a test fails, so a wrong description sends them looking in the wrong place. Audit descriptions two ways:

- **Description vs. the code inside it.** Read each `test_that("...")` and confirm the expectations actually exercise what the description claims. Copy-paste is the usual culprit: a block titled `"errors on negative input"` that actually tests positive input, a description naming function `foo()` while every expectation calls `bar()`, or a description mentioning a case (`"handles NA"`) that no expectation covers. A mismatch is a `Warning` in the Correctness track: either the description or the test is wrong, and you should say which looks stale.
- **Consistency across the whole package.** Look across all test files together, not one at a time. Tests that check the same kind of behavior should describe it the same way, and each description should be distinct enough to identify the block. Flag: near-duplicate descriptions for tests that check different things (so a failure report is ambiguous), the same behavior described inconsistently across files (`"returns a tibble"` vs `"output is a data frame"` vs `"gives correct class"` for the same check), and copy-pasted descriptions left unchanged after the test body was adapted for a different function. Report these as `Suggestion` (Conventions track) unless the inconsistency is actively misleading. Suggest a consistent phrasing pattern rather than listing every instance.

## Coverage and what's tested

- Every exported function has at least one test. An exported function with zero tests is a Warning.
- Tests target the external interface and behavior, not private implementation details (so refactors don't cascade).
- Edge cases, error paths, and known past bugs are tested (regression tests). Error paths use `expect_error(..., class = "...")` with a condition class, not brittle message regex.
- Report the coverage number if `covr` ran, and name the least-covered files. Don't fetishize 100% - flag genuinely risky untested code, not trivial getters.

## Parallelism across similar functions

Reading the code and the tests side by side is illuminating: a family of functions that do similar things should have similarly shaped, similarly thorough tests. Group functions that share a purpose (a family of `scale_*()`, `step_*()`, `read_*()` variants; S3 methods for the same generic; wrappers around a common core) and compare their test blocks against each other. Asymmetry is usually a gap, not a deliberate choice.

- If `foo()` tests empty input, `NA` handling, and an error path, but its sibling `bar()` only tests the happy path, `bar()` is probably under-tested for the same cases. Flag the specific missing cases (`Warning` in Correctness if the untested path is risky, otherwise `Suggestion`).
- Look for edge cases exercised for one member of a family and silently absent for the others, and for one function's tests being noticeably thinner or shallower than its peers'.
- Conversely, near-identical test blocks copy-pasted across a family are worth a `Suggestion` to factor into a shared helper or a loop over cases (a parameterized test), so the family stays in sync as it grows.

Frame these as "here's the coverage pattern across this family, and here's who's missing what" rather than a per-function verdict, so the user sees the asymmetry at a glance.

## Self-sufficiency and hygiene (r-pkgs "designing your test suite")

- **No top-level code** in test files outside `test_that()` - shared objects created at file scope create hidden inter-test dependencies. Setup belongs inside each test, in a `helper-*.R`, `setup-*.R`, or a local fixture function.
- **Self-contained**: any global-state change (options, env vars, working dir, files, attached pkgs) is wrapped in `withr::local_*()` so it's reverted. testthat 3e already applies `local_reproducible_output()`.
- Tests write only to a temp dir (`withr::local_tempfile()` / `local_tempdir()`), never into `tests/`, the working dir, or home. Writing into the repo is a Warning.
- Fixtures: static test data under `tests/testthat/fixtures/` accessed via `testthat::test_path()`; expensive objects saved as `.rds` with a documented, reproducible creation script.
- Helper vs setup files used correctly: `helper-*` runs under `load_all()` too; `setup-*` is for automated runs with paired teardown via `withr::defer(..., teardown_env())`.

## Snapshots, mocking, secrets

- Snapshot tests (`expect_snapshot()`) used for user-facing output/messages; snapshot `.md` files are committed and reviewed, not stale.
- Mocking kept minimal; when used, via `testthat::local_mocked_bindings` or a dedicated package (mockr, httptest2, webfakes) rather than ad hoc.
- No live credentials required to run the suite; secret-dependent tests skip cleanly when creds are absent.

## CRAN-safety

- Slow, flaky, network, or platform-specific tests are guarded: `skip_on_cran()`, `skip_if_offline()`, `skip_if_not_installed()`, `skip_on_os()`. Internet-touching tests must fail gracefully - a hard network dependency on CRAN is a Critical.
- Prefer `expect_equal()` (tolerance) over `expect_identical()` for floating-point results that vary across platforms.
- Full suite runs quickly (well under a few minutes); no reliance on parallelism or exact timing.
- No leftover processes, connections, or temp files after the suite.
