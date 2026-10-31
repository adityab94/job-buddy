# Tracking outcomes and reviewing the search

## Tracker columns (Applications sheet)

| Column | Meaning |
|---|---|
| ID | Running number (1, 2, 3…) |
| Date Found | When the role entered the tracker |
| Company, Role, Location | As in the listing |
| Source | Where it was first found (LinkedIn, IrishJobs, company page, referral…) |
| Job URL | Most direct working link |
| Date Posted | Absolute date |
| Fit Score | 0–100 from the rubric |
| Tier | A, B or C |
| Top Gap | Biggest gap in one short phrase |
| Materials | Yes / No (tailored CV + letter produced) |
| Status | See below |
| Rejected At | Only when Status is Rejected: Screening, Assessment, Interview or Final |
| Date Applied | When they submitted |
| Last Update | Date of the latest change |
| Days to Response | Days from Date Applied to the first reply of any kind |
| Notes | Anything useful: contact name, referral, duplicate sources |
| Next Action | What they need to do, with a date if there is one |
| Applied?, Callback? | Formula columns; don't overwrite |
| Track | Which track the role was scored under (column V, after the formula columns) |

The Applied? and Callback? columns contain formulas that feed the Funnel sheet, which reads
Tier (J), Status (M), Applied? (T) and Callback? (U) by column letter, so those columns must
stay where they are. `jb.py tracker upsert` writes rows, IDs, Last Update and both formulas,
matches existing roles on company + role, and refuses to write if a fixed column has moved.

Without Python, write values into the other columns only and copy the formulas down from the
row above: Applied? is `=IF(OR(M2="",M2="Found"),0,1)`; Callback? is
`=IF(OR(M2="Assessment",M2="Interview",M2="Offer",AND(M2="Rejected",OR(N2="Assessment",N2="Interview",N2="Final"))),1,0)`.

## Status values

`Found` → `Applied` → `Acknowledged` → `Assessment` → `Interview` → `Offer`
plus the end states `Rejected`, `Withdrawn`, `Ghosted`.

Status is where the application is **now**. For rejections, Rejected At records how far it got,
because "rejected at screening" and "rejected after final interview" mean completely different
things for what to change.

A **callback** is any sign a human moved them forward: Assessment, Interview, Offer, or a
rejection at Assessment / Interview / Final.

## Classifying a message

Read the whole message, then decide:
- **Acknowledged**: automated or human confirmation of receipt, "under review".
- **Assessment**: a test, task, case study or questionnaire beyond the application form.
- **Interview**: a request to schedule or attend any conversation (screening call counts).
- **Offer**: an offer, verbal or written.
- **Rejected**: any "not progressing". Set Rejected At from context: no prior contact →
  Screening; after a test → Assessment; after any interview → Interview, or Final if they'd
  reached the last round.

Watch for mixed signals: rejections often thank people for interviewing, and acknowledgements
often mention "next steps". When genuinely unsure, ask the user.

Fill Days to Response on the first reply of any kind (including an acknowledgement).

## Review

Run when asked ("how's it going?"), and suggest one after every ~10 new outcomes.

### What to report (in this order)

1. **Activity**: roles found, applied, open, by tier, over the period.
2. **Funnel by tier** (from the Funnel sheet): applications and callback rate for A, B, C.
   The key question: do Tier A roles convert better than Tier B? If they don't, the rubric
   isn't predicting what employers respond to.
3. **Where rejections happen**: counts by Rejected At. Mostly at Screening means the
   application isn't getting through (targeting, CV, or a hard requirement they're missing).
   Mostly at Interview means applications are fine and interview prep is the lever.
4. **By track, source and role type**: callback rate per track, per source and per title
   family, if there's enough data. With several tracks, the key question is which direction
   is working.
5. **Speed**: typical Days to Response. Very fast rejections usually mean an automatic knockout
   (location, work authorisation, a required qualification, salary expectations on the form),
   not wording. Look for what those roles had in common before blaming the CV.
6. **Suggestions**, each tied to the numbers above.

### Minimum evidence

Small numbers lie. Use these floors before proposing a change:
- A segment (tier, source, role family) needs **at least 8 resolved applications**
  (anything past Applied/Acknowledged, including Ghosted) before you compare its rate with
  another.
- A rubric weight change needs a pattern that holds across **at least 15 resolved
  applications** overall.
Below these, you may share an observation, labelled clearly as an early hunch, and suggest
what to watch for. "No clear pattern yet" is a perfectly good finding.

### Proposing changes

For each suggestion, give: the change, the evidence (with numbers), and what you'd expect to
see if it's right. The user approves or rejects each one. Then:
- update `profile.md` and add a dated entry to its change log;
- add a row to the tracker's Rubric Changes sheet (date, change, evidence, approved yes/no);
- if tiers shift, offer to re-score open (Found / Applied) roles.

Never change the rubric, targeting or sources without approval.
