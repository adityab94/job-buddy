# Changelog

## 0.4.0 (31 Oct 2026)

- The browser collector now reports how many listings each source returned, and flags a
  feed or site that returned nothing as possibly broken, so a broken source is never
  mistaken for a quiet week.
- Jobs.ie can search any town or county (`jobsiePlace`), and setup explains which sources
  apply to users outside Dublin or outside Ireland.
- New "report a problem" step: Claude writes a short diagnostic with nothing personal in it,
  for a GitHub issue. Added issue templates and a troubleshooting page.
- Added a test suite (`evals/`) for scoring, honest tailoring and reading recruiter emails.
- Added a GitHub check that validates the plugin, matching versions and the skill zip.

## 0.3.1 (31 Oct 2026)

- JobDataLake added as an optional, free connector for tech, data and sales/ops roles
  (big employers' own career sites, including Workday, and "find similar jobs").

## 0.3.0 (31 Oct 2026)

- First public release: role tracks, two-pass scoring, seen list, browser collector,
  Indeed connector, tailoring and application tracker.
