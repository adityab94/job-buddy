# Job Buddy (plugin)

Runs your job search from a folder on your computer. Say **"set me up"** to start.

Install (Cowork): Customize → Plugins → Add marketplace → paste `adityab94/job-buddy`, then
install **job-buddy**.

Install (Claude Code):

```
/plugin marketplace add adityab94/job-buddy
/plugin install job-buddy@job-buddy
```

- Builds a scoring rubric for your field, with one or more role **tracks** (each with its own CV)
- Finds roles: Indeed connector, company job boards on your watchlist, Built In Dublin, Jobs.ie,
  remote-job feeds, job-alert emails (Gmail) and any link you paste
- Scores each role 0–100 with reasons (tier A, B or C)
- Tailors your CV and cover letter for strong matches, honestly
- Keeps an application tracker, with an easy dashboard page, and reviews what's working
- Tells you which missing skill would move the most roles up a tier ("what should I learn?")

Free to run: no paid scrapers, no API keys. It never logs in, applies or messages anyone for you.
See CONNECTORS.md for the optional Indeed, Gmail and JobDataLake connectors, and
TROUBLESHOOTING.md if something isn't working.

Things to say: "set me up", "find me roles", "is this a good fit? <link>",
"tailor my CV for <company>", "I heard back from <company>", "how's my search going?",
"show my dashboard", "what should I learn?",
"add a track for <role>".

## What it runs, reads and contacts

- **Your folder only.** Your CV, profile.md, tracker.xlsx, seen.txt, saved job ads and the
  generated dashboard.html stay in the job-search folder you choose. Nothing is sent to the
  author or any server run by the author.
- **Python scripts** in `skills/job-buddy/scripts/` (readable source, standard library plus
  openpyxl for the tracker): `jb.py` does score arithmetic, evidence checks, the seen list,
  tracker writes and folder upgrades; `dashboard.py` and `logo.py` build the local dashboard
  page, which makes no network requests.
- **Browser collector** (`collector.js`), run in Claude's built-in browser only when you ask
  it to find roles. It reads public job listings from: boards-api.greenhouse.io,
  api.lever.co, api.ashbyhq.com, api.smartrecruiters.com / jobs.smartrecruiters.com,
  apply.workable.com, remotive.com, remoteok.com, arbeitnow.com, builtindublin.ie and
  jobs.ie. It sends only the search filters (company slugs, titles), never your data or cookies.
- **Shared Ireland feed**: a public list of job listings fetched from
  raw.githubusercontent.com/adityab94/job-buddy (no data is sent).
- **Optional connectors** you add yourself (Indeed, Gmail, JobDataLake): see CONNECTORS.md.
- **Optional sidebar dashboard**: only if you ask for it, a private claude.ai artifact holding
  your job list (company, role, score, status, dates), never your CV or notes.

It never logs in to job sites, applies, or messages anyone on your behalf.

Privacy: see [PRIVACY.md](PRIVACY.md).

---

Built by **Aditya Bhatnagar (The Buddy Social)**.
