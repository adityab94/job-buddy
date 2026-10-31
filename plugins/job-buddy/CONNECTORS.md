# Recommended connectors

The plugin works without any connectors. These make it better; connect them in
Claude under Settings → Connectors. The skill checks which are connected and skips the rest.

| Connector | What it adds | Needed? |
|---|---|---|
| **Indeed** | Searches Indeed's listings through Indeed's official connector (search jobs, job details, company salaries and ratings). Indeed's listings also appear on Glassdoor, so this covers both. | Recommended |
| **Gmail** | Reads your job-alert emails from LinkedIn, Indeed and IrishJobs, so those sites are covered without scraping. Read-only use: it never sends email. | Optional |
| **JobDataLake** | Searches jobs from about 25,000 companies' own career sites, including big employers on Workday that nothing else here reaches, and finds jobs similar to one you like. Free (500 searches a day), no account. Best for tech, data, sales and operations roles; little for health, public sector or research. | Optional |

**Adding JobDataLake:** it isn't in Claude's connector directory, so add it as a custom
connector with the URL `https://mcp.jobdatalake.com` (Settings → Connectors → Add custom
connector). In Claude Code: `claude mcp add --transport http jobdatalake https://mcp.jobdatalake.com`.
Only your search words are sent to it, never your CV or profile.

Also used, no connector needed: the Claude desktop app's built-in browser, which reads public
company job boards (Greenhouse, Lever, Ashby, SmartRecruiters, Workable), Built In Dublin,
Jobs.ie and remote-job feeds. Each site asks you to allow it once.
