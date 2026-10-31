#!/usr/bin/env python3
"""Build the shared Job Buddy feed: one daily JSON of Ireland-relevant jobs from employers' public
job-board APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Workable), plus a health report.

  python3 feed/build_feed.py [--watchlist feed/watchlist-ie.json] [--previous old/ie.json] [--out out/]

Writes <out>/ie.json (the feed) and <out>/health.md (sources that failed or dropped to zero).
Exit code 0 always when the feed was written; the workflow reads health.json to decide on alerts.
Only official public job-board APIs are read: no scraping, no logins.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

UA = "JobBuddyFeed/1.0 (+https://github.com/adityab94/job-buddy)"
FEED_VERSION = 1
# A job is kept when its location text mentions one of these.
IRELAND = re.compile(r"\b(ireland|dublin|cork|galway|limerick|waterford|kilkenny|athlone|sligo|"
                     r"letterkenny|belfast|emea|europe|eu\b|anywhere|worldwide|global)", re.I)
IRISH_PLACE = re.compile(r"\b(ireland|irish|dublin|cork|galway|limerick|waterford|belfast)\b", re.I)
REMOTE_ONLY_ELSEWHERE = re.compile(r"\b(us only|usa only|united states only|canada only|uk only)\b", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ms(v):
    return dt.datetime.fromtimestamp(v / 1000, dt.timezone.utc).isoformat() if v else None


ATS = {
    "greenhouse": lambda s: [(p["title"], (p.get("location") or {}).get("name", ""), p.get("first_published") or p.get("updated_at"), p["absolute_url"])
                             for p in get(f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs")["jobs"]],
    "lever": lambda s: [(p["text"], " ".join(filter(None, [(p.get("categories") or {}).get("location"), p.get("workplaceType")])), ms(p.get("createdAt")), p["hostedUrl"])
                        for p in get(f"https://api.lever.co/v0/postings/{s}?mode=json")],
    "ashby": lambda s: [(p["title"], " ".join([p.get("location") or ""] + [x.get("location", "") for x in p.get("secondaryLocations") or []] + (["remote"] if p.get("isRemote") else [])), p.get("publishedAt"), p["jobUrl"])
                        for p in get(f"https://api.ashbyhq.com/posting-api/job-board/{s}")["jobs"]],
    "smartrecruiters": lambda s: [(p["name"], " ".join(filter(None, [(p.get("location") or {}).get("city"), (p.get("location") or {}).get("country"), "remote" if (p.get("location") or {}).get("remote") else ""])), p.get("releasedDate"), f"https://jobs.smartrecruiters.com/{s}/{p['id']}")
                                  for p in get(f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=100")["content"]],
    "workable": lambda s: [(p["title"], " ".join(filter(None, [p.get("city"), p.get("country"), "remote" if p.get("telecommuting") else ""])), p.get("published_on") or p.get("created_at"), p["url"])
                           for p in get(f"https://apply.workable.com/api/v1/widget/accounts/{s}")["jobs"]],
}


def relevant(loc, title=""):
    """Location mentions Ireland, an Irish city or a region that includes Ireland; a title only
    counts when it names an Irish place ("Account Manager, EMEA" in London is not a match)."""
    if IRISH_PLACE.search(title or ""):
        return True
    loc = loc or ""
    if re.search(r"\b(ie|irl)\b", loc) or IRELAND.search(loc):
        return not REMOTE_ONLY_ELSEWHERE.search(loc)
    return False


def fetch(company):
    name, ats, slug = company["name"], company["ats"], company["id"]
    try:
        rows = ATS[ats](slug)
    except Exception as e:  # noqa: BLE001 - every failure is reported in health
        return name, {"ok": False, "error": f"{type(e).__name__}: {e}"[:200], "listed": 0, "kept": 0}, []
    jobs = [{"c": name, "t": t.strip(), "l": re.sub(r"\s+", " ", l or "").strip()[:120], "posted": p,
             "u": u, "src": ats} for t, l, p, u in rows if relevant(l, t)]
    return name, {"ok": True, "listed": len(rows), "kept": len(jobs)}, jobs


def health(sources, previous):
    prev = (previous or {}).get("sources", {})
    alerts = []
    for name, s in sources.items():
        if not s["ok"]:
            alerts.append(f"{name}: failed ({s['error']})")
        elif s["listed"] == 0 and prev.get(name, {}).get("listed", 0) > 0:
            alerts.append(f"{name}: 0 listings today (had {prev[name]['listed']} last run): board ID changed or company moved ATS?")
    return alerts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--watchlist", default=str(Path(__file__).with_name("watchlist-ie.json")))
    ap.add_argument("--previous")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    watch = json.loads(Path(a.watchlist).read_text())["companies"]
    previous = json.loads(Path(a.previous).read_text()) if a.previous and Path(a.previous).is_file() else None
    sources, jobs = {}, []
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for name, s, j in pool.map(fetch, watch):
            sources[name] = s
            jobs.extend(j)
    jobs.sort(key=lambda j: (j["posted"] or ""), reverse=True)
    alerts = health(sources, previous)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    feed = {"version": FEED_VERSION, "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "region": "ie", "companies": len(watch), "jobs_count": len(jobs), "sources": sources, "jobs": jobs}
    (out / "ie.json").write_text(json.dumps(feed, ensure_ascii=False, separators=(",", ":")))
    (out / "health.json").write_text(json.dumps({"alerts": alerts, "generated": feed["generated"]}, indent=1))
    print(f"{len(jobs)} jobs from {sum(s['ok'] for s in sources.values())}/{len(watch)} boards; {len(alerts)} alert(s)")
    for x in alerts:
        print("ALERT", x)
    return 0


if __name__ == "__main__":
    sys.exit(main())
