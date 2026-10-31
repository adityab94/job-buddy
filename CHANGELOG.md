# Changelog

## 0.8.2 (31 Oct 2026)

- The Buddy Social icon for the plugin listing (`assets/icon.png`, 1024px, circular).
- The dashboard logo now ships as a plain image file (`scripts/logo-mask.png`) instead of
  text embedded in a script. The dashboard looks the same.

## 0.8.1 (31 Oct 2026)

- Privacy policy ([PRIVACY.md](plugins/job-buddy/PRIVACY.md)), linked from the plugin manifest
  and README, for the Claude plugin directory.
- The browser collector never sends cookies when it fetches job listings.

## 0.8.0 (31 Oct 2026)

- **30-day learning plans.** "What should I learn?" now ends with a plan for the top gap: what
  "good enough to interview" means, four weekly milestones, a project you build to prove it,
  and free resources that are checked to exist (no guessed links).
- **Stronger CVs, still honest.**
  - A short numbers interview: Job Buddy asks for the two to four figures that would make your
    bullets stronger and saves your answers for next time. It never invents numbers, even if
    asked for "a measurable achievement in every bullet".
  - Duties rewritten as outcomes, result first where there's a real result.
  - Tailored to the kind of employer (startup, scale-up, large company, public sector).
  - A recruiter skim test before you see it.
  - Page length: 1 page under 7 years' experience (1.5 with good reason), up to 1.5 pages
    from 7 years; margins no tighter than about 1.5 cm and text no smaller than 10 pt.
- **Sharper cover letters.** Built around the role's top three needs, one proof per need,
  about 200 words (250 at most), a specific ask instead of "I look forward to hearing from you".
- Three new evals guard against invented numbers, guessed links and generic closes.

## 0.7.0 (31 Oct 2026)

- **10-minute quick start.** Drop in your CV, say what you want and where, and see your first
  three matches scored for you, then tune Job Buddy by rating eight jobs great, okay or no.
  Plain words throughout, sensible job sites switched on for you, progress shown as
  "Step 1 of 3". New [START-HERE.md](START-HERE.md) guide for beginners.
- **A much stronger rubric.**
  - Built from the real market: 15-25 current ads for your role, with every "can I get it"
    requirement showing how many ads ask for it (`jb.py market`).
  - Two scores: "Can I get it?" and "Do I want it?". A great match needs both, so a dream job
    you can't land and an easy job you'd hate no longer look alike.
  - An automatic quality check (`jb.py rubric --check`): weights, vague descriptions,
    overlapping parts, deal-breakers counted twice, missing evidence.
  - Calibration on eight real roles you rate (`jb.py calibrate`): at least 7 in 8 must agree
    before the scoring is trusted; until then every score is marked "first draft", including
    on the dashboard.
- Workspaces upgrade to version 2 automatically (backed up first): the tracker gains Get Score
  and Want Score columns. Existing one-score rubrics keep working, and Job Buddy offers to
  rebuild them with the new method.

## 0.6.0 (31 Oct 2026)

- **Dashboard.** A friendly `dashboard.html` in your folder, designed in The Buddy Social's
  palette: frosted-glass panes over a cream-to-sage gradient, with the logo at the top. It shows
  what needs you next (deadlines, interviews, quiet applications, Tier A roles to apply for), your
  numbers at a glance, a pipeline board, whether your scoring works, what to learn next and
  closed roles. Light by default with a dark-mode toggle; works offline, sends nothing anywhere,
  fits a phone. Refreshes whenever the tracker changes.
- **Personal.** The dashboard greets you by first name for your time of day ("Good morning,
  Aditya"), tells you which week of your search you're in, and leads with what matters most
  right now: an offer, an interview, or your best match waiting. Only your first name is used.
- **Dashboard in your Claude sidebar (optional).** Say yes at setup and Job Buddy publishes the
  dashboard as a private page in your own Claude account: always one click away, on your phone
  too, and updated after every change. It holds only what the dashboard shows, never your CV or
  notes. The local file still works for anyone who prefers it.
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
