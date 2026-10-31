"""Job Buddy dashboard: one self-contained HTML page built from the tracker and the gap plan.

Called by `jb.py dashboard` (and after every tracker write). The page makes no network requests:
all data is embedded, so it works offline and nothing leaves the user's computer.
"""
import json

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job search dashboard</title>
<style>
:root {
  --bg: #f6f5f1; --panel: #ffffff; --ink: #1d1d1b; --muted: #6b6a65; --line: #e4e2db;
  --accent: #2f5d50; --a: #2f6f4f; --b: #9a6b12; --c: #8a8883; --warn: #a3412a;
  --a-bg: #e3f0e8; --b-bg: #f7ecd6; --c-bg: #efeeea; --warn-bg: #f8e4de;
}
@media (prefers-color-scheme: dark) {
  :root { --bg: #161615; --panel: #1f1f1d; --ink: #ecebe6; --muted: #a09e97; --line: #33322f;
    --accent: #8cc4b0; --a: #8fd0ad; --b: #e2b862; --c: #a9a7a1; --warn: #ec9a83;
    --a-bg: #1f3329; --b-bg: #3a2f17; --c-bg: #2a2a27; --warn-bg: #3d231c; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
main { max-width: 1180px; margin: 0 auto; padding: 28px 16px 64px; }
header { display: flex; flex-wrap: wrap; gap: 12px 24px; align-items: end; justify-content: space-between; margin-bottom: 22px; }
h1 { font-size: 26px; margin: 0; letter-spacing: -0.01em; }
h2 { font-size: 15px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin: 34px 0 12px; font-weight: 600; }
.sub { color: var(--muted); font-size: 13px; }
.controls { display: flex; gap: 8px; flex-wrap: wrap; }
select, input { font: inherit; padding: 7px 10px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); color: var(--ink); }
.tiles { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; }
@media (max-width: 900px) { .tiles { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 520px) { .tiles { grid-template-columns: repeat(2, 1fr); } h1 { font-size: 22px; } }
.tile { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
.tile .n { font-size: 30px; font-weight: 650; letter-spacing: -0.02em; }
.tile .l { color: var(--muted); font-size: 13px; }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 6px 16px; }
.action { display: flex; gap: 12px; align-items: baseline; padding: 11px 0; border-bottom: 1px solid var(--line); }
.action:last-child { border-bottom: 0; }
.action .what { flex: 1; }
.empty { color: var(--muted); padding: 12px 0; }
.board { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(185px, 1fr); gap: 12px; overflow-x: auto; padding-bottom: 6px; }
.col { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 10px; min-height: 120px; }
.col h3 { font-size: 13px; margin: 2px 4px 10px; display: flex; justify-content: space-between; color: var(--muted); font-weight: 600; }
.card { border: 1px solid var(--line); border-radius: 10px; padding: 9px 10px; margin-bottom: 8px; background: var(--bg); }
.card .co { font-weight: 600; }
.card .ro { font-size: 13px; }
.card .meta { display: flex; gap: 6px; align-items: center; margin-top: 6px; font-size: 12px; color: var(--muted); flex-wrap: wrap; }
.chip { display: inline-block; border-radius: 999px; padding: 1px 8px; font-size: 12px; font-weight: 600; }
.t-A { background: var(--a-bg); color: var(--a); } .t-B { background: var(--b-bg); color: var(--b); }
.t-C, .t- { background: var(--c-bg); color: var(--c); } .stale { background: var(--warn-bg); color: var(--warn); }
a { color: var(--accent); }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { text-align: left; padding: 9px 8px; border-bottom: 1px solid var(--line); }
th { color: var(--muted); font-weight: 600; font-size: 13px; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tr:last-child td { border-bottom: 0; }
.two { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.gap { padding: 12px 0; border-bottom: 1px solid var(--line); }
.gap:last-child { border-bottom: 0; }
.gap .head { display: flex; justify-content: space-between; gap: 12px; }
.gap ul { margin: 6px 0 0; padding-left: 18px; color: var(--muted); font-size: 13px; }
.note { color: var(--muted); font-size: 13px; margin-top: 8px; }
details summary { cursor: pointer; color: var(--muted); }
footer { margin-top: 40px; color: var(--muted); font-size: 12px; }
</style>
</head>
<body>
<main>
<header>
  <div>
    <h1>Your job search</h1>
    <div class="sub" id="updated"></div>
  </div>
  <div class="controls">
    <select id="track" aria-label="Track"></select>
    <input id="q" type="search" placeholder="Search company or role" aria-label="Search">
  </div>
</header>

<section class="tiles" id="tiles"></section>

<h2>Needs your attention</h2>
<section class="panel" id="actions"></section>

<h2>Pipeline</h2>
<section class="board" id="board"></section>

<div class="two">
  <section>
    <h2>Does your rubric work?</h2>
    <div class="panel"><table id="funnel"></table>
      <p class="note" id="funnel-note"></p></div>
  </section>
  <section>
    <h2>What's holding you back</h2>
    <div class="panel" id="gaps"></div>
  </section>
</div>

<h2>Closed</h2>
<section class="panel" id="closed"></section>

<footer>Built by Job Buddy from tracker.xlsx in this folder. Nothing on this page is sent anywhere.
Ask Claude to "refresh my dashboard" after editing the tracker by hand.</footer>
</main>

<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const OPEN = ['Found', 'Applied', 'Acknowledged', 'Assessment', 'Interview', 'Offer'];
const CLOSED = ['Rejected', 'Withdrawn', 'Ghosted'];
const today = new Date(D.generated + 'T12:00:00');
const el = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) k === 'class' ? e.className = v : e.setAttribute(k, v);
  for (const k of kids) if (k != null) e.append(k.nodeType ? k : String(k));
  return e;
};
const days = d => d ? Math.round((today - new Date(d + 'T12:00:00')) / 864e5) : null;
const applied = r => r.Status && r.Status !== 'Found';
const callback = r => ['Assessment', 'Interview', 'Offer'].includes(r.Status) ||
  (r.Status === 'Rejected' && ['Assessment', 'Interview', 'Final'].includes(r['Rejected At']));
const pct = (a, b) => b ? Math.round(100 * a / b) + '%' : '–';
const tierChip = t => el('span', { class: 'chip t-' + (t || '') }, t ? 'Tier ' + t : 'Unscored');
const safeUrl = u => /^https?:\/\//i.test(u || '') ? u : null;

document.getElementById('updated').textContent =
  `Updated ${today.toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })}`;
const tracks = [...new Set(D.rows.map(r => r.Track).filter(Boolean))];
const sel = document.getElementById('track');
sel.append(el('option', { value: '' }, 'All tracks'), ...tracks.map(t => el('option', { value: t }, t)));
if (tracks.length < 2) sel.hidden = true;

function rows() {
  const t = sel.value, q = document.getElementById('q').value.trim().toLowerCase();
  return D.rows.filter(r => (!t || r.Track === t) &&
    (!q || `${r.Company} ${r.Role}`.toLowerCase().includes(q)));
}

function render() {
  const R = rows();
  const ap = R.filter(applied), cb = R.filter(callback);
  const live = R.filter(r => ['Assessment', 'Interview'].includes(r.Status));
  const tiles = [
    [R.length, 'roles tracked'], [R.filter(r => r.Status === 'Found' && r.Tier === 'A').length, 'Tier A to apply for'],
    [ap.length, 'applied'], [pct(cb.length, ap.length), 'callback rate'],
    [live.length, 'in progress'], [R.filter(r => r.Status === 'Offer').length, 'offers']];
  document.getElementById('tiles').replaceChildren(...tiles.map(([n, l]) =>
    el('div', { class: 'tile' }, el('div', { class: 'n' }, n), el('div', { class: 'l' }, l))));

  // Needs attention: next actions on open roles, live stages, applications quiet for 14+ days
  const acts = [];
  for (const r of R) {
    if (!OPEN.includes(r.Status || 'Found')) continue;
    const quiet = ['Applied', 'Acknowledged'].includes(r.Status) && days(r['Last Update']) >= 14;
    if (r['Next Action'] && r['Next Action'] !== 'None') acts.push([0, r, r['Next Action']]);
    else if (['Assessment', 'Interview', 'Offer'].includes(r.Status)) acts.push([1, r, `${r.Status} stage: prepare`]);
    else if (quiet) acts.push([2, r, `No reply for ${days(r['Last Update'])} days: follow up or mark as ghosted`]);
    else if (r.Status === 'Found' && r.Tier === 'A' && r.Materials !== 'Yes') acts.push([3, r, 'Tier A: tailor your CV and apply']);
  }
  acts.sort((a, b) => a[0] - b[0]);
  const ab = document.getElementById('actions');
  ab.replaceChildren(...(acts.length ? acts.slice(0, 12).map(([p, r, what]) => el('div', { class: 'action' },
    tierChip(r.Tier), el('div', { class: 'what' }, el('strong', {}, r.Company), ' · ', r.Role,
      el('div', { class: 'sub' }, what)))) : [el('div', { class: 'empty' }, 'Nothing waiting on you.')]));

  // Pipeline board
  const board = document.getElementById('board');
  board.replaceChildren(...OPEN.map(s => {
    const items = R.filter(r => (r.Status || 'Found') === s)
      .sort((a, b) => (b['Fit Score'] || 0) - (a['Fit Score'] || 0));
    return el('div', { class: 'col' }, el('h3', {}, el('span', {}, s), el('span', {}, items.length)),
      ...items.map(r => {
        const quiet = ['Applied', 'Acknowledged'].includes(s) && days(r['Last Update']) >= 14;
        const url = safeUrl(r['Job URL']);
        return el('div', { class: 'card' },
          el('div', { class: 'co' }, r.Company), el('div', { class: 'ro' }, r.Role),
          el('div', { class: 'meta' }, tierChip(r.Tier), r['Fit Score'] != null ? r['Fit Score'] : null,
            quiet ? el('span', { class: 'chip stale' }, `quiet ${days(r['Last Update'])}d`) : null,
            url ? el('a', { href: url, target: '_blank', rel: 'noopener noreferrer' }, 'ad') : null));
      }),
      items.length ? null : el('div', { class: 'empty' }, '—'));
  }));

  // Funnel by tier
  const ft = document.getElementById('funnel');
  const line = t => { const x = R.filter(r => (r.Tier || '') === t), a = x.filter(applied), c = x.filter(callback);
    return [t || '–', x.length, a.length, c.length, pct(c.length, a.length), a.length && c.length / a.length]; };
  const fl = ['A', 'B', 'C'].map(line);
  ft.replaceChildren(el('tr', {}, ...['Tier', 'Found', 'Applied', 'Callbacks', 'Rate'].map((h, i) =>
    el('th', { class: i ? 'num' : '' }, h))), ...fl.map(f => el('tr', {}, el('td', {}, tierChip(f[0])),
      ...f.slice(1, 5).map(v => el('td', { class: 'num' }, v)))));
  const [A, B] = [fl[0], fl[1]];
  document.getElementById('funnel-note').textContent = A[2] + B[2] < 10
    ? 'Too few applications yet to judge the rubric. Tier A should end up converting better than Tier B.'
    : (A[5] >= B[5] ? 'Tier A is converting at least as well as Tier B: your rubric is doing its job.'
      : 'Tier B is converting better than Tier A. Ask Claude for a search review: the rubric may need a change.');

  // Gap plan (whole search, not filtered)
  const g = document.getElementById('gaps');
  const top = (D.gaps.skills || []).slice(0, 3);
  g.replaceChildren(...(top.length ? top.map(s => el('div', { class: 'gap' },
    el('div', { class: 'head' }, el('strong', {}, s.skill),
      el('span', { class: 'sub' }, `in ${s.roles_with_gap} role${s.roles_with_gap === 1 ? '' : 's'}`)),
    s.tier_upgrades.length ? el('div', { class: 'sub' }, `Closing it moves ${s.tier_upgrades.length} open role${s.tier_upgrades.length === 1 ? '' : 's'} up a tier:`) :
      el('div', { class: 'sub' }, `Worth about +${s.avg_points_if_closed} points per role; no tier changes yet.`),
    s.tier_upgrades.length ? el('ul', {}, ...s.tier_upgrades.slice(0, 4).map(u => el('li', {}, u.replace(' -> ', ' → ')))) : null))
    : [el('div', { class: 'empty' }, 'Score a few roles and your biggest gaps will show up here.')]),
    ...(D.gaps.notes || []).map(n => el('p', { class: 'note' }, n[0].toUpperCase() + n.slice(1) + '.')),
    el('p', { class: 'note' }, 'Ask Claude "what should I learn?" for a plan.'));

  // Closed
  const closed = R.filter(r => CLOSED.includes(r.Status));
  const stage = {};
  closed.filter(r => r.Status === 'Rejected').forEach(r => stage[r['Rejected At'] || 'Unknown'] = (stage[r['Rejected At'] || 'Unknown'] || 0) + 1);
  const cs = document.getElementById('closed');
  cs.replaceChildren(closed.length ? el('details', {}, el('summary', {},
    `${closed.length} closed · rejected at ` + (Object.entries(stage).map(([k, v]) => `${k} ${v}`).join(', ') || '–')),
    el('table', {}, el('tr', {}, ...['Company', 'Role', 'Status', 'Stage', 'Tier'].map(h => el('th', {}, h))),
      ...closed.map(r => el('tr', {}, el('td', {}, r.Company), el('td', {}, r.Role), el('td', {}, r.Status),
        el('td', {}, r['Rejected At'] || ''), el('td', {}, tierChip(r.Tier))))))
    : el('div', { class: 'empty' }, 'Nothing closed yet.'));
}
sel.onchange = render;
document.getElementById('q').oninput = render;
render();
</script>
</body>
</html>
"""


def render(rows, gaps, generated):
    """rows: tracker rows (dicts keyed by column name, dates as ISO strings); gaps: jb.gap_report()."""
    data = {"generated": generated, "rows": rows,
            "gaps": {"skills": gaps.get("skills", [])[:5], "notes": gaps.get("notes", [])}}
    # Embedded as JSON inside <script type="application/json">; escaping "<" stops any text in
    # the tracker (a job title, a note) from closing the tag and running as code.
    blob = json.dumps(data, ensure_ascii=False, default=str).replace("<", "\\u003c")
    return PAGE.replace("__DATA__", blob)

