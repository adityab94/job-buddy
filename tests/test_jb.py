"""Unit tests for scripts/jb.py. Run from the repo root: python3 -m unittest discover tests"""
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/job-buddy/skills/job-buddy"
TEMPLATE = SKILL / "assets/workspace-template"
sys.path.insert(0, str(SKILL / "scripts"))
import jb  # noqa: E402

try:
    import openpyxl  # noqa: F401
    HAS_XL = True
except ImportError:
    HAS_XL = False

TRACK = """## Track 1: Revenue Operations
- Status: ACTIVE
- Master CV: cv/sam.pdf

### Rubric
Weights add up to 100. Each dimension is scored 1-5 using the anchors.

| Dimension | Weight | 5 looks like | 3 looks like | 1 looks like |
|---|---|---|---|---|
| Core RevOps match | 30 | a | b | c |
| Automation & tooling | 25 | a | b | c |
| AI / agent signal | 15 | a | b | c |
| Seniority fit | 20 | a | b | c |
| Location fit | 10 | a | b | c |

### Tiers
- Tier A: 75+  (tailor CV + cover letter, apply)
- Tier B: 60-74 (worth applying)
- Tier C: under 60 (stretch, only with a reason)

### Tailoring notes
- Always mention: Salesforce

---

## Track 2: Paused one
- Status: PAUSED

| Dimension | Weight |
|---|---|
| Only | 100 |

- Tier A: 80+
"""

TRACK2 = """## Track 1: Revenue Operations
- Status: ACTIVE
- Master CV: cv/sam.pdf

### Rubric
- Rubric status: DRAFT

#### Can I get it?
| Dimension | Weight | 5 looks like | 3 looks like | 1 looks like | Seen in |
|---|---|---|---|---|---|
| Core RevOps work | 50 | Owns routing, forecasting and CRM end to end | Part of the job sits in sales ops | Mostly reporting or data entry | 18/20 |
| Tools asked for | 30 | Salesforce and HubSpot are both named as core | One of the two is named | Neither is mentioned anywhere | 15/20 |
| Seniority asked for | 20 | Asks for 4 to 7 years in RevOps | Asks for 2 to 3 years or 8 plus | Graduate role or Director level | 20/20 |

#### Do I want it?
| Dimension | Weight | 5 looks like | 3 looks like | 1 looks like |
|---|---|---|---|---|
| AI and automation work | 60 | Building AI agents or automations is in scope | Automation is mentioned as nice to have | No automation or AI at all |
| Hybrid days | 40 | Two office days or fewer in Dublin | Three office days in Dublin | Four or more office days |

### Tiers
- Tier A: Get 70+ and Want 70+ (great match)
- Tier B: Get 55+ and Want 55+ (good match)
- Tier C: anything else
"""

JD = """Revenue Operations Manager, Tessel (Dublin, hybrid 2 days a week).
You will own Salesforce and HubSpot, lead routing and forecasting, build automations with
Zapier and Workato, and pilot AI agents for lead qualification. 5+ years in RevOps."""


def make_ws(version=True):
    d = Path(tempfile.mkdtemp())
    ws = d / "job-search"
    shutil.copytree(TEMPLATE, ws)
    text = (ws / "profile.md").read_text(encoding="utf-8")
    text = text.replace("## Track 1: <name>", "## Track 0: placeholder", 1)
    text = text.split("## Track 0: placeholder")[0] + TRACK + "\n## Change log\n"
    if not version:
        text = text.replace("Workspace version: 2\n", "")
    (ws / "profile.md").write_text(text, encoding="utf-8")
    (ws / "jds" / "tessel.txt").write_text(JD, encoding="utf-8")
    return ws


def run_cli(*args, stdin=""):
    p = subprocess.run([sys.executable, str(SKILL / "scripts/jb.py"), *args], input=stdin,
                       capture_output=True, text=True)
    return p.returncode, (json.loads(p.stdout) if p.stdout.strip() else None), p.stderr


def dims(**overrides):
    base = {
        "Core RevOps match": {"score": 5, "quote": "lead routing and forecasting"},
        "Automation & tooling": {"score": 4, "quote": "build automations with Zapier and Workato"},
        "AI / agent signal": {"score": 4, "quote": "pilot AI agents for lead qualification"},
        "Seniority fit": {"score": 4, "quote": "5+ years in RevOps"},
        "Location fit": {"score": 5, "quote": "Dublin, hybrid 2 days a week"},
    }
    base.update(overrides)
    return base


class Profile(unittest.TestCase):
    def test_parse_tracks(self):
        ws = make_ws()
        tracks = jb.parse_tracks((ws / "profile.md").read_text())
        self.assertEqual([t["name"] for t in tracks], ["Revenue Operations", "Paused one"])
        t = tracks[0]
        self.assertEqual(sum(t["weights"].values()), 100)
        self.assertEqual(t["tiers"], {"A": 75, "B": 60})
        self.assertEqual(jb.find_track(tracks, None)["name"], "Revenue Operations")  # paused is skipped
        self.assertEqual(jb.find_track(tracks, "2")["name"], "Paused one")
        self.assertEqual(jb.find_track(tracks, "revenue")["name"], "Revenue Operations")

    def test_template_profile_is_current_version(self):
        text = (TEMPLATE / "profile.md").read_text()
        self.assertEqual(jb.workspace_version(text), jb.WORKSPACE_VERSION)


class Score(unittest.TestCase):
    def setUp(self):
        self.ws = make_ws()

    def test_math_tier_and_verified_evidence(self):
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt", "dimensions": dims()})
        # 30 + 20 + 12 + 16 + 10 = 88
        self.assertEqual(r["score"], 88)
        self.assertEqual(r["tier"], "A")
        self.assertEqual(r["confidence"], "high")
        self.assertEqual(r["unverified"], [])

    def test_halves_round_up(self):
        # 4,2.5,4,4,4 = 72.5: must be 73, not banker's-rounded 72
        half = {k: {"score": s, "quote": dims()[k]["quote"]} for k, s in zip(dims(), [4, 2.5, 4, 4, 4])}
        self.assertEqual(jb.score(self.ws, {"jd_file": "jds/tessel.txt", "dimensions": half})["score"], 73)

    def test_tier_b_c_and_near_cutoff(self):
        low = {k: {"score": 3, "quote": v["quote"]} for k, v in dims().items()}
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt", "dimensions": low})
        self.assertEqual((r["score"], r["tier"]), (60, "B"))
        self.assertTrue(r["near_cutoff"])
        lower = {k: {"score": 1, "quote": v["quote"]} for k, v in dims().items()}
        self.assertEqual(jb.score(self.ws, {"jd_file": "jds/tessel.txt", "dimensions": lower})["tier"], "C")

    def test_invented_quote_lowers_confidence(self):
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt",
                               "dimensions": dims(**{"Core RevOps match": {"score": 5, "quote": "owns quote-to-cash end to end"}})})
        self.assertEqual(r["dimensions"][0]["evidence"], "not in job ad")
        self.assertEqual(r["confidence"], "low")
        self.assertTrue(any("not in the saved job ad" in p for p in r["problems"]))

    def test_quote_normalisation(self):
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt",
                               "dimensions": dims(**{"Location fit": {"score": 5, "quote": "DUBLIN,  hybrid 2 days"}})})
        self.assertEqual(r["dimensions"][4]["evidence"], "verified")

    def test_short_and_missing_quotes(self):
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt",
                               "dimensions": dims(**{"Location fit": {"score": 5, "quote": "Dublin"},
                                                     "Seniority fit": {"score": 4}})})
        self.assertEqual(r["dimensions"][4]["evidence"], "too short")
        self.assertEqual(r["dimensions"][3]["evidence"], "missing")
        self.assertEqual(r["confidence"], "medium")  # 30 weight unverified, nothing invented

    def test_no_jd_file_is_unverified(self):
        r = jb.score(self.ws, {"dimensions": dims()})
        self.assertEqual(r["confidence"], "low")
        self.assertTrue(all(d["evidence"] == "unverified" for d in r["dimensions"]))

    def test_bad_inputs(self):
        with self.assertRaises(jb.Fail):
            jb.score(self.ws, {"dimensions": dims(**{"Seniority fit": {"score": 6}})})
        partial = dims()
        partial.pop("Location fit")
        with self.assertRaises(jb.Fail):
            jb.score(self.ws, {"dimensions": partial})
        with self.assertRaises(jb.Fail):
            jb.score(self.ws, {"jd_file": "jds/nope.txt", "dimensions": dims()})

    def test_weights_not_100_reported(self):
        p = self.ws / "profile.md"
        p.write_text(p.read_text().replace("| Location fit | 10 |", "| Location fit | 15 |"))
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt", "dimensions": dims()})
        self.assertTrue(any("add up to 105" in x for x in r["problems"]))

    def test_cli(self):
        code, out, _ = run_cli("score", str(self.ws), stdin=json.dumps({"jd_file": "jds/tessel.txt", "dimensions": dims()}))
        self.assertEqual((code, out["score"]), (0, 88))
        code, out, err = run_cli("score", str(self.ws), stdin="not json")
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)


class Gaps(unittest.TestCase):
    """Five scored roles; Python is the gap in three, two of them a few points short of Tier A."""

    def score_role(self, company, role, scores, gaps):
        (self.ws / "jds" / f"{company} - {role}.txt").write_text(JD, encoding="utf-8")
        d = {k: {"score": s, "quote": dims()[k]["quote"]} for k, s in zip(dims(), scores)}
        return jb.score(self.ws, {"company": company, "role": role, "jd_file": f"jds/{company} - {role}.txt",
                                  "dimensions": d, "gaps": gaps})

    def setUp(self):
        self.ws = make_ws()
        py = lambda to: {"skill": "Python", "dimension": "Automation & tooling", "score_if_closed": to}  # noqa: E731
        # weights 30/25/15/20/10; e.g. [4,2,4,4,4] = 24+10+12+16+8 = 70
        self.r1 = self.score_role("Wayflyer", "GTM Engineer", [4, 2, 4, 4, 4], [py(5)])          # 70 B -> 85 A
        self.score_role("Harvey", "GTM Systems", [4, 2.5, 4, 4, 4], [py(4)])                     # 72.5 -> 73 B (half-up) -> 80 A
        self.score_role("Kota", "RevOps Manager", [3, 2, 3, 3, 3], [py(4), {"skill": "Marketo",
                        "dimension": "Core RevOps match", "score_if_closed": 4}])                 # 55 C -> 65 B
        self.score_role("Tessel", "RevOps Manager", [5, 4, 4, 4, 5], [])                         # 88 A, no gaps
        self.score_role("Corvid", "Sales Ops", [3, 3, 2, 3, 3], [{"skill": "marketo ",
                        "dimension": "core revops match", "score_if_closed": 5}])                 # 57 C -> 69 B

    def test_score_saves_breakdown(self):
        self.assertEqual(self.r1["saved"], "jds/Wayflyer - GTM Engineer.score.json")
        saved = json.loads((self.ws / self.r1["saved"]).read_text())
        self.assertEqual((saved["company"], saved["score"], saved["tier"]), ("Wayflyer", 70, "B"))
        self.assertEqual(saved["gaps"][0]["dimension"], "Automation & tooling")

    def test_report_ranks_by_tier_a_upgrades(self):
        r = jb.gap_report(self.ws)
        self.assertEqual(r["roles_analysed"], 5)
        top = r["skills"][0]
        self.assertEqual(top["skill"], "Python")
        self.assertEqual(top["roles_with_gap"], 3)
        self.assertEqual(sorted(top["tier_upgrades"]), ["Harvey, GTM Systems: 73 B -> 80 A",
                                                        "Kota, RevOps Manager: 55 C -> 65 B",
                                                        "Wayflyer, GTM Engineer: 70 B -> 85 A"])
        marketo = r["skills"][1]
        self.assertEqual((marketo["skill"].lower().strip(), marketo["roles_with_gap"]), ("marketo", 2))  # names merged
        self.assertEqual(sorted(marketo["tier_upgrades"]), ["Corvid, Sales Ops: 57 C -> 69 B",
                                                            "Kota, RevOps Manager: 55 C -> 61 B"])
        self.assertTrue(any("early hunch" in n for n in r["notes"]))

    def test_invalid_gaps_refused(self):
        for bad in ({"skill": "Python", "dimension": "Nope", "score_if_closed": 5},
                    {"skill": "Python", "dimension": "Location fit", "score_if_closed": 3},  # below current
                    {"dimension": "Location fit", "score_if_closed": 5}):
            with self.assertRaises(jb.Fail):
                self.score_role("X", "Y", [4, 4, 4, 4, 4], [bad])

    def test_invented_quote_not_saved(self):
        (self.ws / "jds" / "Q - R.txt").write_text(JD)
        d = dims(**{"Core RevOps match": {"score": 5, "quote": "owns quote-to-cash end to end"}})
        r = jb.score(self.ws, {"company": "Q", "role": "R", "jd_file": "jds/Q - R.txt", "dimensions": d})
        self.assertNotIn("saved", r)
        self.assertFalse((self.ws / "jds" / "Q - R.score.json").exists())

    def test_rubric_change_skips_old_scores(self):
        p = self.ws / "profile.md"
        p.write_text(p.read_text().replace("| Location fit | 10 |", "| Location & hours | 10 |"))
        r = jb.gap_report(self.ws)
        self.assertEqual(r["roles_analysed"], 0)
        self.assertEqual(len(r["skipped"]), 5)

    @unittest.skipUnless(HAS_XL, "openpyxl not installed")
    def test_closed_roles_dont_count_as_upgrades(self):
        jb.tracker_upsert(self.ws, [{"Company": "Wayflyer", "Role": "GTM Engineer", "Status": "Rejected",
                                     "Rejected At": "Interview"},
                                    {"Company": "Old Co", "Role": "Analyst", "Top Gap": "No Python"}])
        r = jb.gap_report(self.ws)
        top = next(s for s in r["skills"] if s["skill"] == "Python")
        self.assertEqual(top["rejected_roles_with_gap"], 1)
        self.assertEqual(len(top["tier_upgrades"]), 2)  # Wayflyer is closed now
        self.assertEqual(r["top_gap_column"], {"No Python": 1})

    def test_cli_names(self):
        code, out, _ = run_cli("gaps", str(self.ws), "--names")
        self.assertEqual(code, 0)
        self.assertIn("Python", out["known_skill_names"])


def make_ws2():
    ws = make_ws()
    text = (ws / "profile.md").read_text()
    (ws / "profile.md").write_text(text.split("## Track 1: Revenue Operations")[0] + TRACK2 + "\n## Change log\n")
    return ws


DIMS2 = {"Core RevOps work": "lead routing and forecasting", "Tools asked for": "Salesforce and HubSpot",
         "Seniority asked for": "5+ years in RevOps", "AI and automation work": "pilot AI agents for lead qualification",
         "Hybrid days": "Dublin, hybrid 2 days a week"}


def dims2(*scores):
    return {k: {"score": s, "quote": DIMS2[k]} for k, s in zip(DIMS2, scores)}


class TwoPartRubric(unittest.TestCase):
    def setUp(self):
        self.ws = make_ws2()

    def test_parse(self):
        t = jb.parse_tracks((self.ws / "profile.md").read_text())[0]
        self.assertEqual(t["mode"], "two")
        self.assertEqual(set(t["parts"]), {"get", "want"})
        self.assertEqual(t["tiers"], {"A": (70, 70), "B": (55, 55)})
        self.assertEqual(t["rubric_status"], "DRAFT")
        self.assertEqual(t["dims"][0]["seen"], "18/20")

    def test_tier_needs_both(self):
        # get = 50+30+20 = 100; want = 12+8 = 20 -> overall 60 but not A or B
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt", "dimensions": dims2(5, 5, 5, 1, 1)})
        self.assertEqual((r["get"], r["want"], r["score"], r["tier"]), (100, 20, 60, "C"))
        self.assertTrue(r["draft"])
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt", "dimensions": dims2(4, 4, 4, 4, 4)})
        self.assertEqual((r["get"], r["want"], r["tier"]), (80, 80, "A"))
        r = jb.score(self.ws, {"jd_file": "jds/tessel.txt", "dimensions": dims2(3, 3, 3, 5, 4)})
        self.assertEqual((r["get"], r["want"], r["tier"]), (60, 92, "B"))

    def test_quality_check_passes_good_rubric(self):
        r = jb.rubric_check(self.ws)[0]
        self.assertEqual(r["problems"], [])
        self.assertTrue(r["ok"])
        # the only warning is the reminder that 'Hybrid days' sits next to the location deal-breaker
        self.assertEqual([w for w in r["warnings"] if "deal-breaker about location" not in w], [])

    def test_quality_check_catches_weak_rubric(self):
        p = self.ws / "profile.md"
        bad = (p.read_text().replace("| Core RevOps work | 50 | Owns routing, forecasting and CRM end to end",
                                     "| Core RevOps work | 50 | Great match")
               .replace("| 18/20 |", "|  |").replace("| Hybrid days | 40 |", "| Hybrid days | 30 |"))
        p.write_text(bad)
        r = jb.rubric_check(self.ws)[0]
        self.assertTrue(any("add up to 90" in x for x in r["problems"]))
        self.assertTrue(any("vague" in w and "Core RevOps work" in w for w in r["warnings"]))
        self.assertTrue(any("isn't grounded" in w for w in r["warnings"]))
        self.assertFalse(r["ok"])

    def test_legacy_rubric_is_flagged_not_broken(self):
        ws = make_ws()
        r = jb.rubric_check(ws)[0]
        self.assertTrue(any("older one-score rubric" in w for w in r["warnings"]))
        self.assertEqual(jb.score(ws, {"jd_file": "jds/tessel.txt", "dimensions": dims()})["score"], 88)

    def test_market_counts(self):
        m = self.ws / "jds" / "market"
        m.mkdir()
        (m / "a.txt").write_text("We use Salesforce (SFDC) daily. Forecasting is key.")
        (m / "b.txt").write_text("HubSpot admin; sfdc a plus")
        (m / "c.txt").write_text("Python and dbt")
        r = jb.market_counts(self.ws, "Salesforce/SFDC, forecasting, Python, Marketo")
        got = {t["term"]: t["seen_in"] for t in r["terms"]}
        self.assertEqual(got, {"Salesforce/SFDC": "2/3", "forecasting": "1/3", "Python": "1/3", "Marketo": "0/3"})

    def _score_roles(self, n_good, n_mid, n_bad):
        roles = []
        for i in range(n_good):
            roles.append((f"Good{i}", (5, 4, 4, 4, 4), "great"))
        for i in range(n_mid):
            roles.append((f"Mid{i}", (3, 3, 4, 3, 4), "okay"))
        for i in range(n_bad):
            roles.append((f"Bad{i}", (2, 2, 2, 1, 1), "no"))
        for c, sc, _ in roles:
            (self.ws / "jds" / f"{c} - Ops.txt").write_text(JD)
            jb.score(self.ws, {"company": c, "role": "Ops", "jd_file": f"jds/{c} - Ops.txt", "dimensions": dims2(*sc)})
        return [{"company": c, "role": "Ops", "verdict": v} for c, _, v in roles]

    def test_calibration_passes_and_marks_profile(self):
        items = self._score_roles(3, 3, 2)
        r = jb.calibrate(self.ws, items, apply=True)
        self.assertEqual((r["rated"], r["agree"], r["passed"]), (8, 8, True))
        self.assertIn("Rubric status: CALIBRATED (8/8 agreed", (self.ws / "profile.md").read_text())
        self.assertFalse(jb.parse_tracks((self.ws / "profile.md").read_text())[0]["rubric_status"].startswith("DRAFT"))

    def test_calibration_fails_with_two_disagreements(self):
        items = self._score_roles(3, 3, 2)
        items[0]["verdict"] = "no"
        items[1]["verdict"] = "okay"
        r = jb.calibrate(self.ws, items, apply=True)
        self.assertEqual((r["agree"], r["passed"]), (6, False))
        self.assertEqual(len(r["disagreements"]), 2)
        self.assertIn("Rubric status: DRAFT", (self.ws / "profile.md").read_text())

    def test_calibration_needs_eight(self):
        r = jb.calibrate(self.ws, self._score_roles(2, 2, 1))
        self.assertFalse(r["passed"])
        self.assertIn("at least 8", r["note"])

    def test_gap_report_with_two_parts(self):
        (self.ws / "jds" / "W - Eng.txt").write_text(JD)
        jb.score(self.ws, {"company": "W", "role": "Eng", "jd_file": "jds/W - Eng.txt", "dimensions": dims2(4, 2, 4, 4, 4),
                           "gaps": [{"skill": "Salesforce", "dimension": "Tools asked for", "score_if_closed": 5}]})
        top = jb.gap_report(self.ws)["skills"][0]
        # get 40+12+16=68 (B) -> 40+30+16=86 (A); want 80
        self.assertEqual(top["tier_upgrades"], ["W, Eng: 74 B -> 83 A"])


class Seen(unittest.TestCase):
    def test_add_and_check(self):
        ws = make_ws()
        r = jb.seen(ws, "add", ["Wayflyer|GTM Engineer", "wayflyer|gtm  engineer", "Hopper|RevOps Manager"])
        self.assertEqual(len(r["added"]), 2)
        r = jb.seen(ws, "check", ["Way-Flyer|GTM Engineer", "Stripe|RevOps Lead"])
        self.assertEqual(r["unseen"], ["Stripe|RevOps Lead"])
        self.assertEqual(r["already_seen"], 1)

    def test_key_matches_collector(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not installed")
        js = (SKILL / "scripts/collector.js").read_text() + \
            "\nconsole.log(JSON.stringify(['Way Flyer Ltd.','A  B  Role'].length && JSA.key('Way Flyer Ltd.', '  GTM   Engineer ')))"
        p = subprocess.run([node, "-e", "globalThis.window=globalThis;" + js], capture_output=True, text=True)
        self.assertEqual(json.loads(p.stdout.strip().splitlines()[-1]), jb.key("Way Flyer Ltd.", "  GTM   Engineer "))


@unittest.skipUnless(HAS_XL, "openpyxl not installed")
class Tracker(unittest.TestCase):
    def setUp(self):
        self.ws = make_ws()

    def test_template_layout_is_valid(self):
        jb.load_tracker(self.ws)

    def test_upsert_add_then_update(self):
        r = jb.tracker_upsert(self.ws, [{"Company": "Tessel", "Role": "RevOps Manager", "Fit Score": 88, "Tier": "A",
                                          "Date Posted": "2026-10-20", "Track": "Revenue Operations"},
                                         {"Company": "Hopper", "Role": "Sr Manager RevOps", "Tier": "B"}])
        self.assertEqual([x["action"] for x in r], ["added", "added"])
        self.assertEqual([x["id"] for x in r], [1, 2])
        r = jb.tracker_upsert(self.ws, {"Company": "tessel", "Role": "revops  manager", "Status": "Applied",
                                        "Date Applied": "2026-10-31"})
        self.assertEqual((r[0]["action"], r[0]["id"]), ("updated", 1))
        rows = jb.tracker_list(self.ws, all_cols=True)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Status"], "Applied")
        self.assertEqual(rows[0]["Fit Score"], 88)  # untouched fields kept
        self.assertEqual(rows[0]["Date Posted"], "2026-10-20")
        self.assertEqual(rows[1]["Status"], "Found")
        import openpyxl
        s = openpyxl.load_workbook(self.ws / "tracker.xlsx")["Applications"]
        self.assertTrue(str(s["T2"].value).startswith("=IF("))
        self.assertIn('N2="Final"', s["U2"].value)

    def test_upsert_rejects_protected_and_unknown_columns(self):
        for bad in ({"Company": "X", "Role": "Y", "Applied?": 1}, {"Company": "X", "Role": "Y", "Salary": 1},
                    {"Company": "X"}):
            with self.assertRaises(jb.Fail):
                jb.tracker_upsert(self.ws, bad)

    def test_moved_fixed_column_is_refused(self):
        import openpyxl
        wb = openpyxl.load_workbook(self.ws / "tracker.xlsx")
        wb["Applications"]["M1"] = "State"
        wb.save(self.ws / "tracker.xlsx")
        with self.assertRaises(jb.Fail):
            jb.tracker_list(self.ws, False)


@unittest.skipUnless(HAS_XL, "openpyxl not installed")
class Dashboard(unittest.TestCase):
    def setUp(self):
        self.ws = make_ws()

    def test_written_on_upsert_and_on_demand(self):
        self.assertFalse((self.ws / "dashboard.html").exists())
        jb.tracker_upsert(self.ws, {"Company": "Tessel", "Role": "RevOps Manager", "Tier": "A", "Fit Score": 88})
        page = (self.ws / "dashboard.html").read_text()
        self.assertIn('"Company": "Tessel"', page)
        self.assertEqual(jb.build_dashboard(self.ws)["roles"], 1)

    def test_tracker_text_cannot_break_out_of_the_data_block(self):
        evil = "</script><script>alert(1)</script>"
        jb.tracker_upsert(self.ws, {"Company": evil, "Role": "x", "Notes": "<img src=x onerror=alert(1)>"})
        page = (self.ws / "dashboard.html").read_text()
        data = page.split('<script id="data" type="application/json">')[1].split("</script>")[0]
        self.assertNotIn("<", data)
        self.assertEqual(json.loads(data)["rows"][0]["Company"], evil)

    def test_snapshot_holds_only_shown_columns(self):
        jb.tracker_upsert(self.ws, {"Company": "Tessel", "Role": "RevOps Manager", "Tier": "A",
                                    "Notes": "Recruiter: Jane Doe, 087 000 0000", "Top Gap": "Python"})
        snap = json.loads((self.ws / "dashboard-data.json").read_text())
        row = snap["rows"][0]
        self.assertEqual(row["Company"], "Tessel")
        self.assertNotIn("Notes", row)
        self.assertNotIn("Top Gap", row)
        self.assertNotIn("Jane", json.dumps(snap))

    def test_artifact_page_has_no_data_or_skeleton(self):
        jb.tracker_upsert(self.ws, {"Company": "Tessel", "Role": "RevOps Manager"})
        jb.build_dashboard(self.ws, artifact_page=True)
        page = (self.ws / "dashboard-artifact.html").read_text()
        self.assertTrue(page.startswith("<title>"))
        for tag in ("<!doctype", "<html", "<head>", "<body>"):
            self.assertNotIn(tag, page.lower())
        data = page.split('<script id="data" type="application/json">')[1].split("</script>")[0]
        self.assertEqual(json.loads(data), {"mode": "artifact", "rows": [], "gaps": {}})
        self.assertNotIn("Tessel", page)

    def test_greeting_uses_first_name_and_active_tracks_only(self):
        p = self.ws / "profile.md"
        p.write_text(p.read_text().replace("- Name:", "- Name: Sam Doyle", 1))
        self.assertEqual(jb.dashboard_person(self.ws), {"name": "Sam", "tracks": ["Revenue Operations"], "draft": False})
        jb.tracker_upsert(self.ws, {"Company": "Tessel", "Role": "RevOps Manager"})
        snap = json.loads((self.ws / "dashboard-data.json").read_text())
        self.assertEqual(snap["person"]["name"], "Sam")
        self.assertNotIn("Doyle", json.dumps(snap))

    def test_no_name_means_no_greeting_name(self):
        self.assertEqual(jb.dashboard_person(self.ws)["name"], "")
        p = self.ws / "profile.md"
        p.write_text(p.read_text().replace("- Name:", "- Name: <script>", 1))
        self.assertEqual(jb.dashboard_person(self.ws)["name"], "")

    def test_no_external_requests(self):
        jb.build_dashboard(self.ws)
        page = (self.ws / "dashboard.html").read_text()
        self.assertNotRegex(page, r'(src|href)\s*=\s*"https?:')
        self.assertNotIn("@import", page)


class Migrate(unittest.TestCase):
    def test_v0_to_v1(self):
        ws = make_ws(version=False)
        shutil.rmtree(ws / "jds")
        self.assertTrue(jb.check(ws)["needs_migration"])
        r = jb.migrate(ws)
        self.assertEqual((r["from"], r["to"]), (0, 2))
        self.assertEqual(len(r["backups"]), 2)
        for b in r["backups"]:
            self.assertTrue((ws / b).is_file())
        self.assertEqual(jb.workspace_version((ws / "profile.md").read_text()), 2)
        self.assertTrue((ws / "jds").is_dir())
        self.assertIn("Status: NOT SET UP\nWorkspace version: 2", (ws / "profile.md").read_text())
        self.assertEqual(jb.migrate(ws)["changes"], ["already up to date"])

    @unittest.skipUnless(HAS_XL, "openpyxl not installed")
    def test_v1_to_v2_adds_score_columns(self):
        import openpyxl
        ws = make_ws()
        p = ws / "profile.md"
        p.write_text(p.read_text().replace("Workspace version: 2", "Workspace version: 1"))
        wb = openpyxl.load_workbook(ws / "tracker.xlsx")
        wb["Applications"]["W1"], wb["Applications"]["X1"] = None, None
        wb.save(ws / "tracker.xlsx")
        r = jb.migrate(ws)
        self.assertEqual((r["from"], r["to"]), (1, 2))
        heads = [c.value for c in openpyxl.load_workbook(ws / "tracker.xlsx")["Applications"][1]]
        self.assertEqual(heads[-2:], ["Get Score", "Want Score"])
        jb.tracker_upsert(ws, {"Company": "Tessel", "Role": "RevOps Manager", "Get Score": 82, "Want Score": 74})

    def test_refuses_newer_workspace(self):
        ws = make_ws()
        p = ws / "profile.md"
        p.write_text(p.read_text().replace("Workspace version: 2", "Workspace version: 99"))
        with self.assertRaises(jb.Fail):
            jb.migrate(ws)

    def test_backups_are_gitignored_pattern(self):
        ws = make_ws(version=False)
        names = jb.migrate(ws)["backups"]
        self.assertTrue(all(".backup-" in n for n in names))


if __name__ == "__main__":
    unittest.main()
