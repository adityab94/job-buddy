# Job Buddy evals

Test cases for `claude plugin eval` (Claude Code v2.1.269+). Each case is a realistic request
with a made-up profile and CV (Sam Doyle), plus graders that check the outcome.

| Case | Checks |
|---|---|
| score-strong-fit | A clearly matching role scores 75+ and lands in Tier A |
| score-hard-filter-fail | A Director role in Munich fails the hard filters |
| score-short-contract | A 6-month contract is flagged against "permanent only" |
| tailor-no-invention | Tailoring never claims skills (Marketo, Python) or metrics that aren't in the CV |
| email-post-interview-rejection | "Thanks for interviewing… unfortunately" is a rejection at Interview |
| email-assessment-invite | An assessment invite is a next stage, with its deadline up top |
| report-a-problem | The diagnostic points to GitHub issues and leaves out personal details |
| ignores-unrelated-request | Job Buddy stays out of unrelated requests |

Run from `plugins/job-buddy` (uses your Claude plan; roughly 8 cases × 3 runs × 2 arms):

    claude plugin eval .

Quick check while editing one case:

    claude plugin eval . --case score-strong-fit --runs 1 --ablation none

Run before every release that changes SKILL.md or anything in `references/`.
