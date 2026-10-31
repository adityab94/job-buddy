# Job Buddy for Claude

Job Buddy is a Claude plugin that runs your job search from a folder on your computer. It learns what a good
role looks like for *you*, finds and scores jobs, tailors your CV and cover letters, and keeps an
application tracker. It works for any field: tech, health, research, public sector and more.
Ireland and EU by default, easy to change.

## Install (Cowork or Claude Code)

**Cowork:** Customize → Plugins → Add marketplace → paste this repo's GitHub URL
(`adityab94/job-buddy`), then install **job-buddy**.

**Claude Code:**
```
/plugin install job-buddy --marketplace adityab94/job-buddy
```

**Claude on the web (skills only):** download `job-buddy-skill.zip` from Releases and
upload it under Settings → Capabilities → Skills.

Updates: push a new version here and users get it when they update the marketplace.

## Get started

1. Make an empty folder on your computer (e.g. `job-search`) and connect it to Claude.
2. Put your CV in it, or attach it in the chat.
3. Say **"set me up"**. Claude builds your workspace, interviews you, drafts your rubric and
   switches on your job sources.
4. Optional: connect **Indeed**, **Gmail** and **JobDataLake** (see `plugins/job-buddy/CONNECTORS.md`),
   and set up free job alerts on LinkedIn, Indeed and IrishJobs.

Then say **"find me roles"**, paste a job link, or **"tailor my CV for <company>"**.

## What's inside

```
.claude-plugin/marketplace.json            ← makes this repo installable as a marketplace
plugins/job-buddy/
  .claude-plugin/plugin.json
  CONNECTORS.md                            ← optional Indeed, Gmail and JobDataLake connectors
  TROUBLESHOOTING.md                       ← common problems and fixes
  evals/                                   ← test cases for scoring, tailoring and emails
  skills/job-buddy/
    SKILL.md                               ← the instructions Claude follows
    references/                            ← rubric design, sources, tailoring, outcomes
    scripts/collector.js                   ← free job collector (runs in Claude's built-in browser)
    scripts/jb.py                          ← core: scoring maths, evidence check, tracker updates
    assets/workspace-template/             ← blank profile, tracker and folders
```

## Privacy

Your profile, CVs, tracker and tailored documents stay in your own folder, never in this repo.
The `.gitignore` blocks them if you fork this. What goes where:

- **Claude** reads your CV and profile to score jobs and tailor documents, like any file
  you share with Claude.
- **Indeed and JobDataLake** (if you connect them) receive only your search words and
  location, never your CV.
- **Job sites** read by the collector receive ordinary page requests, with no login.
- **The shared feed** is a public file of job listings built daily from employers' public job
  boards (`feed/`). Your Job Buddy downloads it; it never uploads anything.
- **Nothing is sent to the Job Buddy author.** There is no tracking or analytics.

## Problems and ideas

See [TROUBLESHOOTING.md](plugins/job-buddy/TROUBLESHOOTING.md), or ask Claude to "report a
problem with Job Buddy" and file what it writes as an
[issue](https://github.com/adityab94/job-buddy/issues/new/choose). Changes are listed in
[CHANGELOG.md](CHANGELOG.md).

## Respecting job sites

Uses official connectors, public job-board APIs and public pages at a normal pace. It does not
scrape LinkedIn or get past security checks. Please respect each site's terms, and credit
RemoteOK if you use its feed.

## Licence

MIT

---

Built by **Aditya Bhatnagar (The Buddy Social)**.
