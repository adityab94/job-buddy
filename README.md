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
4. Optional: connect **Indeed** and **Gmail** (see `plugins/job-buddy/CONNECTORS.md`),
   and set up free job alerts on LinkedIn, Indeed and IrishJobs.

Then say **"find me roles"**, paste a job link, or **"tailor my CV for <company>"**.

## What's inside

```
.claude-plugin/marketplace.json            ← makes this repo installable as a marketplace
plugins/job-buddy/
  .claude-plugin/plugin.json
  CONNECTORS.md                            ← optional Indeed and Gmail connectors
  skills/job-buddy/
    SKILL.md                               ← the instructions Claude follows
    references/                            ← rubric design, sources, tailoring, outcomes
    scripts/collector.js                   ← free job collector (runs in Claude's built-in browser)
    assets/workspace-template/             ← blank profile, tracker and folders
```

## Privacy

Your profile, CVs, tracker and tailored documents stay in your own folder, never in this repo.
The `.gitignore` blocks them if you fork this.

## Respecting job sites

Uses official connectors, public job-board APIs and public pages at a normal pace. It does not
scrape LinkedIn or get past security checks. Please respect each site's terms, and credit
RemoteOK if you use its feed.

## Licence

MIT

---

Built by **Aditya Bhatnagar (The Buddy Social)**.
