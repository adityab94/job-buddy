# Job Buddy privacy policy

Last updated: 31 October 2026

Job Buddy is a free, open-source Claude plugin by Aditya Bhatnagar (The Buddy Social). This
policy explains what it reads, stores and sends.

## The short version

Your data stays in the job-search folder you choose on your own computer. Job Buddy has no
server and no accounts, and nothing is ever sent to the author.

## What it reads

- Your CV and anything you tell Claude about your experience, preferences and applications.
- Public job listings (see "What it contacts" below).
- If you add them yourself, the optional Indeed, Gmail or JobDataLake connectors. Gmail is
  used only to read job-alert emails when you ask it to find roles.

## What it stores, and where

Everything is written as ordinary files in your job-search folder: `profile.md` (your
preferences and rubric), `tracker.xlsx` (your applications), `seen.txt` (jobs already
reviewed), saved job ads in `jds/`, tailored CVs and cover letters in `outputs/`, and a local
`dashboard.html`. You can read, edit or delete any of them at any time. Deleting the folder
deletes everything Job Buddy stored.

Your conversations with Claude are handled by Anthropic under your Claude account's own terms
and privacy settings, as with any other use of Claude.

## What it contacts

When you ask it to find roles, Job Buddy fetches public job listings from: Greenhouse,
Lever, Ashby, SmartRecruiters and Workable public job APIs, Remotive, RemoteOK, Arbeitnow,
Built In Dublin, Jobs.ie, and a public feed file on raw.githubusercontent.com
(adityab94/job-buddy). It sends only search details such as company names and job titles,
never your CV, profile or tracker, and never your cookies or logins.

It never signs in to job sites, applies for jobs, or messages anyone on your behalf.

## Optional sidebar dashboard

Only if you ask for it, Job Buddy publishes a private Claude artifact to your own claude.ai
account showing your job list (company, role, score, status and dates). It never includes
your CV or notes. It's private to you unless you choose to share it, and you can ask Claude to
delete it at any time.

## Analytics and tracking

None. Job Buddy collects no analytics, telemetry or usage data.

## Children

Job Buddy is not intended for people under 18.

## Changes and contact

Changes to this policy are recorded in the repository's history. Questions or concerns:
open an issue at https://github.com/adityab94/job-buddy/issues.
