# Changelog

## 0.6.0 (31 Oct 2026)

- **Dashboard.** A friendly `dashboard.html` in your folder: headline numbers, what needs your
  attention (deadlines, interviews, quiet applications, Tier A roles to apply for), a pipeline
  board, whether your rubric works, your top gaps and closed roles. Works offline, sends
  nothing anywhere, light and dark mode, fits a phone. Refreshes whenever the tracker changes.
- **Gap plan.** Each score now records the gaps that cost points. Ask "what should I learn?"
  and Job Buddy re-scores every role as if you had each missing skill, then shows which one
  moves the most open roles up a tier, with an honest plan to close it.
- **Fix:** scores ending in .5 now round up (72.5 → 73). Python's default rounding sent them
  down to the even number, which could drop a role a tier.

## 0.5.1 (31 Oct 2026)

- Tailoring is stricter about honesty: no numbers worked out from dates ("7 years"), no claims
  stretched past what the CV says, and a final line-by-line check against the CV. Found by the
  eval suite: before this fix, tailoring with Job Buddy scored worse on honesty than without it.
- The skill now triggers reliably on quick "score this role" requests, even with a profile
  pasted in the message.
- Eval fix: the assessment-invite test used a deadline on the wrong weekday.

## 0.5.0 (31 Oct 2026)

- **Shared Ireland feed.** A daily job reads ~30 employers' public job boards (Stripe, Intercom,
  MongoDB, Harvey, OpenAI, Anthropic, Tines, Wayflyer…) and publishes one file. The collector
  reads it with `feed: true`, so most users no longer need to look up board IDs. Broken boards
  open a "Feed health" issue automatically.
- **Scores you can check.** Each dimension now cites a word-for-word quote from the job ad,
  saved in the new `jds/` folder. A core script (`scripts/jb.py`) does the arithmetic and tiers,
  and flags any quote that isn't really in the ad. Confidence and near-cut-off warnings come
  from the same check.
- **Reliable tracker.** All tracker writes go through the core script: matching on company +
  role, IDs, dates and the Applied?/Callback? formulas. The blank tracker now has those formulas
  pre-filled (they were missing, so the Funnel sheet stayed empty for new users).
- **Safe upgrades.** Workspaces carry a version number. Older folders are backed up and upgraded
  automatically on first use.
- **Safer with untrusted text.** Job ads, emails and pages are treated as data, never as
  instructions; scam-style recruiter emails are called out. Two new evals test this.
- Location matching also looks for Irish places in job titles ("Remote - Ireland").

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
