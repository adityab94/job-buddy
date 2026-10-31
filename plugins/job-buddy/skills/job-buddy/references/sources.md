# Where jobs come from

Six ways in. Each person switches on the ones that fit them in profile.md ("Sources").
The aim is to keep raw listings out of the conversation: filter first, read only what survives.

## 1. Indeed connector (official, optional)

Indeed's own Claude connector: `search_jobs` (search, location, country_code, job_type) and
`get_job_details` (job_id). No scraping, no blocking.

- One search per target title. Use the profile's place (e.g. "Dublin") and, if remote is
  accepted, a second search with location "remote". Use `job_type: fulltime` when the profile
  wants permanent roles.
- About 10 results per search, ~1k tokens. There is **no date filter**: drop anything older
  than the profile's recency setting yourself. Exception: a strong title match up to 90 days
  old may be kept, labelled "older, check it's still open".
- Job IDs only last for the session. Match duplicates on company + title, never on the ID.
- `get_company_data` gives salaries and employee ratings: use it for the salary check on
  Tier A roles with no stated salary, and for interview prep.
- Indeed's listings also feed Glassdoor, so there is no need to search Glassdoor separately.

## 2. JobDataLake connector (free, optional, tech and business roles)

A job-data MCP that reads ~25,000 companies' own career sites, refreshed hourly. Its tools
have their own names: `search_jobs` (JobDataLake's, not Indeed's), `get_job`, `get_company`,
`find_similar_jobs`, `get_filter_options`. Free: 500 calls a day, no account. The free pool
may be shared between users, so keep calls few; if it says the limit is reached, skip it.

What it adds that nothing else here does:
- **Workday career sites** (large employers: Salesforce, Mastercard, McKesson, ServiceNow…),
  which the collector can't read.
- **`find_similar_jobs`**: given a Tier A role found here, finds lookalikes. Use it after a
  search turns up a strong A.
- Real filters: `countries` (ISO, e.g. `IE`), `posted_within` (`24h`, `7d`, `30d`),
  `seniority`, `remote_type`, `employment_type`.

How to use it:
- One `search_jobs` per track, using the track's most distinctive keyword (short keywords
  match best: "revenue operations", not a full title), with `countries` set to the
  profile's country and `posted_within` matching the recency setting.
- Results are short (~150 tokens per job). The `ID` is a stable handle; still dedupe on
  company + title like everything else.
- **Recheck location.** Its location tags are sometimes wrong (a UK-only remote role came
  back tagged Ireland). Confirm from the full description before scoring.

Limits (tested 31 Oct 2026, Ireland): thin for niche business roles ("revenue operations" 2
jobs, "sales operations" 1, "GTM" 0) and nothing for health or most non-tech fields ("nurse"
0). Job categories are tech and business only, and its semantic search covers remote tech
roles only. So: switch it on for tech, data, sales/ops and big-company targets; leave it off
for health, public sector and research users.

## 3. Browser collector (free, built-in browser, Windows and Mac)

`scripts/collector.js`, shipped with this skill. It runs inside the Claude desktop app's built-in
browser, fetches public feeds, filters them in the page and returns short rows only.

How to run it:
1. Build CONFIG from profile.md: `include` = the track's target titles (lowercase),
   `exclude` = the track's exclude words, `places`, `remote`, `days`, `seen` (see below),
   `companies` (watchlist), `feeds` (remote feeds switched on), `builtin: true/false`,
   `jobsiePlace` (the user's town or county, e.g. `cork`, `galway`; default `dublin`).
   With several tracks, run once per track or merge the include lists and route afterwards.
2. Open `https://builtindublin.ie/jobs` in the built-in browser (any page on that site works,
   and it is only a host page: the watchlist and feeds work from it for users anywhere).
   Paste the contents of `scripts/collector.js` into one javascript call, followed by
   `await JSA.run(CONFIG)`. This covers the company watchlist, remote feeds and Built In Dublin.
3. If Jobs.ie is switched on: open `https://www.jobs.ie/`, paste the script again, then
   `await JSA.jobsie(CONFIG)`.
4. The result starts with `checked N | kept K | dropped {...}`, then:
   - `per source:` how many listings each source returned before filtering;
   - `BROKEN? 0 listings from: …` a feed or scraped site that returned nothing. That
     almost always means it broke (site redesign, feed down), not a quiet week;
   - `no openings: …` watchlist companies with no open jobs right now (normal);
   - `errors: …` sources that failed outright (a `404` usually means a wrong board ID);
   then one row per kept job: `source | company | title | location | age in days | link`.
   Tell the user in one line about every BROKEN or errored source, and suggest they report
   a source that stays broken on two runs (see **Report a problem** in SKILL.md).

**Where the user lives matters.** Built In Dublin is Dublin-only and Jobs.ie needs
`jobsiePlace`. For users outside Dublin, set `builtin: false` and `jobsiePlace` to their
town or county. For users outside Ireland, Built In Dublin and Jobs.ie don't apply: their
sources are the Indeed connector (with their country code), JobDataLake, the company
watchlist, remote feeds, job-alert emails and field-specific sites for their country.
Say this plainly at setup so a thin first search isn't a surprise.

First use of each site asks the user to allow it once in the built-in browser.

What the collector reads (all tested Oct 2026):

| Source | How | Notes |
|---|---|---|
| Greenhouse, Lever, Ashby, SmartRecruiters, Workable | Official public job-board APIs per company | Stable. Needs the company's board ID |
| Remotive, RemoteOK | Free remote-job APIs | RemoteOK asks for credit with a link |
| Arbeitnow | Free EU job API | Mostly Germany; leave off for Ireland unless relevant |
| Built In Dublin | Public search pages | Tech and startup roles in Dublin |
| Jobs.ie | Public search pages | Sister site of IrishJobs; strongest for non-tech fields |

Finding a company's board ID: open its careers page and look at where "Apply" links go:
`boards.greenhouse.io/<id>` or `job-boards.greenhouse.io/<id>`, `jobs.lever.co/<id>`,
`jobs.ashbyhq.com/<id>`, `jobs.smartrecruiters.com/<id>`, `apply.workable.com/<id>`.
An error like `404` for a company in the collector output means the ID is wrong or the
company moved board; tell the user and fix the watchlist.

If a site's layout changes, the collector flags it as BROKEN or reports an error. Say so in
one line; never report "no new roles" when a source failed.

## 4. Job-alert emails (Gmail connector, optional)

Covers LinkedIn, Indeed, IrishJobs and Glassdoor without scraping. The user sets up free
alerts on those sites for their titles and location. When the Gmail connector is connected,
search only alert senders (e.g. `from:(jobalerts-noreply@linkedin.com OR alert@indeed.com
OR irishjobs.ie) newer_than:7d`), pull title, company, location and link from each email,
then filter and score like any other row. If there is no Gmail, users can forward or paste
alert emails.

## 5. Pasted links and text (always on)

Any link or job text the user shares. Open the link; LinkedIn's public job page usually
works for a single job. If a page is blocked (Indeed or IrishJobs pages, sign-in walls),
ask the user to paste the job text instead. Never try to get past a security check.

## 6. Field-specific sites

Chosen during setup, read with the built-in browser like any public page:
publicjobs.ie (Irish public service), HSE and hospital group careers (health),
EURAXESS (research), gradireland (graduates), EURES (EU-wide), and niche boards the user
trusts (e.g. RevOps Careers for RevOps). Add new ones to the profile's Sources table.

## Not used

Live LinkedIn search, Indeed or IrishJobs page scraping, and paid scrapers. They break
site terms, get blocked, or cost money. Alerts, the Indeed connector and pasted links
cover the same jobs.

## The seen list

`seen.txt` holds roles screened out before scoring (`company|title|date`). Roles in the
tracker count as seen too. Pass the collector only keys from the last 60 days
(`company` lowercased with non-letters removed, `|`, title lowercased), so the list stays small.
Add every quick-score reject to seen.txt so it is never read twice.
