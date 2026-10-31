"""Release consistency checks for Job Buddy. Run from the repo root: python3 .github/scripts/check_release.py"""
import json, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "plugins/job-buddy/skills/job-buddy"
errors = []

plugin = json.loads((ROOT / "plugins/job-buddy/.claude-plugin/plugin.json").read_text())
market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
entry = next((p for p in market["plugins"] if p["name"] == plugin["name"]), None)
version = plugin["version"]

if entry is None:
    errors.append("marketplace.json has no entry for " + plugin["name"])
elif entry.get("version") != version:
    errors.append(f"marketplace.json version {entry.get('version')} != plugin.json {version}")

m = re.search(r"^Version: (\S+)", (SKILL_DIR / "SKILL.md").read_text(), re.M)
if not m or m.group(1) != version:
    errors.append(f"SKILL.md 'Version:' line is {m and m.group(1)}, expected {version}")

m = re.search(r"^## (\S+)", (ROOT / "CHANGELOG.md").read_text(), re.M)
if not m or m.group(1) != version:
    errors.append(f"CHANGELOG.md top entry is {m and m.group(1)}, expected {version}")

# The zip must hold exactly the skill folder (as job-buddy/...), byte for byte.
local = {"job-buddy/" + p.relative_to(SKILL_DIR).as_posix(): p.read_bytes()
         for p in SKILL_DIR.rglob("*") if p.is_file() and p.name != ".DS_Store" and "__pycache__" not in p.parts}
with zipfile.ZipFile(ROOT / "job-buddy-skill.zip") as z:
    zipped = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
for n in sorted(local.keys() - zipped.keys()):
    errors.append("missing from zip: " + n)
for n in sorted(zipped.keys() - local.keys()):
    errors.append("in zip but not in skill folder: " + n)
for n in sorted(local.keys() & zipped.keys()):
    if local[n] != zipped[n]:
        errors.append("zip is stale for: " + n)

if errors:
    print("Release check failed:\n- " + "\n- ".join(errors))
    print("\nRebuild the zip: cd plugins/job-buddy/skills && zip -r ../../../job-buddy-skill.zip job-buddy")
    sys.exit(1)
print(f"Release check passed for {version}.")
