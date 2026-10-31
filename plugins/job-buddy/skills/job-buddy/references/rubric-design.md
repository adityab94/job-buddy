# Building a strong rubric

The rubric decides every recommendation, so it has to be built from evidence, split into the
two questions that actually decide a job, checked mechanically, and proven against the user's
own judgement before it's trusted. Each kind of role (track) has its own.

A rubric has four parts: deal-breakers, "Can I get it?", "Do I want it?", and tiers.

## 1. Deal-breakers (pass / fail)

Things that make a role a no regardless of anything else. Keep the list short and literal,
taken straight from the user's words: location or office days outside what they'll accept, a
licence or clearance they don't hold and can't get quickly, a contract type they won't take,
salary clearly below their floor (only when the ad states it), visa sponsorship needed but
refused. If an ad is silent on one, it passes, with a confidence note. Never score the same
thing again as a dimension; a dimension may score only what's beyond the deal-breaker (e.g.
"2 office days" vs "3" when the deal-breaker is "no more than 3").

## 2. Build from the real market, not a template

1. **Gather 15–25 current ads** for the user's target role, in their place (or remote), from
   the sources that are on: the shared feed, Indeed (`get_job_details` gives the full text),
   JobDataLake, pasted links. Prefer variety: different employers, sizes and seniority within
   reach. Save each ad's text as `jds/market/<Company - Role>.txt`. Read them in batches and
   keep notes short; don't paste ads into the conversation.
2. **List what employers ask for**: the recurring responsibilities, skills, tools,
   credentials and experience levels, in the ads' own words. Then count them exactly:
   `jb.py market <workspace> --terms "Salesforce/SFDC, forecasting, lead routing, Python"`
   (use `/` for synonyms). Requirements in most ads are the core of "Can I get it?"; ones in
   a few ads are differentiators.
3. **Hold the CV against that list**: where they're strong, where they're thin, what they
   have that the market values but rarely asks for.

## 3. "Can I get it?": how well they match what employers ask

2–4 dimensions, weights summing to 100, each tied to a cluster of requirements from the
market list. Every dimension records how many ads ask for it in a **Seen in** column (e.g.
`18/20`): that's the evidence it belongs. Typical shapes, renamed in the field's own words:
core day-to-day work, named skills / tools / credentials, level of experience, sector or
setting. A nurse's rubric never says "tech stack".

## 4. "Do I want it?": how well the role fits what they want

2–4 dimensions, weights summing to 100, from the user's own priorities: the work that excites
them (e.g. "AI and automation", "research time", "patient population"), working pattern
beyond the deal-breaker, growth toward where they want to be next, culture or mission signals
they named. Ask what made their best and worst past jobs; that usually finds them.

Keep the two parts separate. A dream role they can't land and an easy role they'd hate must
not look alike, and only the split shows the difference.

## 5. Anchors: what a 5, a 3 and a 1 look like

Every dimension needs a short description of a **5**, **3** and **1** that you could check in
a job ad. Scores of 2 and 4 sit between them.
- Weak: "5 = great match"
- Strong: "5 = the ad's main responsibilities are things they've done for 2+ years;
  3 = about half overlap; 1 = mostly work they haven't done"

## 6. Tiers

Each part scores 0–100 (Σ score ÷ 5 × weight). The overall score shown is their average, but
the tier needs both:
- **Tier A (great match): Get 70+ and Want 70+.** Tailor the CV and cover letter, apply.
- **Tier B (good match): Get 55+ and Want 55+.** Worth applying.
- **Tier C (long shot): anything else.** Only with a reason.
Adjust the cut-offs per user only during calibration, and only with a reason they agree to.

## 7. Check it

Run `jb.py rubric <workspace> --check`. Fix every **problem** (weights not adding to 100, a
part with too few or too many dimensions, missing anchors, tiers that don't make sense)
before scoring anything. Treat **warnings** as weak spots: vague anchors, dimensions not
grounded in market ads, two dimensions that are really one, overlap with a deal-breaker.
Fix them unless there's a clear reason not to.

## 8. Calibrate before trusting it

Score eight real roles (the ones the search found are fine; the user never has to bring
their own) and ask them to rate each great / okay / no. Run
`jb.py calibrate <workspace> --apply` with their verdicts. At least 7 in 8 must agree before
the rubric is marked CALIBRATED; until then every score is a first draft. For each
disagreement, find the cause in the rubric (an anchor too generous, a weight too high, a
priority missing) and fix that, rather than nudging the tier cut-offs. Say in plain words
what changed, re-score, run it again. Log the result in the change log.

Later, real outcomes take over: the search review checks whether Tier A gets more callbacks
than Tier B (references/outcomes.md), and that evidence outranks the calibration.

---

## Worked example: RevOps / GTM automation, Dublin

Deal-breakers: Ireland-based or remote from Ireland; no more than 3 office days; permanent.
Market: 20 Dublin RevOps ads (October 2026).

#### Can I get it?
| Dimension | Weight | 5 looks like | 3 looks like | 1 looks like | Seen in |
|---|---|---|---|---|---|
| Core RevOps work | 45 | Owns routing, forecasting and CRM processes end to end | RevOps is part of a wider ops or admin role | Mostly reporting or data entry | 18/20 |
| Tools asked for | 30 | Salesforce and a workflow tool (HubSpot, Zapier, Workato) both central | One of them is named | Neither is mentioned | 15/20 |
| Experience level | 25 | Asks for 4–7 years in RevOps or sales ops | Asks for 2–3 years, or 8+ | Graduate role, or Director level | 20/20 |

#### Do I want it?
| Dimension | Weight | 5 looks like | 3 looks like | 1 looks like |
|---|---|---|---|---|
| AI and automation work | 55 | Building AI agents or automations is in scope | Automation is a nice-to-have | No automation or AI at all |
| Office days | 25 | Two or fewer office days in Dublin | Three office days | (deal-breaker beyond this) |
| Growth toward GTM engineering | 20 | Path to systems or GTM engineering is named | Small team where it could grow | Pure maintenance role |

Tiers: A = Get 70+ and Want 70+; B = Get 55+ and Want 55+; C = anything else.

Use this for shape and level of detail, not content. A different field needs different
dimensions, built from its own market.
