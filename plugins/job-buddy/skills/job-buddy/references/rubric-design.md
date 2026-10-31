# Designing a rubric for any field

Each track in profile.md has its own rubric. Hard filters that apply to every track live in
the profile's "Shared rules" section; track-specific filters (such as a salary floor) live
in the track.

A rubric turns "does this job suit me?" into a repeatable score. It has three parts:
hard filters, weighted dimensions, and tier cutoffs.

## 1. Hard filters (pass / fail)

Things that make a role a no regardless of anything else. Keep this list short and literal,
taken straight from the user's dealbreakers. Typical examples:
- Location / work mode outside what they'll accept
- Requires a licence, registration or clearance they don't hold and can't get quickly
- Contract type they won't take (e.g. fixed-term under 6 months)
- Salary clearly below their stated floor (only if the JD states salary)
- Visa sponsorship needed but explicitly not offered

If a JD is silent on a filter, it passes, with a confidence note.

## 2. Weighted dimensions (scored 1–5)

Use **4 to 6 dimensions**. Fewer is too blunt; more and the weights stop meaning anything.
Weights are whole numbers summing to 100.

Most fields can be covered by adapting these building blocks. Rename them in the user's own
language; a nurse's rubric should not say "tech stack".

| Building block | What it asks | Usually weighted |
|---|---|---|
| Core role match | Is the day-to-day work the work they do / want to do? | Highest (25–35) |
| Key skills or credentials | Do they have the specific skills, tools, methods, qualifications named? | High (15–25) |
| Domain / sector fit | Same industry, population, setting or subject area? | Medium (10–20) |
| Seniority fit | Does the level match where they are (or one step up)? | Medium (10–20) |
| Location & work-mode fit | How well does it fit beyond the hard filter (commute, hybrid days)? | Low–medium (5–15) |
| Growth / signal | Does it move them toward what they want next (a field-specific "signal")? | Low–medium (5–15) |

Field-specific "signal" dimensions are often the most useful part of a rubric because they
capture what the user actually wants that a generic match misses. Examples:
- RevOps person moving toward AI: "AI / automation signal" (agents, LLM workflows in the JD)
- Researcher: "Funding & research environment" (named grants, PI track record, protected time)
- Clinician: "Specialty & patient population"
- Designer: "Product maturity & design culture"

### Writing anchors

Every dimension needs a short description of what a **5**, **3** and **1** look like, in
concrete terms the user would recognise. Scores of 2 and 4 sit between anchors. Good anchors
are observable in a job description:

- Weak: "5 = great match"
- Strong: "5 = JD's main responsibilities are things I've done for 2+ years; 3 = about half
  overlap; 1 = mostly work I haven't done"

## 3. Tier cutoffs

Weighted score = Σ (dimension score ÷ 5 × weight), giving 0–100.
A dimension scored 1 contributes 20% of its weight, so the practical floor is 20.

Default tiers (adjust per user after calibration):
- **Tier A (75+)**: strong fit; tailor materials and apply
- **Tier B (60–74)**: worth applying; tailor if time allows
- **Tier C (under 60)**: stretch; only with a reason

## 4. Calibrate before trusting it

Score two or three postings the user already has a strong opinion on. If the rubric disagrees
with their gut, find out which dimension is wrong (anchor too generous? weight too high?) and
fix that, rather than nudging the cutoffs. Log the change.

---

## Worked example: RevOps / GTM automation professional (Ireland)

Hard filters: Ireland-based (Dublin preferred) or remote from Ireland; permanent or 12+ month
contract.

| Dimension | Weight | 5 | 3 | 1 |
|---|---|---|---|---|
| Core RevOps match | 30 | Owns CRM, quote-to-cash, forecasting or routing processes end to end | RevOps is part of the role alongside general ops or admin | Sales ops in name only; mostly reporting or data entry |
| Automation & tooling | 25 | Salesforce plus workflow tooling (Zapier, HubSpot, Marketo, etc.) central to the job | Uses the tools but someone else builds | No meaningful systems work |
| AI / agent signal | 15 | Building or running AI agents, LLM workflows or GTM automation is in scope | AI mentioned as a nice-to-have | No AI element |
| Seniority fit | 20 | Analyst-to-Manager band with ~5 years expected | Slightly junior or a stretch up | Entry-level or Director+ |
| Location fit | 10 | Dublin hybrid or fully remote in Ireland | Ireland but long commute / mostly on-site | Remote but awkward time zone |

Tiers: A 75+, B 60–74, C under 60. Tailoring logic: Tier A gets a tailored CV and cover letter;
Tier B gets a tailored summary and top bullets only.

Use this to show the shape and level of detail, not the content. A different field needs
different dimensions.
