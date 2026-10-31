"""Tests for feed/build_feed.py (no network). Run from the repo root: python3 -m unittest discover tests"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "feed"))
import build_feed as bf  # noqa: E402


class Relevant(unittest.TestCase):
    def test_ireland_locations_kept(self):
        for loc in ["Dublin, Ireland", "Cork", "Remote - Ireland", "Dublin, IE", "EMEA remote", "Europe",
                    "Amsterdam; Dublin", "Remote (Anywhere)"]:
            self.assertTrue(bf.relevant(loc), loc)

    def test_elsewhere_dropped(self):
        for loc in ["London, UK", "New York", "US - Remote", "Remote - US only", "Berlin, Germany", ""]:
            self.assertFalse(bf.relevant(loc), loc)

    def test_title_counts_only_for_irish_places(self):
        self.assertTrue(bf.relevant("Remote", "Account Executive, Ireland"))
        self.assertFalse(bf.relevant("London, UK", "Account Executive, EMEA"))


class Health(unittest.TestCase):
    def test_failures_and_drops_alert(self):
        prev = {"sources": {"A": {"listed": 10}, "B": {"listed": 5}, "C": {"listed": 0}}}
        now = {"A": {"ok": True, "listed": 0, "kept": 0},
               "B": {"ok": False, "error": "HTTPError 404", "listed": 0, "kept": 0},
               "C": {"ok": True, "listed": 0, "kept": 0}}
        alerts = bf.health(now, prev)
        self.assertEqual(len(alerts), 2)
        self.assertTrue(any(a.startswith("A: 0 listings") for a in alerts))
        self.assertTrue(any(a.startswith("B: failed") for a in alerts))

    def test_no_previous_feed(self):
        self.assertEqual(bf.health({"A": {"ok": True, "listed": 0, "kept": 0}}, None), [])


class Watchlist(unittest.TestCase):
    def test_watchlist_is_well_formed(self):
        data = json.loads((ROOT / "feed/watchlist-ie.json").read_text())
        names = [c["name"] for c in data["companies"]]
        self.assertEqual(len(names), len(set(names)), "duplicate company")
        for c in data["companies"]:
            self.assertIn(c["ats"], bf.ATS, c)
            self.assertTrue(c["id"], c)


if __name__ == "__main__":
    unittest.main()
