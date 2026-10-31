# CLAUDE.md: Job Buddy

Context for Claude Code working in this repo. Read this first.

## What this is

**Job Buddy** is a Claude plugin (by Aditya Bhatnagar, The Buddy Social) that runs a person's job
search from a local folder: it builds a scoring rubric for their field, finds roles, scores them
0–100 (tiers A/B/C), tailors CVs and cover letters honestly, and keeps an application tracker.
Audience: job seekers in any field (Ireland/EU default), many non-technical, on Windows or Mac.
Repo: https://github.com/adityab94/job-buddy · Licence: MIT · Current version: 0.3.1

## Repo layout

```
.claude-plugin/marketplace.json        repo = plugin marketplace (name: job-buddy)
plugins/job-buddy/
  .claude-plugin/plugin.json           plugin manifest (name job-buddy, author "Aditya Bhatnagar (The Buddy Social)")
  CONNECTORS.md                        optional connectors: Indeed (official), Gmail (job-alert emails)
  README.md
  skills/job-buddy/
    SKILL.md                           the workflow Claude follows (setup, tracks, find, score, tailor, track, review)
    references/                        rubric-design.md, sources.md, tailoring.md, outcomes.md (read on demand)
    scripts/collector.js               browser collector (runs in Claude desktop's built-in browser)
    assets/workspace-template/         blank user workspace: profile.md, tracker.xlsx, seen.txt, cv/, outputs/, examples/
job-buddy-skill.zip                    skill-only zip for claude.ai upload (rebuild after any skill change)
README.md, LICENSE, .gitignore
```

Install line: `/plugin install job-buddy --marketplace adityab94/job-buddy`

## Key design decisions (and why)

1. **The user's folder is the memory.** profile.md + tracker.xlsx + seen.txt live in the user's own
   folder, never in the repo. The skill reads them at the start of every task.
2. **Tracks.** A user can target up to 3 kinds of role; each track has its own master CV, titles,
   exclude words, salary floor, rubric and tiers. Shared: hard filters, locations, sources,
   watchlist, tracker (Track column V, after the formula columns T/U), seen list.
3. **Token economy.** Filter before reading. The collector filters in the page and returns only
   short rows (~600 tokens per run vs ~55k when raw listings were read). Two-pass scoring: quick
   score from title/company, full JD only for likely A/B. seen.txt prevents re-reading.
4. **Sources, in order of preference** (all tested Oct 2026, see references/sources.md):
   - Indeed **official connector** (`search_jobs`, `get_job_details`, `get_company_data`). Works for
     IE. No date filter, so recency is applied by the skill. Job IDs are session-scoped; dedupe on
     company+title. Indeed listings also feed Glassdoor, so Glassdoor is not searched separately.
   - **JobDataLake MCP** (optional, free, no account; `https://mcp.jobdatalake.com`). Adds
     Workday-hosted big-employer roles and `find_similar_jobs`. Thin for Ireland niche roles,
     nothing for health/public sector (tested 31 Oct 2026). Free pool (500/day) may be shared,
     so it's documented as a custom connector, not bundled in the plugin.
   - **Browser collector**, run from a builtindublin.ie page: Greenhouse, Lever, Ashby,
     SmartRecruiters, Workable public APIs (per company watchlist), Remotive, RemoteOK, Arbeitnow
     (CORS-open), Built In Dublin (same-origin fetch). `JSA.jobsie()` from a jobs.ie page.
     Himalayas works only same-origin (not wired in). Glassdoor is client-rendered (not wired in).
   - **Gmail job-alert emails** (optional) to cover LinkedIn, Indeed, IrishJobs.
   - **Pasted links/text**: always on; LinkedIn's public job page works for single jobs.
5. **Deliberately NOT used:** live LinkedIn scraping (ToS, blocks after ~5 searches; LinkedIn MCPs
   reviewed: felipfr's needs partner API access, stickerdaniel's scrapes a logged-in session and
   risks the user's account), Indeed/IrishJobs page scraping (Cloudflare/Akamai blocks), Apify or
   other paid scrapers (cost per user), getting past any security check.
6. **Honesty rules** for tailoring live in references/tailoring.md: never invent skills, metrics
   or titles; no keyword stuffing; plain human tone.
7. **Not a connector.** A hosted MCP connector can't reach the user's folder or built-in browser,
   and would mean storing CVs server-side. Plugin + GitHub marketplace is the distribution path.

## Conventions

- Skill text is written as instructions to Claude, plain language toward users, no code shown to users.
- Keep SKILL.md lean; detail goes in references/.
- After changing anything under `skills/job-buddy/`: rebuild `job-buddy-skill.zip`
  (`cd plugins/job-buddy/skills && zip -r ../../../job-buddy-skill.zip job-buddy`), bump the
  version in both plugin.json and marketplace.json, and run
  `claude plugin validate plugins/job-buddy/.claude-plugin/plugin.json` and
  `claude plugin validate .claude-plugin/marketplace.json`.
- Never commit personal data (CVs, profiles, trackers, outputs). `.gitignore` covers common paths.
- collector.js must stay plain browser JS (no build step, no dependencies) and be pasteable in one call.

## History (Oct 2026, built in a Cowork session)

- Started as a "job-search-assistant" skill. First-run setup and calibration done on Adi's own
  search (RevOps / Business Systems track; AI & automation weighted 30, core systems 25; office
  days filter raised to 3 after calibration; vague-JD rule = Tier B + ask the recruiter).
- First searches were manual LinkedIn-guest scraping: expensive and rate-limited, which led to the
  collector + Indeed connector design.
- Tested ~25 job sites (results in references/sources.md).
- Added tracks, seen list, two-pass scoring; migrated Adi's workspace; packaged as a plugin;
  renamed to Job Buddy; signed "Aditya Bhatnagar (The Buddy Social)"; MIT licence.

## Next actions

1. ~~**First push**, tag `v0.3.0` and Release with the zip.~~ Done 31 Oct 2026; v0.3.1 added
   JobDataLake as an optional connector.
2. **Install test from GitHub**: `/plugin install job-buddy --marketplace adityab94/job-buddy`, then
   "set me up" on an empty folder. Verify the workspace template is copied and setup completes.
3. **Retest two sources** marked untested in sources.md: Workable (needs a real company slug) and
   EURES (search URL was wrong), plus EURAXESS and HSE careers for non-tech users.
4. **Make Glassdoor/Himalayas optional readers** only if there's demand (page-read mode, not fetch).
5. **Token optimisation idea:** load collector.js via
   `await import('https://cdn.jsdelivr.net/gh/adityab94/job-buddy@v0.3.0/plugins/job-buddy/skills/job-buddy/scripts/collector.js')`
   instead of pasting ~2k tokens each run. Must check each host page's CSP first and pin a tag
   (never @latest).
6. **Gmail alerts path**: test with real LinkedIn / Indeed / IrishJobs alert emails and document the
   exact sender addresses in sources.md.
7. **Beta testers**: one non-tech user (e.g. public-health field) runs setup end to end; collect issues.
8. **Later**: plugin directory submission (check Anthropic's current requirements); a shared daily
   job feed (one hosted collector, e.g. Vercel cron, publishing JSON that each skill filters) once
   there are enough users in the same region.
