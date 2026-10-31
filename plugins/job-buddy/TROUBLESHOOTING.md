# Troubleshooting

Common problems and what to do. If none of these fit, ask Claude to
"report a problem with Job Buddy" and file the result as a
[GitHub issue](https://github.com/adityab94/job-buddy/issues/new/choose).

## Setup

**Claude doesn't seem to know about Job Buddy.**
Check the plugin is installed and switched on (Customize → Plugins in the desktop app, or
`/plugin` in Claude Code). Then say "set me up" or "find me roles" in a new session.
If you also have an older job-search skill installed, remove it so the two don't compete.

**"I can't see a workspace" / it keeps asking for a folder.**
Claude can only use a folder you've connected to the session. Connect your `job-search`
folder (or an empty one for a fresh start) and try again.

**I'm on claude.ai, not the desktop app.**
Upload `job-buddy-skill.zip` from the
[latest release](https://github.com/adityab94/job-buddy/releases/latest). Without the
desktop app there's no built-in browser, so the collector can't run: you'll rely on
connectors and pasted job links. Re-upload the zip to get updates.

## Finding jobs

**A source says "BROKEN?" or shows an error.**
Once can be a hiccup; try again later. If it happens on two runs, the site has probably
changed: file a "A job source is broken" issue. Other sources keep working meanwhile.

**A watchlist company shows a 404 error.**
Its job-board ID is wrong or the company moved to a different job board. Ask Claude to
"fix <company> in my watchlist"; it will look up the right one.

**Very few results.**
- Outside Dublin: Built In Dublin is Dublin-only. Ask Claude to set Jobs.ie to your town.
- Outside Ireland: Built In Dublin and Jobs.ie don't apply. Connect Indeed, add companies to
  your watchlist, and set up job alerts.
- Non-tech fields: add field-specific sites (publicjobs.ie, HSE, EURAXESS…) and job alerts.
- Your titles may be narrow: ask Claude to add adjacent titles to your track.

**The browser asks me to "Allow" a site.**
Normal, once per site. Job Buddy only reads public pages and never logs in.

**JobDataLake says the daily limit is reached.**
The free tier has a daily cap. It resets the next day; other sources still run.

## Tracker

**"Couldn't save the tracker."**
Close `tracker.xlsx` in Excel (or Numbers) and ask again. Claude can't write to it while
it's open.

**A formula column looks wrong.**
The grey columns (Applied?, Callback?) are formulas. If something got typed over them,
ask Claude to "repair the tracker formulas".

## Dashboard

**I want my dashboard in Claude, not as a file.**
Ask Claude "put my dashboard in my Claude sidebar". It creates a private page in your Claude
account that updates itself and also opens on your phone. Not every Claude app supports this;
if yours doesn't, the local file still works.

**My online dashboard is out of date.**
It updates at the end of each task that changes your tracker. If you edited tracker.xlsx
yourself, ask Claude to "refresh my dashboard".

**It says "Open this from your Claude sidebar".**
The page reads your data from your Claude account, so it needs to be opened from Claude while
you're signed in.

**There's no dashboard.html.**
It appears once Job Buddy has written the first role to your tracker. You can also ask Claude
to "show my dashboard".

**The dashboard is out of date.**
It refreshes whenever Claude updates the tracker. If you edited tracker.xlsx yourself, ask
Claude to "refresh my dashboard".

**The gap plan is empty.**
It needs roles scored with Job Buddy 0.6 or later (each score now records the gaps). Older
roles show up through the tracker's Top Gap column once you have a few.

## Usage limits

A full search plus tailoring several CVs uses a fair amount of your Claude plan. If you hit
limits, search less often (weekly is plenty), tailor only Tier A roles, and switch off
sources that never produce good matches.
