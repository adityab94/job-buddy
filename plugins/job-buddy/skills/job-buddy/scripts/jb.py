#!/usr/bin/env python3
"""Job Buddy core: the parts that must be exact, so Claude doesn't redo them by hand each time.

Claude judges (dimension scores, evidence, wording); this script does the arithmetic, checks the
evidence against the saved job ad, and reads and writes the workspace files.

Usage (WORKSPACE is the user's job-search folder; JSON goes in on stdin and comes out on stdout):
  jb.py check   WORKSPACE                 workspace version, missing files, whether openpyxl is present
  jb.py migrate WORKSPACE                 back up, then bring an older workspace up to date
  jb.py rubric  WORKSPACE [--track T] [--check]   tracks and tiers; --check runs the quality check
  jb.py market  WORKSPACE --terms "a/b, c"        how many saved market ads (jds/market/) mention each
  jb.py calibrate WORKSPACE [--track T] [--apply]  [{"company","role","verdict": great|okay|no}]
  jb.py score   WORKSPACE                 {"track", "company", "role", "jd_file",
                                           "dimensions": {name: {"score", "quote"}},
                                           "gaps": [{"skill", "dimension", "score_if_closed"}]}
  jb.py gaps    WORKSPACE [--track T] [--names]   which missing skills hold back the most roles
  jb.py seen    WORKSPACE check|add       lines of "company|title" on stdin
  jb.py tracker WORKSPACE list [--all]    tracker rows as JSON
  jb.py tracker WORKSPACE upsert          [{"Company", "Role", ...column: value}] on stdin
  jb.py dashboard WORKSPACE [--artifact-page]   write dashboard.html and dashboard-data.json (also
                                          after every upsert); --artifact-page adds the page to publish once

Exit codes: 0 ok, 2 bad input, 3 file open elsewhere (close it and retry), 4 openpyxl missing.
Standard library only, except the tracker commands and migration's tracker step (openpyxl).
"""
import datetime as dt
import json
import math
import re
import shutil
import sys
from pathlib import Path

WORKSPACE_VERSION = 2

# Applications sheet layout. The Funnel sheet's formulas point at J (Tier), M (Status),
# T (Applied?) and U (Callback?) by letter, so those positions are fixed; everything else is
# found by header name.
HEADERS = ["ID", "Date Found", "Company", "Role", "Location", "Source", "Job URL", "Date Posted",
           "Fit Score", "Tier", "Top Gap", "Materials", "Status", "Rejected At", "Date Applied",
           "Last Update", "Days to Response", "Notes", "Next Action", "Applied?", "Callback?", "Track",
           "Get Score", "Want Score"]
FIXED = {"Tier": "J", "Status": "M", "Rejected At": "N", "Applied?": "T", "Callback?": "U"}
FORMULA_COLS = ("Applied?", "Callback?")
DATE_COLS = {"Date Found", "Date Posted", "Date Applied", "Last Update"}
MAX_ROW = 501  # the Funnel formulas cover rows 2-501
SHORT_LIST = ["ID", "Company", "Role", "Fit Score", "Tier", "Status", "Track", "Last Update", "Next Action"]


class Fail(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


def formulas(r):
    return {
        "Applied?": f'=IF(OR(M{r}="",M{r}="Found"),0,1)',
        "Callback?": f'=IF(OR(M{r}="Assessment",M{r}="Interview",M{r}="Offer",AND(M{r}="Rejected",'
                     f'OR(N{r}="Assessment",N{r}="Interview",N{r}="Final"))),1,0)',
    }


def key(company, title):
    """Same key as collector.js: company without non-alphanumerics, title with spaces collapsed."""
    c = re.sub(r"[^a-z0-9]", "", (company or "").lower())
    t = re.sub(r"\s+", " ", (title or "").lower()).strip()
    return f"{c}|{t}"


def half_up(x):
    """72.5 -> 73. Python's round() rounds halves to even (72.5 -> 72), which can drop a tier."""
    return int(math.floor(x + 0.5))


def today():
    return dt.date.today()


def out(obj):
    print(json.dumps(obj, indent=1, ensure_ascii=False, default=str))


def read_stdin_json():
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        raise Fail(f"stdin is not valid JSON: {e}")


# ---------- workspace and profile ----------

def workspace(path):
    ws = Path(path).expanduser()
    if not (ws / "profile.md").is_file():
        raise Fail(f"no profile.md in {ws}: is this the job-search folder?")
    return ws


def workspace_version(profile_text):
    m = re.search(r"^Workspace version:\s*(\d+)", profile_text, re.M)
    return int(m.group(1)) if m else 0


def _cells(line):
    t = line.strip()
    return [c.strip() for c in t.strip("|").split("|")] if t.startswith("|") else None


def parse_tracks(profile_text):
    """Tracks from profile.md: '## Track N: name' sections with their rubric and tiers.

    Current rubrics have two parts, '#### Can I get it?' and '#### Do I want it?', each a table
    (Dimension | Weight | 5 looks like | 3 looks like | 1 looks like | Seen in) whose weights add
    to 100, and tiers like 'Tier A: Get 70+ and Want 70+'. Older one-table rubrics with tiers like
    'Tier A: 75+' still work ("single" mode)."""
    tracks = []
    for part in re.split(r"^## (?=Track\b)", profile_text, flags=re.M)[1:]:
        part = re.split(r"^## (?!#)", part, maxsplit=1, flags=re.M)[0]  # stop at the next top section
        m = re.match(r"Track\s*(\d+)?\s*:?\s*(.*)", part.splitlines()[0])
        num, name = (m.group(1) or ""), m.group(2).strip()
        status = re.search(r"^- Status:\s*(\S+)", part, re.M)
        rstatus = re.search(r"^- Rubric status:\s*(.+)$", part, re.M)
        dims, header, section = [], None, "single"
        for line in part.splitlines():
            h4 = re.match(r"^####\s+(.*)", line)
            if h4:
                low = h4.group(1).lower()
                section = "get" if "get" in low else "want" if "want" in low else "single"
                continue
            cells = _cells(line)
            if not cells:
                header = None
                continue
            low = [c.lower() for c in cells]
            if len(low) >= 2 and low[0] == "dimension" and low[1] == "weight":
                header = low
                continue
            if header is None or not cells[0] or set(cells[0]) <= set("-: "):
                continue
            try:
                weight = float(cells[1])
            except (ValueError, IndexError):
                continue
            col = lambda *names: next((cells[k] for k, hname in enumerate(header)
                                      if any(n in hname for n in names) and k < len(cells)), "")
            dims.append({"name": cells[0], "weight": weight, "part": section,
                         "a5": col("5 "), "a3": col("3 "), "a1": col("1 "), "seen": col("seen", "evidence")})
        two = {t: (int(g), int(w)) for t, g, w in re.findall(
            r"Tier\s+([A-Z])\s*:\s*Get\s+(\d+)\+?\s*(?:and|&|,)\s*Want\s+(\d+)", part, re.I)}
        mode = "two" if any(d["part"] in ("get", "want") for d in dims) else "single"
        if mode == "two":
            tiers = dict(sorted(two.items(), key=lambda kv: -sum(kv[1])))
        else:
            # "Tier A: 75+", "Tier B: 60-74" give cut-offs; "Tier C: under 60" is the remainder.
            tiers = {t: int(n) for t, n in re.findall(r"Tier\s+([A-Z])\s*:\s*(\d+)", part)}
            tiers = dict(sorted(tiers.items(), key=lambda kv: -kv[1]))
        parts = {}
        for d in dims:
            parts.setdefault(d["part"], {})[d["name"]] = d["weight"]
        tracks.append({"number": num, "name": name, "status": status.group(1) if status else "",
                       "rubric_status": rstatus.group(1).strip() if rstatus else "",
                       "mode": mode, "dims": dims, "parts": parts,
                       "weights": {d["name"]: d["weight"] for d in dims}, "tiers": tiers})
    return tracks


def compute(track, dim_scores):
    """Weighted score(s) and tier from {dimension: 1-5}. Two-part rubrics give a 'get' and a
    'want' score (each 0-100); the overall score is their average and a tier needs both."""
    if track["mode"] == "two":
        sub = {part: half_up(sum(dim_scores[d] / 5 * w for d, w in ws.items()))
               for part, ws in track["parts"].items() if part in ("get", "want")}
        get, want = sub.get("get", 0), sub.get("want", 0)
        tier = next((t for t, (g, w) in track["tiers"].items() if get >= g and want >= w), None)
        if tier is None:
            tier = next((t for t in sorted(set("ABC") | set(track["tiers"])) if t not in track["tiers"]), "C")
        return {"score": half_up((get + want) / 2), "get": get, "want": want, "tier": tier}
    total = half_up(sum(dim_scores[d] / 5 * w for d, w in track["weights"].items()))
    return {"score": total, "get": None, "want": None, "tier": tier_for(total, track["tiers"])}


def find_track(tracks, wanted):
    if not tracks:
        raise Fail("profile.md has no '## Track N: name' section with a rubric yet")
    if not wanted:
        active = [t for t in tracks if t["status"].upper() != "PAUSED"]
        if len(active) == 1:
            return active[0]
        raise Fail("several tracks: say which with 'track' (name or number)")
    w = str(wanted).lower().strip()
    for t in tracks:
        if w == t["number"] or w == t["name"].lower():
            return t
    hits = [t for t in tracks if w in t["name"].lower()]
    if len(hits) == 1:
        return hits[0]
    raise Fail(f"no single track matches '{wanted}'; tracks: {[t['name'] for t in tracks]}")


# ---------- scoring ----------

def norm_text(s):
    s = (s or "").lower()
    s = s.translate(str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                                   "–": "-", "—": "-", " ": " ", "…": "..."}))
    s = re.sub(r"[^\w€$£%+#./'-]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def check_quote(quote, jd_norm):
    q = norm_text(quote)
    if not q:
        return "missing"
    if jd_norm is None:
        return "unverified"
    if q not in jd_norm:
        return "not in job ad"
    return "verified" if len(q.split()) >= 3 else "too short"


def score(ws, req):
    tracks = parse_tracks((ws / "profile.md").read_text(encoding="utf-8"))
    track = find_track(tracks, req.get("track"))
    weights, tiers = track["weights"], track["tiers"]
    problems = []
    if not weights:
        raise Fail(f"track '{track['name']}' has no rubric weights in profile.md")
    for part, ws_ in track["parts"].items():
        if abs(sum(ws_.values()) - 100) > 0.01:
            label = {"get": "'Can I get it?' ", "want": "'Do I want it?' "}.get(part, "")
            problems.append(f"{label}rubric weights add up to {sum(ws_.values()):g}, not 100")

    jd_norm = None
    if req.get("jd_file"):
        jd_path = (ws / req["jd_file"]).resolve()
        if not jd_path.is_file():
            raise Fail(f"job ad file not found: {req['jd_file']}")
        jd_norm = norm_text(jd_path.read_text(encoding="utf-8", errors="replace"))

    given = {k.lower().strip(): v for k, v in (req.get("dimensions") or {}).items()}
    rows = []
    part_of = {d["name"]: d["part"] for d in track["dims"]}
    for dim, weight in weights.items():
        d = given.pop(dim.lower(), None)
        if d is None:
            raise Fail(f"missing score for dimension '{dim}'")
        s = d.get("score") if isinstance(d, dict) else d
        if not isinstance(s, (int, float)) or not 1 <= s <= 5 or (s * 2) % 1:
            raise Fail(f"score for '{dim}' must be 1-5 (halves allowed), got {s!r}")
        pts = s / 5 * weight
        evidence = check_quote(d.get("quote") if isinstance(d, dict) else "", jd_norm)
        rows.append({"dimension": dim, "part": part_of.get(dim, "single"), "weight": weight, "score": s,
                     "points": round(pts, 1), "evidence": evidence})
    if given:
        problems.append(f"ignored dimensions not in the rubric: {sorted(given)}")

    res = compute(track, {r["dimension"]: r["score"] for r in rows})
    total, tier = res["score"], res["tier"]
    gaps = check_gaps(req.get("gaps") or [], {r["dimension"]: r["score"] for r in rows})

    weak = [r["dimension"] for r in rows if r["evidence"] != "verified"]
    invented = [r["dimension"] for r in rows if r["evidence"] == "not in job ad"]
    weak_weight = sum(r["weight"] for r in rows if r["evidence"] != "verified") / max(1, len(track["parts"]))
    confidence = "low" if invented or weak_weight > 30 else ("medium" if weak else "high")
    if invented:
        problems.append("these quotes are not in the saved job ad; recheck them before showing the "
                        f"score: {invented}")
    if jd_norm is None:
        problems.append("no jd_file given, so evidence could not be checked; save the job ad to jds/")

    if track["mode"] == "two":
        near = [f"{lbl} {v} is within 3 points of Tier {t}'s {lbl.lower()} cut-off ({c})"
                for t, (g, w) in tiers.items() for lbl, v, c in (("Get", res["get"], g), ("Want", res["want"], w))
                if abs(v - c) <= 3]
    else:
        near = [f"{total} is within 3 points of the Tier {t} cut-off ({c})" for t, c in tiers.items() if abs(total - c) <= 3]
    draft = track["rubric_status"].upper().startswith("DRAFT")
    result = {"track": track["name"], "score": total, "get": res["get"], "want": res["want"], "tier": tier,
              "draft": draft, "confidence": confidence,
              "dimensions": rows, "gaps": gaps, "unverified": weak, "near_cutoff": near, "problems": problems}

    # Keep the breakdown next to the job ad, so 'gaps' can re-score roles later. Not saved while
    # evidence is invented: Claude fixes the quotes and runs score again.
    if req.get("jd_file") and not invented:
        saved = jd_path.with_name(jd_path.stem + ".score.json")
        saved.write_text(json.dumps({
            "company": req.get("company") or "", "role": req.get("role") or "", "track": track["name"],
            "scored_on": today().isoformat(), "score": total, "get": res["get"], "want": res["want"], "tier": tier,
            "dimensions": {r["dimension"]: r["score"] for r in rows}, "gaps": gaps}, indent=1, ensure_ascii=False),
            encoding="utf-8")
        result["saved"] = saved.relative_to(ws.resolve()).as_posix()
    return result


def tier_for(total, tiers):
    tier = next((t for t, cut in tiers.items() if total >= cut), None)
    if tier is None:
        letters = sorted(set("ABC") | set(tiers))
        tier = next((t for t in letters if t not in tiers), "C")
    return tier


def check_gaps(gaps, dim_scores):
    """Each gap: {"skill", "dimension", "score_if_closed"}: what the dimension would score if the
    user had the skill. Claude's estimate; the script only checks it's consistent."""
    lower = {d.lower(): d for d in dim_scores}
    clean = []
    for g in gaps:
        if not isinstance(g, dict) or not str(g.get("skill") or "").strip():
            raise Fail(f"each gap needs a 'skill': {g}")
        dim = lower.get(str(g.get("dimension") or "").lower().strip())
        if not dim:
            raise Fail(f"gap '{g['skill']}' names dimension {g.get('dimension')!r}, not in the rubric: {list(dim_scores)}")
        to = g.get("score_if_closed")
        if not isinstance(to, (int, float)) or not dim_scores[dim] < to <= 5 or (to * 2) % 1:
            raise Fail(f"gap '{g['skill']}': score_if_closed must be above the current {dim_scores[dim]} and at most 5")
        clean.append({"skill": str(g["skill"]).strip(), "dimension": dim, "score_if_closed": to})
    return clean


# ---------- rubric quality ----------

VAGUE = re.compile(r"^(?:very |really |quite )?(?:great|good|ok|okay|fine|bad|poor|strong|weak|excellent|"
                   r"perfect|ideal|average|decent|some|none|low|high|medium|match|fit|n/?a|-)"
                   r"(?: (?:match|fit|role|job|level))?\.?$", re.I)
STOP = {"and", "or", "the", "a", "of", "to", "in", "for", "fit", "match", "&", "/", "-"}
FILTER_WORDS = {"location": "location", "remote": "location", "commute": "location", "hybrid": "location",
                "salary": "salary", "pay": "salary", "contract": "contract", "visa": "visa", "sponsorship": "visa"}


def rubric_check(ws, track_name=None):
    """Mechanical checks on each track's rubric. 'problems' must be fixed before the rubric is used;
    'warnings' make it weaker. Judgement (are these the right dimensions?) stays with Claude."""
    text = (ws / "profile.md").read_text(encoding="utf-8")
    tracks = parse_tracks(text)
    if track_name:
        tracks = [find_track(tracks, track_name)]
    shared = text.split("## Track")[0].lower()
    out = []
    for t in tracks:
        problems, warnings = [], []
        if not t["dims"]:
            problems.append("no rubric table yet")
        if t["mode"] == "single" and t["dims"]:
            warnings.append("older one-score rubric: rebuild it as 'Can I get it?' and 'Do I want it?' for "
                            "sharper tiers")
        for part, label in (("get", "Can I get it?"), ("want", "Do I want it?"), ("single", "Rubric")):
            ws_ = t["parts"].get(part)
            if ws_ is None:
                if t["mode"] == "two" and part != "single":
                    problems.append(f"'{label}' has no dimensions")
                continue
            n = len(ws_)
            if t["mode"] == "two" and not 2 <= n <= 4:
                problems.append(f"'{label}' has {n} dimensions; use 2 to 4")
            if t["mode"] == "single" and not 4 <= n <= 6:
                warnings.append(f"{n} dimensions; 4 to 6 work best")
            if abs(sum(ws_.values()) - 100) > 0.01:
                problems.append(f"'{label}' weights add up to {sum(ws_.values()):g}, not 100")
            for d, w in ws_.items():
                if w < 5 or w > 60:
                    warnings.append(f"'{d}' weighs {w:g}: below 5 it barely counts, above 60 it decides alone")
        names = [d["name"] for d in t["dims"]]
        for d in t["dims"]:
            for k, label in (("a5", "5"), ("a3", "3"), ("a1", "1")):
                a = d[k].strip()
                if not a:
                    problems.append(f"'{d['name']}' has no '{label} looks like' description")
                elif VAGUE.match(a) or len(a.split()) < 4:
                    warnings.append(f"'{d['name']}' {label}: \"{a}\" is vague; say what you'd see in a job ad")
            if d["a5"] and d["a5"].strip().lower() in (d["a3"].strip().lower(), d["a1"].strip().lower()):
                problems.append(f"'{d['name']}' uses the same description for different scores")
            if d["part"] == "get" and not re.search(r"\d+\s*/\s*\d+", d["seen"]):
                warnings.append(f"'{d['name']}' isn't grounded in real ads yet (no 'Seen in' count like 14/20)")
            hit = {FILTER_WORDS[w] for w in re.findall(r"[a-z]+", d["name"].lower()) if w in FILTER_WORDS}
            for kind in hit:
                if any(w in shared for w, k in FILTER_WORDS.items() if k == kind):
                    warnings.append(f"'{d['name']}' overlaps a deal-breaker about {kind}: score only what's beyond "
                                    "the deal-breaker (e.g. hybrid days), or it gets counted twice")
        for i, a in enumerate(names):
            wa = {w for w in re.findall(r"[a-z]+", a.lower())} - STOP
            for b in names[i + 1:]:
                wb = {w for w in re.findall(r"[a-z]+", b.lower())} - STOP
                if wa and wb and len(wa & wb) / len(wa | wb) >= 0.5:
                    warnings.append(f"'{a}' and '{b}' look like the same thing; merge or sharpen them")
        if t["mode"] == "two":
            if not {"A", "B"} <= set(t["tiers"]):
                problems.append("tiers need 'Tier A: Get NN+ and Want NN+' and the same for Tier B")
            elif not all(a >= b for a, b in zip(t["tiers"]["A"], t["tiers"]["B"])):
                problems.append("Tier A's cut-offs must be at least Tier B's")
        elif not t["tiers"]:
            problems.append("no tier cut-offs")
        out.append({"track": t["name"], "mode": t["mode"], "rubric_status": t["rubric_status"] or "not set",
                    "problems": problems, "warnings": warnings, "ok": not problems})
    return out


def market_counts(ws, terms):
    """How many saved market ads (jds/market/*.txt) mention each requirement. 'a/b' counts either."""
    files = sorted((ws / "jds" / "market").glob("*.txt")) if (ws / "jds" / "market").is_dir() else []
    if not files:
        raise Fail("no market ads saved yet: save 15-25 current ads as jds/market/<Company - Role>.txt")
    texts = [norm_text(f.read_text(encoding="utf-8", errors="replace")) for f in files]
    rows = []
    for term in [t.strip() for t in terms.split(",") if t.strip()]:
        alts = [norm_text(a) for a in term.split("/") if a.strip()]
        pats = [re.compile(r"(?<![\w])" + re.escape(a) + r"(?![\w])") for a in alts]
        n = sum(1 for tx in texts if any(p.search(tx) for p in pats))
        rows.append({"term": term, "ads": n, "seen_in": f"{n}/{len(texts)}"})
    return {"ads": len(texts), "terms": sorted(rows, key=lambda r: -r["ads"])}


VERDICT_TIER = {"great": "A", "okay": "B", "ok": "B", "no": None}


def calibrate(ws, items, track_name=None, apply=False):
    """Compare the user's verdicts on scored roles (great / okay / no) with the rubric's tiers.
    Passes at 8+ roles with at least 7 in 8 agreeing; with apply, marks the rubric CALIBRATED."""
    text = (ws / "profile.md").read_text(encoding="utf-8")
    track = find_track(parse_tracks(text), track_name)
    files = {}
    for p in (ws / "jds").glob("*.score.json") if (ws / "jds").is_dir() else []:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        files[key(d.get("company"), d.get("role"))] = d
    agree, rows, missing = 0, [], []
    for it in items:
        verdict = str(it.get("verdict", "")).lower().strip()
        if verdict not in VERDICT_TIER:
            raise Fail(f"verdict must be great, okay or no: {it}")
        d = files.get(key(it.get("company"), it.get("role")))
        if not d or set(map(str.lower, track["weights"])) != set(map(str.lower, d.get("dimensions", {}))):
            missing.append(f"{it.get('company')}, {it.get('role')}")
            continue
        dims = {n: d["dimensions"][next(k for k in d["dimensions"] if k.lower() == n.lower())] for n in track["weights"]}
        got = compute(track, dims)
        want_tier = VERDICT_TIER[verdict]
        ok = got["tier"] == want_tier if want_tier else got["tier"] not in ("A", "B")
        agree += ok
        if not ok:
            low = sorted(dims.items(), key=lambda kv: kv[1])[:2]
            high = sorted(dims.items(), key=lambda kv: -kv[1])[:2]
            rows.append({"role": f"{d.get('company')}, {d.get('role')}", "you_said": verdict,
                         "rubric_gave": got["tier"], "get": got["get"], "want": got["want"], "score": got["score"],
                         "lowest": dict(low), "highest": dict(high)})
    total = agree + len(rows)
    need = -(-total * 7 // 8)  # ceil(7/8 of total)
    passed = total >= 8 and agree >= need
    result = {"track": track["name"], "rated": total, "agree": agree, "needed": max(need, 7) if total < 8 else need,
              "passed": passed, "disagreements": rows, "not_scored": missing}
    if total < 8:
        result["note"] = f"rate at least 8 scored roles (have {total})"
    if passed and apply:
        stamp = f"- Rubric status: CALIBRATED ({agree}/{total} agreed, {today().isoformat()})"
        sections = re.split(r"(?=^## )", text, flags=re.M)
        for i, sec in enumerate(sections):
            if sec.startswith("## Track") and parse_tracks(sec)[0]["name"] == track["name"]:
                if re.search(r"^- Rubric status:.*$", sec, re.M):
                    sec = re.sub(r"^- Rubric status:.*$", stamp, sec, count=1, flags=re.M)
                else:
                    sec = re.sub(r"^(### Rubric[^\n]*\n)", r"\1" + stamp + "\n", sec, count=1, flags=re.M)
                sections[i] = sec
        (ws / "profile.md").write_text("".join(sections), encoding="utf-8")
        result["profile_updated"] = True
    return result


# ---------- gap economics ----------

OPEN = {"", "found", "applied", "acknowledged", "assessment", "interview"}
MIN_ROLES = 8  # below this, the gap plan is labelled an early hunch (matches outcomes.md's spirit)


def skill_key(s):
    return re.sub(r"[^a-z0-9+#.]+", " ", (s or "").lower()).strip()


def statuses(ws):
    """Tracker Status and Top Gap by company|role key, if the tracker can be read."""
    try:
        wb, sheet, cols, _ = load_tracker(ws)
    except Fail:
        return None
    rows = {}
    for r in data_rows(sheet, cols):
        k = key(sheet[f"{cols['Company']}{r}"].value, sheet[f"{cols['Role']}{r}"].value)
        rows[k] = {"status": str(sheet[f"{cols['Status']}{r}"].value or ""),
                   "top_gap": str(sheet[f"{cols['Top Gap']}{r}"].value or "") if "Top Gap" in cols else ""}
    return rows


def gap_report(ws, track_name=None):
    tracks = parse_tracks((ws / "profile.md").read_text(encoding="utf-8"))
    track_of = {t["name"]: t for t in tracks}
    tracker = statuses(ws)
    roles, skipped = [], []
    for p in sorted((ws / "jds").glob("*.score.json")) if (ws / "jds").is_dir() else []:
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            skipped.append(f"{p.name}: unreadable")
            continue
        t = track_of.get(s.get("track"))
        if track_name and (not t or t is not find_track(tracks, track_name)):
            continue
        if not t or set(map(str.lower, t["weights"])) != set(map(str.lower, s.get("dimensions", {}))):
            skipped.append(f"{p.name}: rubric changed since it was scored; re-score it to include it")
            continue
        dims = {d: s["dimensions"][next(k for k in s["dimensions"] if k.lower() == d.lower())] for d in t["weights"]}
        base = compute(t, dims)
        info = (tracker or {}).get(key(s.get("company"), s.get("role")), {})
        roles.append({"company": s.get("company"), "role": s.get("role"), "track": t, "dims": dims,
                      "score": base["score"], "tier": base["tier"],
                      "status": info.get("status", ""), "gaps": s.get("gaps") or []})

    skills = {}
    for r in roles:
        is_open = r["status"].lower() in OPEN
        for g in r["gaps"]:
            k = skill_key(g["skill"])
            e = skills.setdefault(k, {"names": {}, "roles": 0, "open_roles": 0, "rejected_roles": 0,
                                       "points": [], "upgrades": []})
            e["names"][g["skill"]] = e["names"].get(g["skill"], 0) + 1
            e["roles"] += 1
            e["open_roles"] += is_open
            e["rejected_roles"] += r["status"].lower() == "rejected"
            dims = dict(r["dims"])
            dims[g["dimension"]] = max(dims[g["dimension"]], g["score_if_closed"])
            after = compute(r["track"], dims)
            new, new_tier = after["score"], after["tier"]
            e["points"].append(new - r["score"])
            if new_tier != r["tier"] and is_open:
                e["upgrades"].append(f"{r['company']}, {r['role']}: {r['score']} {r['tier']} -> {new} {new_tier}")

    ranked = sorted(skills.values(), key=lambda e: (-sum(u.endswith(" A") for u in e["upgrades"]), -len(e["upgrades"]),
                                                    -e["roles"], -sum(e["points"])))
    out_skills = [{"skill": max(e["names"], key=e["names"].get), "roles_with_gap": e["roles"],
                   "open_roles_with_gap": e["open_roles"], "rejected_roles_with_gap": e["rejected_roles"],
                   "avg_points_if_closed": round(sum(e["points"]) / len(e["points"]), 1),
                   "tier_upgrades": e["upgrades"]} for e in ranked]

    # Roles scored before 0.6 have no score file; their tracker 'Top Gap' text still counts.
    scored = {key(r["company"], r["role"]) for r in roles}
    legacy = {}
    for k, info in (tracker or {}).items():
        if k not in scored and info["top_gap"].strip():
            g = info["top_gap"].strip()
            legacy[g] = legacy.get(g, 0) + 1
    notes = []
    if len(roles) < MIN_ROLES:
        notes.append(f"only {len(roles)} roles have a saved score breakdown: treat this as an early hunch")
    if tracker is None:
        notes.append("tracker not read (openpyxl missing?), so every role counts as open")
    return {"roles_analysed": len(roles), "skills": out_skills,
            "top_gap_column": dict(sorted(legacy.items(), key=lambda kv: -kv[1])),
            "known_skill_names": sorted({max(e["names"], key=e["names"].get) for e in skills.values()}),
            "skipped": skipped, "notes": notes}


# ---------- seen list ----------

def seen_keys(ws):
    p = ws / "seen.txt"
    keys = set()
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split("|")
            if len(parts) >= 2 and not line.startswith("#"):
                keys.add(key(parts[0], parts[1]))
    return keys


def seen(ws, action, lines):
    known = seen_keys(ws)
    pairs = [l.split("|")[:2] for l in lines if "|" in l]
    if action == "check":
        return {"unseen": [f"{c}|{t}" for c, t in pairs if key(c, t) not in known],
                "already_seen": sum(1 for c, t in pairs if key(c, t) in known)}
    added = []
    with (ws / "seen.txt").open("a", encoding="utf-8") as f:
        for c, t in pairs:
            k = key(c, t)
            if k not in known:
                known.add(k)
                f.write(f"{c.strip()}|{t.strip()}|{today().isoformat()}\n")
                added.append(f"{c.strip()}|{t.strip()}")
    return {"added": added, "skipped_existing": len(pairs) - len(added)}


# ---------- tracker ----------

def need_openpyxl():
    try:
        import openpyxl  # noqa: F401
        return openpyxl
    except ImportError:
        raise Fail("openpyxl is not installed (pip install openpyxl); update the tracker by hand "
                   "following references/outcomes.md", 4)


def load_tracker(ws):
    openpyxl = need_openpyxl()
    path = ws / "tracker.xlsx"
    if not path.is_file():
        raise Fail("tracker.xlsx not found in the workspace")
    wb = openpyxl.load_workbook(path)
    if "Applications" not in wb.sheetnames:
        raise Fail("tracker.xlsx has no 'Applications' sheet")
    ws_ = wb["Applications"]
    cols = {}
    for cell in ws_[1]:
        if cell.value:
            cols[str(cell.value).strip()] = cell.column_letter
    for name, letter in FIXED.items():
        if cols.get(name) != letter:
            raise Fail(f"tracker column '{name}' must be in column {letter} (the Funnel sheet depends on it); "
                       f"found {cols.get(name)}. Move it back, or run 'migrate'.")
    return wb, ws_, cols, path


def save_tracker(wb, path):
    try:
        wb.save(path)
    except PermissionError:
        raise Fail("tracker.xlsx is open in another app; close it and try again", 3)


def cell_out(v):
    if isinstance(v, dt.datetime):
        return v.date().isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    return v


def data_rows(sheet, cols):
    c = cols["Company"]
    for r in range(2, sheet.max_row + 1):
        if sheet[f"{c}{r}"].value not in (None, ""):
            yield r


def tracker_list(ws, all_cols):
    wb, sheet, cols, _ = load_tracker(ws)
    names = HEADERS if all_cols else SHORT_LIST
    return [{n: cell_out(sheet[f"{cols[n]}{r}"].value) for n in names if n in cols and n not in FORMULA_COLS}
            for r in data_rows(sheet, cols)]


def to_cell(name, v):
    if name in DATE_COLS and isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return dt.date.fromisoformat(v)
    return v


def tracker_upsert(ws, rows):
    if isinstance(rows, dict):
        rows = [rows]
    wb, sheet, cols, path = load_tracker(ws)
    index, next_id, first_free = {}, 1, 2
    for r in data_rows(sheet, cols):
        index[key(sheet[f"{cols['Company']}{r}"].value, sheet[f"{cols['Role']}{r}"].value)] = r
        rid = sheet[f"{cols['ID']}{r}"].value
        if isinstance(rid, (int, float)):
            next_id = max(next_id, int(rid) + 1)
        first_free = r + 1
    result = []
    for row in rows:
        if not row.get("Company") or not row.get("Role"):
            raise Fail(f"each row needs Company and Role: {row}")
        unknown = [k for k in row if k not in cols or k in FORMULA_COLS or k == "ID"]
        if unknown:
            raise Fail(f"unknown or protected columns {unknown}; columns are {list(cols)}")
        k = key(row["Company"], row["Role"])
        r = index.get(k)
        new = r is None
        if new:
            r = first_free
            if r > MAX_ROW:
                raise Fail(f"tracker is full ({MAX_ROW - 1} rows); archive old rows to another sheet first")
            first_free += 1
            index[k] = r
            sheet[f"{cols['ID']}{r}"] = next_id
            next_id += 1
            row.setdefault("Date Found", today().isoformat())
            row.setdefault("Status", "Found")
        for name, v in row.items():
            c = sheet[f"{cols[name]}{r}"]
            c.value = to_cell(name, v)
            if name in DATE_COLS and isinstance(c.value, dt.date):
                c.number_format = "DD-MMM-YYYY"
        last = sheet[f"{cols['Last Update']}{r}"]
        last.value, last.number_format = today(), "DD-MMM-YYYY"
        for name, f in formulas(r).items():
            sheet[f"{cols[name]}{r}"] = f
        result.append({"row": r, "id": sheet[f"{cols['ID']}{r}"].value, "action": "added" if new else "updated",
                       "company": row["Company"], "role": row["Role"]})
    save_tracker(wb, path)
    try:
        build_dashboard(ws)
    except Exception:  # noqa: BLE001 - the tracker write succeeded; the page is refreshed next time
        pass
    return result


def dashboard_person(ws):
    """First name and active track names from profile.md, for the dashboard's greeting."""
    text = (ws / "profile.md").read_text(encoding="utf-8")
    m = re.search(r"^- Name:[ \t]*(\S[^\n]*)$", text, re.M)
    first = m.group(1).strip().split()[0] if m else ""
    if not re.fullmatch(r"[^\W\d_][\w'-]{0,40}", first or "-"):
        first = ""
    active = [t for t in parse_tracks(text) if t["status"].upper() != "PAUSED" and t["name"] and "<" not in t["name"]]
    draft = any(t["rubric_status"].upper().startswith("DRAFT") for t in active)
    return {"name": first, "tracks": [t["name"] for t in active], "draft": draft}


SNAPSHOT_LIMIT = 240_000  # the artifact store holds documents up to 256 KiB


def build_dashboard(ws, artifact_page=False):
    """dashboard.html (local, data embedded) and dashboard-data.json (the snapshot Claude writes to
    the user's private dashboard artifact). With artifact_page, also dashboard-artifact.html: the
    data-free page published once as that artifact."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import dashboard
    rows = tracker_list(ws, all_cols=True)
    gaps, generated, person = gap_report(ws), today().isoformat(), dashboard_person(ws)
    (ws / "dashboard.html").write_text(dashboard.render(rows, gaps, generated, person), encoding="utf-8")
    snap = dashboard.snapshot(rows, gaps, generated, person)
    blob = json.dumps(snap, ensure_ascii=False, default=str)
    result = {"written": ["dashboard.html", "dashboard-data.json"], "roles": len(rows), "snapshot_bytes": len(blob.encode())}
    if len(blob.encode()) > SNAPSHOT_LIMIT:
        # Too big for one store document: drop closed roles' notes first, then closed roles.
        for r in snap["rows"]:
            if r.get("Status") in ("Rejected", "Withdrawn", "Ghosted"):
                r.pop("Notes", None)
        blob = json.dumps(snap, ensure_ascii=False, default=str)
        if len(blob.encode()) > SNAPSHOT_LIMIT:
            snap["rows"] = [r for r in snap["rows"] if r.get("Status") not in ("Rejected", "Withdrawn", "Ghosted")]
            blob = json.dumps(snap, ensure_ascii=False, default=str)
            result["note"] = "closed roles left out of the online dashboard to fit its size limit"
    (ws / "dashboard-data.json").write_text(blob, encoding="utf-8")
    if artifact_page:
        (ws / "dashboard-artifact.html").write_text(dashboard.render_artifact(), encoding="utf-8")
        result["written"].append("dashboard-artifact.html")
    return result


# ---------- check and migrate ----------

EXPECTED = ["profile.md", "tracker.xlsx", "seen.txt", "cv", "outputs", "jds"]


def check(ws):
    text = (ws / "profile.md").read_text(encoding="utf-8")
    v = workspace_version(text)
    try:
        need_openpyxl()
        has_xl = True
    except Fail:
        has_xl = False
    return {"workspace_version": v, "current_version": WORKSPACE_VERSION,
            "needs_migration": v < WORKSPACE_VERSION, "newer_than_skill": v > WORKSPACE_VERSION,
            "missing": [e for e in EXPECTED if not (ws / e).exists()], "openpyxl": has_xl,
            "tracks": [t["name"] for t in parse_tracks(text)]}


def backup(ws, name, from_v):
    src = ws / name
    if not src.is_file():
        return None
    dst = ws / f"{src.stem}.backup-v{from_v}-{today():%Y%m%d}{src.suffix}"
    n = 2
    while dst.exists():
        dst = ws / f"{src.stem}.backup-v{from_v}-{today():%Y%m%d}-{n}{src.suffix}"
        n += 1
    shutil.copy2(src, dst)
    return dst.name


def migrate_0_to_1(ws, done):
    """v0 (Job Buddy 0.3-0.4) -> v1: version line, jds/ folder, Applied?/Callback? formulas on every row."""
    p = ws / "profile.md"
    text = p.read_text(encoding="utf-8")
    if re.search(r"^Status:.*$", text, re.M):
        text = re.sub(r"^(Status:.*)$", rf"\1\nWorkspace version: 1", text, count=1, flags=re.M)
    else:
        text = "Workspace version: 1\n" + text
    p.write_text(text, encoding="utf-8")
    done.append("profile.md: added 'Workspace version: 1'")
    (ws / "jds").mkdir(exist_ok=True)
    done.append("created jds/ for saved job ads")
    try:
        wb, sheet, cols, path = load_tracker(ws)
    except Fail as e:
        if e.code != 4:
            raise
        done.append("tracker formulas skipped (openpyxl not installed); each row gets them when "
                    "'tracker upsert' writes it")
        return
    if "Track" not in cols:
        sheet["V1"] = "Track"
        done.append("tracker: added Track column header (V)")
    for r in range(2, MAX_ROW + 1):
        for name, f in formulas(r).items():
            sheet[f"{FIXED[name]}{r}"] = f
    save_tracker(wb, path)
    done.append(f"tracker: Applied?/Callback? formulas on rows 2-{MAX_ROW}")


def migrate_1_to_2(ws, done):
    """v1 -> v2 (Job Buddy 0.7): two-part rubrics ('Can I get it?' / 'Do I want it?') and the
    tracker columns that hold their scores. Existing one-score rubrics keep working."""
    p = ws / "profile.md"
    p.write_text(re.sub(r"^Workspace version:.*$", "Workspace version: 2", p.read_text(encoding="utf-8"),
                        count=1, flags=re.M), encoding="utf-8")
    done.append("profile.md: Workspace version 2")
    try:
        wb, sheet, cols, path = load_tracker(ws)
    except Fail as e:
        if e.code != 4:
            raise
        done.append("tracker columns skipped (openpyxl not installed)")
        return
    added = []
    for letter, name in (("W", "Get Score"), ("X", "Want Score")):
        if name not in cols:
            if sheet[f"{letter}1"].value not in (None, ""):
                raise Fail(f"tracker column {letter} is already used by '{sheet[f'{letter}1'].value}'")
            sheet[f"{letter}1"] = name
            sheet[f"{letter}1"]._style = sheet["V1"]._style
            added.append(name)
    if added:
        save_tracker(wb, path)
        done.append(f"tracker: added {', '.join(added)} columns")
    done.append("your current rubric still works; ask Job Buddy to rebuild it as 'Can I get it?' and "
                "'Do I want it?' when you're ready")


MIGRATIONS = {0: migrate_0_to_1, 1: migrate_1_to_2}


def migrate(ws):
    v = workspace_version((ws / "profile.md").read_text(encoding="utf-8"))
    if v > WORKSPACE_VERSION:
        raise Fail(f"workspace is version {v} but this Job Buddy only knows up to {WORKSPACE_VERSION}; "
                   "update the plugin")
    if v == WORKSPACE_VERSION:
        return {"from": v, "to": v, "backups": [], "changes": ["already up to date"]}
    backups = [b for b in (backup(ws, "profile.md", v), backup(ws, "tracker.xlsx", v)) if b]
    done, start = [], v
    while v < WORKSPACE_VERSION:
        MIGRATIONS[v](ws, done)
        v += 1
    return {"from": start, "to": v, "backups": backups, "changes": done}


# ---------- entry point ----------

def main(argv):
    if len(argv) < 3 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0 if len(argv) > 1 else 2
    cmd, ws = argv[1], workspace(argv[2])
    rest = argv[3:]
    if cmd == "check":
        out(check(ws))
    elif cmd == "migrate":
        out(migrate(ws))
    elif cmd == "rubric":
        track = rest[rest.index("--track") + 1] if "--track" in rest[:-1] else None
        if "--check" in rest:
            out(rubric_check(ws, track))
        else:
            tracks = parse_tracks((ws / "profile.md").read_text(encoding="utf-8"))
            out([find_track(tracks, track)] if track else tracks)
    elif cmd == "market":
        if "--terms" not in rest[:-1]:
            raise Fail("usage: jb.py market WORKSPACE --terms \"Salesforce/SFDC, forecasting, Python\"")
        out(market_counts(ws, rest[rest.index("--terms") + 1]))
    elif cmd == "calibrate":
        track = rest[rest.index("--track") + 1] if "--track" in rest[:-1] else None
        out(calibrate(ws, read_stdin_json(), track, apply="--apply" in rest))
    elif cmd == "score":
        out(score(ws, read_stdin_json()))
    elif cmd == "gaps":
        report = gap_report(ws, rest[1] if rest[:1] == ["--track"] and len(rest) > 1 else None)
        out({"known_skill_names": report["known_skill_names"]} if "--names" in rest else report)
    elif cmd == "seen" and rest[:1] in (["check"], ["add"]):
        out(seen(ws, rest[0], [l for l in sys.stdin.read().splitlines() if l.strip()]))
    elif cmd == "tracker" and rest[:1] == ["list"]:
        out(tracker_list(ws, "--all" in rest))
    elif cmd == "dashboard":
        out(build_dashboard(ws, artifact_page="--artifact-page" in rest))
    elif cmd == "tracker" and rest[:1] == ["upsert"]:
        out(tracker_upsert(ws, read_stdin_json()))
    else:
        raise Fail(f"unknown command: {' '.join(argv[1:])}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Fail as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(e.code)
