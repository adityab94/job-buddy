#!/usr/bin/env python3
"""Job Buddy core: the parts that must be exact, so Claude doesn't redo them by hand each time.

Claude judges (dimension scores, evidence, wording); this script does the arithmetic, checks the
evidence against the saved job ad, and reads and writes the workspace files.

Usage (WORKSPACE is the user's job-search folder; JSON goes in on stdin and comes out on stdout):
  jb.py check   WORKSPACE                 workspace version, missing files, whether openpyxl is present
  jb.py migrate WORKSPACE                 back up, then bring an older workspace up to date
  jb.py rubric  WORKSPACE [--track T]     tracks with their weights and tier cut-offs
  jb.py score   WORKSPACE                 {"track", "jd_file", "dimensions": {name: {"score", "quote"}}}
  jb.py seen    WORKSPACE check|add       lines of "company|title" on stdin
  jb.py tracker WORKSPACE list [--all]    tracker rows as JSON
  jb.py tracker WORKSPACE upsert          [{"Company", "Role", ...column: value}] on stdin

Exit codes: 0 ok, 2 bad input, 3 file open elsewhere (close it and retry), 4 openpyxl missing.
Standard library only, except the tracker commands and migration's tracker step (openpyxl).
"""
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

WORKSPACE_VERSION = 1

# Applications sheet layout. The Funnel sheet's formulas point at J (Tier), M (Status),
# T (Applied?) and U (Callback?) by letter, so those positions are fixed; everything else is
# found by header name.
HEADERS = ["ID", "Date Found", "Company", "Role", "Location", "Source", "Job URL", "Date Posted",
           "Fit Score", "Tier", "Top Gap", "Materials", "Status", "Rejected At", "Date Applied",
           "Last Update", "Days to Response", "Notes", "Next Action", "Applied?", "Callback?", "Track"]
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


def parse_tracks(profile_text):
    """Tracks from profile.md: '## Track N: name' sections with a Rubric table and Tiers list."""
    tracks = []
    parts = re.split(r"^## (?=Track\b)", profile_text, flags=re.M)[1:]
    for part in parts:
        part = re.split(r"^## (?!#)", part, maxsplit=1, flags=re.M)[0]  # stop at the next top section
        head = part.splitlines()[0]
        m = re.match(r"Track\s*(\d+)?\s*:?\s*(.*)", head)
        num, name = (m.group(1) or ""), m.group(2).strip()
        status = re.search(r"^- Status:\s*(\S+)", part, re.M)
        weights, in_table = {}, False
        for line in part.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else None
            if cells and len(cells) >= 2 and cells[0].lower() == "dimension" and cells[1].lower() == "weight":
                in_table = True
                continue
            if in_table:
                if not cells:
                    in_table = False
                    continue
                if set(cells[0]) <= set("-: ") or not cells[0]:
                    continue
                try:
                    weights[cells[0]] = float(cells[1])
                except ValueError:
                    pass
        # "Tier A: 75+", "Tier B: 60-74" give cut-offs; "Tier C: under 60" is the remainder.
        tiers = {t: int(n) for t, n in re.findall(r"Tier\s+([A-Z])\s*:\s*(\d+)", part)}
        tracks.append({"number": num, "name": name, "status": status.group(1) if status else "",
                       "weights": weights, "tiers": dict(sorted(tiers.items(), key=lambda kv: -kv[1]))})
    return tracks


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
    if abs(sum(weights.values()) - 100) > 0.01:
        problems.append(f"rubric weights add up to {sum(weights.values()):g}, not 100")

    jd_norm = None
    if req.get("jd_file"):
        jd_path = (ws / req["jd_file"]).resolve()
        if not jd_path.is_file():
            raise Fail(f"job ad file not found: {req['jd_file']}")
        jd_norm = norm_text(jd_path.read_text(encoding="utf-8", errors="replace"))

    given = {k.lower().strip(): v for k, v in (req.get("dimensions") or {}).items()}
    rows, total = [], 0.0
    for dim, weight in weights.items():
        d = given.pop(dim.lower(), None)
        if d is None:
            raise Fail(f"missing score for dimension '{dim}'")
        s = d.get("score") if isinstance(d, dict) else d
        if not isinstance(s, (int, float)) or not 1 <= s <= 5 or (s * 2) % 1:
            raise Fail(f"score for '{dim}' must be 1-5 (halves allowed), got {s!r}")
        pts = s / 5 * weight
        total += pts
        evidence = check_quote(d.get("quote") if isinstance(d, dict) else "", jd_norm)
        rows.append({"dimension": dim, "weight": weight, "score": s, "points": round(pts, 1), "evidence": evidence})
    if given:
        problems.append(f"ignored dimensions not in the rubric: {sorted(given)}")

    total = round(total)
    tier = next((t for t, cut in tiers.items() if total >= cut), None)
    if tier is None:
        letters = sorted(set("ABC") | set(tiers))
        tier = next((t for t in letters if t not in tiers), "C")

    weak = [r["dimension"] for r in rows if r["evidence"] != "verified"]
    invented = [r["dimension"] for r in rows if r["evidence"] == "not in job ad"]
    weak_weight = sum(r["weight"] for r in rows if r["evidence"] != "verified")
    confidence = "low" if invented or weak_weight > 30 else ("medium" if weak else "high")
    if invented:
        problems.append("these quotes are not in the saved job ad; recheck them before showing the "
                        f"score: {invented}")
    if jd_norm is None:
        problems.append("no jd_file given, so evidence could not be checked; save the job ad to jds/")

    near = [f"{total} is within 3 points of the Tier {t} cut-off ({c})" for t, c in tiers.items() if abs(total - c) <= 3]
    return {"track": track["name"], "score": total, "tier": tier, "confidence": confidence,
            "dimensions": rows, "unverified": weak, "near_cutoff": near, "problems": problems}


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


MIGRATIONS = {0: migrate_0_to_1}


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
        tracks = parse_tracks((ws / "profile.md").read_text(encoding="utf-8"))
        out([find_track(tracks, rest[1])] if rest[:1] == ["--track"] and len(rest) > 1 else tracks)
    elif cmd == "score":
        out(score(ws, read_stdin_json()))
    elif cmd == "seen" and rest[:1] in (["check"], ["add"]):
        out(seen(ws, rest[0], [l for l in sys.stdin.read().splitlines() if l.strip()]))
    elif cmd == "tracker" and rest[:1] == ["list"]:
        out(tracker_list(ws, "--all" in rest))
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
