# Checklist: Checks, infrastructure, lifecycle, and CRAN readiness

## R CMD check triage

The output of `R CMD check` (via `devtools::check()`) is the backbone of the audit. Record and classify every result:

- **ERROR** -> Critical, always. Fix regardless of CRAN plans.
- **WARNING** -> Critical/Warning. Must be gone for CRAN; investigate otherwise.
- **NOTE** -> Note. Aim for zero for CRAN; explain any that remain.

For each finding, give the exact check that emitted it and the concrete cause. Common ones and their real fix:
- "no visible binding for global variable" -> NSE columns; use `.data`/`.env` or `utils::globalVariables()`.
- "Undefined global functions or variables" / "'::' or ':::' import not declared" -> add the package to Imports and use `::` or `@importFrom`.
- "checking dependencies in R code ... namespace ... not imported from" -> declare the dependency.
- non-ASCII, missing `@returns`, undocumented arguments, examples that error, unstated vignette deps -> see the code/documentation checklists.
- These NOTEs are acceptable and need no fix: the "New submission" NOTE on a first release, and the marked-UTF-8-strings NOTE for data.

If R isn't installed, say so and note that the check-based findings are inferred, not verified.

## Git and GitHub

- The package is under version control (a `.git` dir). If not, that's a foundational Suggestion.
- `.gitignore` sensibly ignores `docs/`, `.Rproj.user`, `*.Rproj` (or not, by preference), `.Rhistory`, `.RData`, build artifacts.
- `.Rbuildignore` excludes non-package files from the bundle: `^.*\.Rproj$`, `^\.Rproj\.user$`, `README.Rmd`, `LICENSE.md`, `_pkgdown.yml`, `docs`, `data-raw`, `\.github`, `cran-comments.md`, `revdep`. Remember patterns must be **anchored** (`^foo$`) or they match substrings everywhere.
- No large/generated/secret files committed (data blobs, credentials, `.Rproj.user`). Flag any secret material immediately as Critical.
- No stray junk checked into git: `tests/testthat/testthat-problems.rds` (leftover from a failed test run), `.RData`, `.Rhistory`, editor backups, build artifacts. Flag and recommend removing + gitignoring.
- URL/BugReports in DESCRIPTION point at the actual repo.

## Continuous integration

- `.github/workflows/` contains an `R-CMD-check` workflow (ideally the `r-lib/actions` `check-standard` matrix across Linux/macOS/Windows and multiple R versions). No CI at all is a Warning for a package intended for distribution.
- Additional useful workflows: `test-coverage`, `pkgdown`, `pr-commands`. Note their presence/absence.
- Workflows aren't obviously broken/pinned to abandoned actions; the README badge reflects real status.

## Lifecycle and versioning

- Version number tells a coherent story (dev suffix `.9000` during development; bumped appropriately for the change type - patch for fixes, minor for features, major for breaking changes).
- Breaking changes are handled with deprecation, not silent removal: `lifecycle::deprecate_warn()`, lifecycle badges, `deprecated()` defaults + `lifecycle::is_present()`. Superseded (not removed) legacy functions are fine and should stay documented.
- Public API stability matches the stated lifecycle stage; experimental parts are labeled.

## Data and other components

- `data/` objects each in their own `.rda` (via `usethis::use_data()`), documented, with a reproducible `data-raw/` script (`.Rbuildignore`d). Datasets sized within CRAN's ~1MB guidance; oversized data suggests a separate data package.
- Internal data in a single `R/sysdata.rda`; raw example files in `inst/extdata/` accessed via `system.file(..., mustWork = TRUE)` or `fs::path_package()`.
- `inst/` subdirs don't shadow official names (`inst/data`, `inst/man`, etc.).
- `src/` (if present): declared `SystemRequirements`/`LinkingTo`, registered native routines, `useDynLib`, and `.onUnload` unloading the DLL. (Deep C/C++ review is out of scope; flag the structural essentials.)
- `inst/CITATION` present for citable packages; consider `codemeta.json`.

## CRAN readiness (if a release is the goal)

- Clean `R CMD check` locally **and** on `devtools::check_win_devel()` and CI across OSes.
- `cran-comments.md` exists documenting check results and any NOTE explanations.
- `urlchecker::url_check()` clean.
- Reverse-dependency check (`revdepcheck::revdep_check()`) run for packages with downstream users; breaks communicated with lead time.
- First submission extras: `@returns` + `@examples` on all exports, `cph` in Authors@R, no `\dontrun{}` hiding broken examples, policy review at cran.r-project.org/web/packages/policies.html.
- Releases spaced per policy (roughly 1-2 months apart).
