"""Job Buddy dashboard: one self-contained HTML page built from the tracker and the gap plan.

Called by `jb.py dashboard` (and after every tracker write). The page makes no network requests:
all data, the logo and the icons are embedded, so it works offline and nothing leaves the user's
computer. Look: soft UI and frosted glass over a cream-to-sage gradient, from The Buddy Social's
palette; light by default with a theme toggle.
"""
import json

from logo import LOGO_MASK_PNG_B64

HEAD = r"""<title>Job Search Dashboard</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
@property --wash-1 { syntax: '<color>'; inherits: true; initial-value: transparent; }
@property --wash-2 { syntax: '<color>'; inherits: true; initial-value: transparent; }
@property --wash-3 { syntax: '<color>'; inherits: true; initial-value: transparent; }
@property --wash-4 { syntax: '<color>'; inherits: true; initial-value: transparent; }
@property --ground { syntax: '<color>'; inherits: true; initial-value: transparent; }
@property --orb { syntax: '<color>'; inherits: true; initial-value: transparent; }
:root {
  --logo: url("data:image/png;base64,__LOGO__");
  --radius: 22px; --radius-sm: 14px;
  --ease: cubic-bezier(.16, 1, .3, 1);
  font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI Variable", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
:root {
  --ground: #f7efda;
  --wash-1: #fff0c4; --wash-2: #b3d18c; --wash-3: #efc47a; --wash-4: #cfe4bb; --orb: rgba(110, 150, 70, .5);
  --ink: #1f2e17; --ink-2: #4f5d43; --ink-3: #5a654e;
  --brand: #4c7031; --brand-ink: #3b5a25; --brand-soft: rgba(76, 112, 49, .12);
  --glass: rgba(255, 252, 243, .46); --glass-strong: rgba(255, 253, 247, .9);
  --glass-edge: rgba(255, 255, 255, .85); --glass-line: rgba(76, 112, 49, .14);
  --shadow: 0 1px 0 rgba(255,255,255,.9) inset, 0 18px 40px -22px rgba(52, 77, 32, .38), 0 3px 10px -4px rgba(52, 77, 32, .14);
  --shadow-lift: 0 1px 0 rgba(255,255,255,.95) inset, 0 26px 50px -24px rgba(52, 77, 32, .45), 0 6px 14px -6px rgba(52, 77, 32, .18);
  --a: #2f6a2a; --a-bg: rgba(76, 140, 60, .16);
  --b: #7a4f00; --b-bg: rgba(214, 150, 40, .2);
  --c: #5f665a; --c-bg: rgba(95, 102, 90, .12);
  --wait: #86500a; --wait-bg: rgba(224, 160, 50, .2);
  --bar: rgba(76, 112, 49, .16);
  --sheen: rgba(255, 255, 255, .85);
  --rim-1: rgba(255, 255, 255, .95); --rim-2: rgba(255, 255, 255, .15); --rim-3: rgba(76, 112, 49, .14);
  --next-ring: rgba(76, 112, 49, .12); --next-sheen: rgba(255, 255, 255, .9);
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
  --ground: #0e170d;
  --wash-1: #24401c; --wash-2: #13260f; --wash-3: #3a3014; --wash-4: #1a3a28; --orb: rgba(150, 200, 100, .14);
  --ink: #f4ead2; --ink-2: #c9c1a8; --ink-3: #a29c86;
  --brand: #a9cd86; --brand-ink: #c3df9f; --brand-soft: rgba(169, 205, 134, .14);
  --glass: rgba(30, 44, 26, .45); --glass-strong: rgba(52, 76, 44, .82);
  --glass-edge: rgba(255, 246, 220, .1); --glass-line: rgba(255, 246, 220, .09);
  --shadow: 0 1px 0 rgba(255,246,220,.07) inset, 0 20px 44px -22px rgba(0,0,0,.7), 0 3px 10px -4px rgba(0,0,0,.4);
  --shadow-lift: 0 1px 0 rgba(255,246,220,.1) inset, 0 28px 54px -24px rgba(0,0,0,.8), 0 6px 14px -6px rgba(0,0,0,.5);
  --a: #b4dc93; --a-bg: rgba(140, 200, 100, .16);
  --b: #f0c374; --b-bg: rgba(240, 180, 80, .16);
  --c: #bdb6a0; --c-bg: rgba(200, 190, 160, .12);
  --wait: #f2b85e; --wait-bg: rgba(240, 170, 70, .16);
  --bar: rgba(169, 205, 134, .16);
  --sheen: rgba(255, 246, 220, .1);
  --rim-1: rgba(255, 246, 220, .3); --rim-2: rgba(255, 246, 220, .04); --rim-3: rgba(169, 205, 134, .14);
  --next-ring: rgba(169, 205, 134, .28); --next-sheen: rgba(255, 246, 220, .16);
  color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --ground: #0e170d;
  --wash-1: #24401c; --wash-2: #13260f; --wash-3: #3a3014; --wash-4: #1a3a28; --orb: rgba(150, 200, 100, .14);
  --ink: #f4ead2; --ink-2: #c9c1a8; --ink-3: #a29c86;
  --brand: #a9cd86; --brand-ink: #c3df9f; --brand-soft: rgba(169, 205, 134, .14);
  --glass: rgba(30, 44, 26, .45); --glass-strong: rgba(52, 76, 44, .82);
  --glass-edge: rgba(255, 246, 220, .1); --glass-line: rgba(255, 246, 220, .09);
  --shadow: 0 1px 0 rgba(255,246,220,.07) inset, 0 20px 44px -22px rgba(0,0,0,.7), 0 3px 10px -4px rgba(0,0,0,.4);
  --shadow-lift: 0 1px 0 rgba(255,246,220,.1) inset, 0 28px 54px -24px rgba(0,0,0,.8), 0 6px 14px -6px rgba(0,0,0,.5);
  --a: #b4dc93; --a-bg: rgba(140, 200, 100, .16);
  --b: #f0c374; --b-bg: rgba(240, 180, 80, .16);
  --c: #bdb6a0; --c-bg: rgba(200, 190, 160, .12);
  --wait: #f2b85e; --wait-bg: rgba(240, 170, 70, .16);
  --bar: rgba(169, 205, 134, .16);
  --sheen: rgba(255, 246, 220, .1);
  --rim-1: rgba(255, 246, 220, .3); --rim-2: rgba(255, 246, 220, .04); --rim-3: rgba(169, 205, 134, .14);
  --next-ring: rgba(169, 205, 134, .28); --next-sheen: rgba(255, 246, 220, .16);
  color-scheme: dark;
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
html { background: var(--ground); color: var(--ink); -webkit-text-size-adjust: 100%; scrollbar-color: var(--bar) transparent;
  transition: color .5s var(--ease); }
body { margin: 0; min-height: 100vh; background: var(--ground); color: var(--ink); font-size: 15px; line-height: 1.5; font-variant-numeric: tabular-nums; }
.sky { position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background:
    radial-gradient(60vw 55vh at 8% 0%, var(--wash-1), transparent 70%),
    radial-gradient(55vw 60vh at 100% 18%, var(--wash-2), transparent 70%),
    radial-gradient(60vw 50vh at 85% 100%, var(--wash-3), transparent 70%),
    radial-gradient(50vw 45vh at 0% 95%, var(--wash-4), transparent 70%),
    var(--ground);
  transition: --wash-1 .7s var(--ease), --wash-2 .7s var(--ease), --wash-3 .7s var(--ease), --wash-4 .7s var(--ease),
    --ground .7s var(--ease), --orb .7s var(--ease); }
.sky::before, .sky::after { content: ""; position: absolute; border-radius: 50%; filter: blur(60px); background: var(--orb); }
.sky::before { width: 36vw; height: 30vw; left: 30%; top: 4%; }
.sky::after { width: 30vw; height: 26vw; left: 2%; top: 58%; background: var(--wash-3); opacity: .7; }
::selection { background: var(--brand); color: var(--ground); }
:focus-visible { outline: 2px solid var(--brand); outline-offset: 3px; border-radius: 10px; }
a { color: var(--brand-ink); text-underline-offset: 3px; }
main { max-width: 1240px; margin: 0 auto; padding-block: 28px 40px;
  padding-left: max(24px, env(safe-area-inset-left, 0px)); padding-right: max(24px, env(safe-area-inset-right, 0px)); }

.glass { position: relative; isolation: isolate; background: var(--glass); border: 1px solid var(--glass-edge); border-radius: var(--radius);
  box-shadow: var(--shadow); -webkit-backdrop-filter: blur(24px) saturate(160%); backdrop-filter: blur(24px) saturate(160%); }
.glass::before { content: ""; position: absolute; inset: 0; border-radius: inherit; pointer-events: none; z-index: -1;
  background: linear-gradient(170deg, var(--sheen) 0%, transparent 42%); }
.glass::after { content: ""; position: absolute; inset: -1px; border-radius: inherit; padding: 1px; pointer-events: none;
  background: linear-gradient(170deg, var(--rim-1), var(--rim-2) 40%, var(--rim-3));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0); }
.glass, .icon-btn { transition: background-color .5s var(--ease), border-color .5s var(--ease), color .5s var(--ease),
  transform .22s var(--ease), box-shadow .22s var(--ease); }
@supports not ((backdrop-filter: blur(2px)) or (-webkit-backdrop-filter: blur(2px))) {
  .glass { background: var(--glass-strong); }
}

/* Header */
header { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 18px 28px; align-items: center; margin-bottom: 26px; }
.mark { width: 112px; aspect-ratio: 336 / 200; background: var(--brand-ink);
  -webkit-mask: var(--logo) center / contain no-repeat; mask: var(--logo) center / contain no-repeat; }
.title { border-left: 1px solid var(--glass-line); padding-left: 26px; min-width: 0; }
h1 { margin: 0; font-size: 28px; line-height: 1.15; font-weight: 680; letter-spacing: -0.02em; }
.draft { margin: 10px 0 0; padding: 6px 12px; border-radius: 12px; background: var(--wait-bg); color: var(--ink); font-size: 13.5px; max-width: 70ch; width: fit-content; }
.status { margin: 6px 0 0; color: var(--ink-2); max-width: 70ch; text-wrap: pretty; }
.tools { display: flex; gap: 10px; align-items: center; }
.field { display: flex; align-items: center; gap: 8px; height: 42px; padding: 0 14px; border-radius: 999px; }
.field svg { flex: none; color: var(--ink-3); }
.field input, .field select { border: 0; background: transparent; color: var(--ink); font: inherit; outline: none; min-width: 0; }
.field input { width: 190px; caret-color: var(--brand); }
.field input::placeholder { color: var(--ink-3); }
.field:focus-within { outline: 2px solid var(--brand); outline-offset: 2px; }
.icon-btn { width: 42px; height: 42px; border-radius: 999px; display: grid; place-items: center; cursor: pointer;
  color: var(--ink); border: 1px solid var(--glass-edge); }
.icon-btn:hover { transform: translateY(-1px); box-shadow: var(--shadow-lift); }
.icon-btn:active { transform: translateY(0); box-shadow: inset 0 2px 6px rgba(40, 60, 25, .18); }
.icon-btn .moon, [data-theme="dark"] .icon-btn .sun { display: none; }
[data-theme="dark"] .icon-btn .moon { display: block; }

/* Lead row */
.lead { display: grid; grid-template-columns: minmax(0, 1.75fr) minmax(280px, 1fr); gap: 20px; align-items: start; }
.pane { padding: 22px 24px; }
.pane-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 6px; }
h2 { margin: 0; font-size: 17px; font-weight: 650; letter-spacing: -0.01em; }
.pane-head .hint { color: var(--ink-3); font-size: 13px; }
.next { background: var(--glass-strong); box-shadow: var(--shadow), 0 0 0 1px var(--next-ring); }
.next::before { background: linear-gradient(170deg, var(--next-sheen) 0%, transparent 55%); }
.todo { list-style: none; margin: 0; padding: 0; }
.todo li { display: grid; grid-template-columns: auto 1fr auto; gap: 14px; align-items: center; padding: 14px 0; border-top: 1px solid var(--glass-line); }
.todo li:first-child { border-top: 0; }
.todo .who { font-weight: 620; }
.todo .role { color: var(--ink-2); }
.todo .what { color: var(--ink-2); font-size: 14px; margin-top: 2px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: var(--brand); box-shadow: 0 0 0 5px var(--brand-soft); }
.dot.wait { background: var(--wait); box-shadow: 0 0 0 5px var(--wait-bg); }
.dot.live { background: var(--a); box-shadow: 0 0 0 5px var(--a-bg); }
.calm { padding: 18px 0 8px; color: var(--ink-2); margin: 0; }

.counts { display: grid; grid-template-columns: 1fr 1fr; }
.count { padding: 16px 4px 14px; border-top: 1px solid var(--glass-line); }
.count:nth-child(-n+2) { border-top: 0; padding-top: 6px; }
.count:nth-child(odd) { padding-right: 16px; border-right: 1px solid var(--glass-line); }
.count:nth-child(even) { padding-left: 18px; }
.count .n { font-size: 30px; font-weight: 680; letter-spacing: -0.03em; line-height: 1.1; }
.count .l { color: var(--ink-2); font-size: 13.5px; }
@media (min-width: 981px) {
  .lead { align-items: stretch; }
  .lead > .pane:last-child { display: flex; flex-direction: column; }
  .counts { flex: 1; grid-auto-rows: 1fr; margin-top: 8px; }
  .count, .count:nth-child(-n+2) { padding-top: 14px; }
}

/* Pipeline */
.section-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin: 40px 2px 14px; }
.section-head .hint { color: var(--ink-3); font-size: 13px; }
.lanes { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(168px, 1fr); gap: 14px; overflow-x: auto;
  padding: 4px 4px 14px; margin: 0 -4px; scroll-snap-type: x proximity; scrollbar-width: thin; scrollbar-color: var(--bar) transparent; }
.lanes::-webkit-scrollbar { height: 8px; } .lanes::-webkit-scrollbar-thumb { background: var(--bar); border-radius: 8px; }
.lane { scroll-snap-align: start; min-width: 0; }
.lane-head { display: flex; justify-content: space-between; align-items: center; padding: 0 6px 10px; color: var(--ink-2); font-size: 13.5px; font-weight: 600; }
.lane-head .num { min-width: 26px; height: 22px; padding: 0 8px; border-radius: 999px; display: inline-grid; place-items: center;
  background: var(--brand-soft); color: var(--brand-ink); font-size: 12px; }
.job { padding: 13px 14px; border-radius: var(--radius-sm); margin-bottom: 10px; }
.job:hover { transform: translateY(-2px); box-shadow: var(--shadow-lift); }
.job .co { font-weight: 640; }
.job .ro { color: var(--ink-2); font-size: 13.5px; line-height: 1.35; margin-top: 1px; }
.job .meta { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-top: 10px; font-size: 12.5px; color: var(--ink-3); }
.job .meta a { margin-left: auto; display: inline-flex; align-items: center; gap: 4px; font-size: 12.5px; }
.lane-empty { padding: 14px; border-radius: var(--radius-sm); border: 1.5px dashed var(--glass-line); color: var(--ink-3); font-size: 13px; text-align: center; }

.chip { display: inline-flex; align-items: center; height: 22px; padding: 0 9px; border-radius: 999px; font-size: 12px; font-weight: 650; white-space: nowrap; }
.t-A { background: var(--a-bg); color: var(--a); } .t-B { background: var(--b-bg); color: var(--b); }
.t-C, .t-x { background: var(--c-bg); color: var(--c); }
.quiet { background: var(--wait-bg); color: var(--wait); }

/* Insight row */
.insight { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 40px; align-items: start; }
.tier-row { display: grid; grid-template-columns: 64px 1fr auto; gap: 14px; align-items: center; padding: 14px 0; border-top: 1px solid var(--glass-line); }
.pane-head + .tier-row { border-top: 0; }
.tier-row .detail { font-size: 13.5px; color: var(--ink-2); }
.track { height: 8px; border-radius: 99px; background: var(--bar); margin-top: 7px; overflow: hidden; }
.track i { display: block; height: 100%; border-radius: inherit; background: var(--brand); transition: width .6s var(--ease); }
.rate { font-size: 20px; font-weight: 680; letter-spacing: -0.02em; min-width: 54px; text-align: right; }
.verdict { margin: 12px 0 0; padding: 12px 14px; border-radius: var(--radius-sm); background: var(--brand-soft); color: var(--ink); font-size: 14px; }
.verdict.warn { background: var(--wait-bg); }
.gap { padding: 14px 0; border-top: 1px solid var(--glass-line); }
.pane-head + .gap { border-top: 0; }
.gap .skill { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.gap .skill b { font-size: 18px; font-weight: 680; letter-spacing: -0.01em; }
.gap .skill span { color: var(--ink-3); font-size: 13px; }
.gap .why { color: var(--ink-2); font-size: 14px; margin: 3px 0 8px; }
.lift { display: grid; grid-template-columns: 1fr auto; gap: 10px; align-items: center; padding: 6px 0; font-size: 14px; }
.lift .jump { display: inline-flex; gap: 6px; align-items: center; color: var(--ink-3); font-size: 13px; }
.aside { color: var(--ink-3); font-size: 13px; margin: 10px 0 0; }

/* Closed */
.closed { margin-top: 40px; padding: 4px 24px; }
.closed summary { cursor: pointer; padding: 14px 0; list-style: none; display: flex; justify-content: space-between; align-items: center; gap: 12px; color: var(--ink-2); }
.closed summary::-webkit-details-marker { display: none; }
.closed summary b { color: var(--ink); font-weight: 650; }
.closed summary svg { transition: transform .25s var(--ease); flex: none; }
.closed[open] summary svg { transform: rotate(180deg); }
table { width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 12px; }
th, td { text-align: left; padding: 10px 8px; border-top: 1px solid var(--glass-line); }
th { color: var(--ink-3); font-weight: 600; font-size: 12.5px; }

footer { margin-top: 48px; display: flex; flex-wrap: wrap; gap: 14px 24px; align-items: center; justify-content: space-between;
  padding-top: 22px; border-top: 1px solid var(--glass-line); color: var(--ink-3); font-size: 13px; }
.sign { display: flex; align-items: center; gap: 14px; color: var(--ink-2); }
.sign .mark { width: 54px; }
.sign b { color: var(--ink); font-weight: 650; }

.empty-state { padding: 36px 28px; text-align: center; }
.empty-state h2 { font-size: 20px; margin-bottom: 6px; }
.empty-state p { color: var(--ink-2); margin: 0 auto; max-width: 52ch; }

@media (max-width: 980px) {
  .lead, .insight { grid-template-columns: 1fr; }
  header { grid-template-columns: auto 1fr; }
  .tools { grid-column: 1 / -1; }
  .field.search { flex: 1; } .field input { width: 100%; }
}
@media (max-width: 560px) {
  main { padding-block: 18px 32px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
  header { grid-template-columns: 1fr; gap: 14px; }
  .title { border-left: 0; padding-left: 0; }
  .mark { width: 92px; }
  h1 { font-size: 24px; }
  .pane { padding: 18px; }
  .lanes { grid-auto-columns: 78%; }
  .count .n { font-size: 26px; }
  .pane-head { flex-wrap: wrap; row-gap: 2px; }
  .pane-head .hint { flex-basis: 100%; }
  .todo li { grid-template-columns: auto 1fr; }
  .todo li > .chip { grid-column: 2; justify-self: start; margin-top: -4px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { transition: none !important; }
}
</style>
"""

BODY = r"""<div class="sky" aria-hidden="true"></div>
<main>
<header>
  <div class="mark" role="img" aria-label="The Buddy Social"></div>
  <div class="title">
    <h1 id="hello">Your job search</h1>
    <p class="status" id="status"></p>
    <p class="draft" id="draft" hidden>Your scoring is a first draft. Rate a few roles great, okay or no and Claude will tune it to you.</p>
  </div>
  <div class="tools">
    <label class="field glass search">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="Search company or role" aria-label="Search company or role">
    </label>
    <label class="field glass" id="track-field" hidden>
      <select id="track" aria-label="Track"></select>
    </label>
    <button class="icon-btn glass" id="theme" type="button" aria-label="Switch to dark mode">
      <svg class="sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/></svg>
      <svg class="moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/></svg>
    </button>
  </div>
</header>

<div id="app"></div>

<footer>
  <div class="sign">
    <div class="mark" role="img" aria-label="The Buddy Social"></div>
    <span>Created by <b>Aditya Bhatnagar</b> · The Buddy Social</span>
  </div>
  <span id="where">Made by Job Buddy from tracker.xlsx in this folder. Nothing here is sent anywhere.</span>
</footer>
</main>

<script id="data" type="application/json">__DATA__</script>
<script>
let D = JSON.parse(document.getElementById('data').textContent);
const STAGES = ['Found', 'Applied', 'Acknowledged', 'Assessment', 'Interview', 'Offer'];
const CLOSED = ['Rejected', 'Withdrawn', 'Ghosted', 'Expired'];
let today = new Date((D.generated || new Date().toISOString().slice(0, 10)) + 'T12:00:00');
const h = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') e.className = v; else if (k === 'style') e.style.cssText = v; else e.setAttribute(k, v);
  }
  for (const k of kids.flat()) if (k != null && k !== false) e.append(k.nodeType ? k : String(k));
  return e;
};
const svg = (paths, size = 14) => { const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  for (const [k, v] of Object.entries({ width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor',
    'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', 'aria-hidden': 'true' })) s.setAttribute(k, v);
  s.innerHTML = paths; return s; };
const ICON_OUT = '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M19 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h5"/>';
const ICON_ARROW = '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>';
const ICON_CHEVRON = '<path d="m6 9 6 6 6-6"/>';
const days = d => d ? Math.round((today - new Date(d + 'T12:00:00')) / 864e5) : null;
const status = r => r.Status || 'Found';
const applied = r => !['Found', 'Expired'].includes(status(r));
const callback = r => ['Assessment', 'Interview', 'Offer'].includes(r.Status) ||
  (r.Status === 'Rejected' && ['Assessment', 'Interview', 'Final'].includes(r['Rejected At']));
const quietFor = r => ['Applied', 'Acknowledged'].includes(r.Status) && days(r['Last Update']) >= 14 ? days(r['Last Update']) : 0;
const pct = (a, b) => b ? Math.round(100 * a / b) + '%' : '–';
const tier = t => h('span', { class: 'chip t-' + (t || 'x') }, t ? 'Tier ' + t : 'Not scored');
const safeUrl = u => /^https?:\/\//i.test(u || '') ? u : null;
const plural = (n, one, many = one + 's') => `${n} ${n === 1 ? one : many}`;
const dateLong = d => d.toLocaleDateString(undefined, { day: 'numeric', month: 'long' });

// Theme: light unless the user switched it; remembered in this browser only.
const root = document.documentElement, themeBtn = document.getElementById('theme');
const setTheme = t => { root.dataset.theme = t;
  themeBtn.setAttribute('aria-label', t === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'); };
let savedTheme = null;
try { savedTheme = localStorage.getItem('jb-theme'); } catch (e) {}
setTheme(savedTheme === 'dark' ? 'dark' : 'light');
themeBtn.onclick = () => { const t = root.dataset.theme === 'dark' ? 'light' : 'dark'; setTheme(t);
  try { localStorage.setItem('jb-theme', t); } catch (e) {} };

const sel = document.getElementById('track');
const q = document.getElementById('q');
function setTracks() {
  const tracks = [...new Set(D.rows.map(r => r.Track).filter(Boolean))], keep = sel.value;
  sel.replaceChildren(h('option', { value: '' }, 'All tracks'), ...tracks.map(t => h('option', { value: t }, t)));
  sel.value = tracks.includes(keep) ? keep : '';
  document.getElementById('track-field').hidden = tracks.length < 2;
}

function visible() {
  const t = sel.value, s = q.value.trim().toLowerCase();
  return D.rows.filter(r => (!t || r.Track === t) && (!s || `${r.Company} ${r.Role}`.toLowerCase().includes(s)));
}

// Personal touches, all from the user's own profile and tracker: first name, the time of day on
// their own clock, how long the search has run, and the one thing that matters most right now.
function greet() {
  const name = (D.person || {}).name, hr = new Date().getHours();
  const part = hr >= 5 && hr < 12 ? 'Good morning' : hr >= 12 && hr < 17 ? 'Good afternoon' : hr >= 17 && hr < 22 ? 'Good evening' : 'Hello';
  document.getElementById('hello').textContent = name ? `${part}, ${name}` : 'Your job search';
  document.getElementById('draft').hidden = !(D.person || {}).draft || !D.rows.length;
}
function searchWeek(R) {
  const tracks = ((D.person || {}).tracks || []).filter(Boolean);
  const found = R.map(r => r['Date Found']).filter(Boolean).sort()[0];
  if (!found) return '';
  const week = Math.max(1, Math.ceil((days(found) + 1) / 7));
  const what = tracks.length === 1 ? `${tracks[0]} search` : 'search';
  return `Week ${week} of your ${what}.`;
}
function headline(R, ap, live, offers, T) {
  const best = list => list.slice().sort((a, b) => (b['Fit Score'] || 0) - (a['Fit Score'] || 0))[0];
  if (offers.length) return offers.length === 1 ? `You have an offer from ${offers[0].Company}.` : `You have ${offers.length} offers to weigh up.`;
  const iv = R.filter(r => r.Status === 'Interview');
  if (iv.length) return iv.length === 1 ? `${iv[0].Company} is at interview stage.` : `${iv.length} interviews in progress, led by ${best(iv).Company}.`;
  if (live.length) return `${plural(live.length, 'application')} moving forward, ${plural(ap.length, 'sent')} in total.`;
  const waiting = R.filter(r => (r.Status || 'Found') === 'Found' && r.Tier === 'A');
  if (waiting.length) return `${plural(waiting.length, 'strong match', 'strong matches')} waiting for you, starting with ${best(waiting).Company}.`;
  if (ap.length) return `${plural(ap.length, 'application')} out. ${T.length ? plural(T.length, 'thing needs', 'things need') + ' you.' : 'Nothing is waiting on you.'}`;
  return 'No strong matches yet. Ask Claude to “find me roles”.';
}

function todos(R) {
  const out = [];
  for (const r of R) {
    if (CLOSED.includes(r.Status)) continue;
    const na = r['Next Action'] && r['Next Action'] !== 'None' ? r['Next Action'] : '';
    if (['Assessment', 'Interview', 'Offer'].includes(r.Status)) out.push([0, 'live', r, na || `${r.Status} stage: get ready`]);
    else if (na) out.push([1, '', r, na]);
    else if (quietFor(r)) out.push([2, 'wait', r, `No reply for ${quietFor(r)} days. Follow up, or mark it as ghosted.`]);
    else if (status(r) === 'Found' && r.Tier === 'A' && r.Materials !== 'Yes') out.push([3, '', r, 'Strong match. Tailor your CV and apply.']);
  }
  return out.sort((a, b) => a[0] - b[0]);
}

function render() {
  const R = visible(), app = document.getElementById('app');
  const ap = R.filter(applied), cb = R.filter(callback);
  const live = R.filter(r => ['Assessment', 'Interview'].includes(r.Status));
  const offers = R.filter(r => r.Status === 'Offer');
  const T = todos(R);

  greet();
  document.getElementById('status').textContent = !D.rows.length
    ? `Nothing tracked yet. Updated ${dateLong(today)}.`
    : [searchWeek(R), headline(R, ap, live, offers, T), `Updated ${dateLong(today)}.`].filter(Boolean).join(' ');

  if (!D.rows.length) {
    const [title, text] = {
      loading: ['Loading your job search…', 'One moment while your latest tracker data arrives.'],
      offline: ['Open this from your Claude sidebar', 'Your dashboard data lives in your Claude account. Open the page from Claude, signed in, to see it.'],
    }[D.state] || ['Your dashboard fills in as you go',
      'Ask Claude to “find me roles” or paste a job link. Every role Job Buddy scores lands here, with what to do next.'];
    app.replaceChildren(h('section', { class: 'glass empty-state' }, h('h2', {}, title), h('p', {}, text)));
    if (D.state) document.getElementById('status').textContent = '';
    return;
  }

  // Lead row: next up + counts
  const next = h('section', { class: 'glass pane next', 'aria-labelledby': 'next-h' },
    h('div', { class: 'pane-head' }, h('h2', { id: 'next-h' }, 'Next up'),
      T.length > 8 ? h('span', { class: 'hint' }, `showing 8 of ${T.length}`) : null),
    T.length ? h('ul', { class: 'todo' }, T.slice(0, 8).map(([, kind, r, what]) =>
      h('li', {}, h('span', { class: 'dot ' + kind }),
        h('div', {}, h('div', {}, h('span', { class: 'who' }, r.Company), h('span', { class: 'role' }, ' · ' + r.Role)),
          h('div', { class: 'what' }, what)),
        tier(r.Tier))))
      : h('p', { class: 'calm' }, 'Nothing is waiting on you right now. Ask Claude to “find me roles” for fresh matches.'));
  const counts = h('section', { class: 'glass pane', 'aria-labelledby': 'counts-h' },
    h('div', { class: 'pane-head' }, h('h2', { id: 'counts-h' }, 'At a glance')),
    h('div', { class: 'counts' }, [
      [R.length, 'roles tracked'], [ap.length, 'applications sent'],
      [pct(cb.length, ap.length), 'heard back with a next step'], [offers.length, offers.length === 1 ? 'offer' : 'offers']]
      .map(([n, l]) => h('div', { class: 'count' }, h('div', { class: 'n' }, n), h('div', { class: 'l' }, l)))));

  // Pipeline
  const lanes = h('div', { class: 'lanes' }, STAGES.map(s => {
    const items = R.filter(r => status(r) === s).sort((a, b) => (b['Fit Score'] || 0) - (a['Fit Score'] || 0));
    return h('section', { class: 'lane', 'aria-label': `${s}: ${items.length}` },
      h('div', { class: 'lane-head' }, h('span', {}, s), h('span', { class: 'num' }, items.length)),
      items.length ? items.map(r => {
        const url = safeUrl(r['Job URL']), qd = quietFor(r);
        return h('article', { class: 'glass job' },
          h('div', { class: 'co' }, r.Company), h('div', { class: 'ro' }, r.Role),
          h('div', { class: 'meta' }, tier(r.Tier), r['Fit Score'] != null ? h('span', {}, r['Fit Score']) : null,
            qd ? h('span', { class: 'chip quiet' }, `quiet ${qd}d`) : null,
            url ? h('a', { href: url, target: '_blank', rel: 'noopener noreferrer', 'aria-label': `Open the ${r.Company} job ad` }, 'View ad', svg(ICON_OUT, 12)) : null));
      }) : h('div', { class: 'lane-empty' }, 'None yet'));
  }));

  // Rubric check
  const rows = ['A', 'B', 'C'].map(t => { const x = R.filter(r => r.Tier === t), a = x.filter(applied), c = x.filter(callback);
    return { t, found: x.length, applied: a.length, cb: c.length, rate: a.length ? c.length / a.length : null }; });
  const [A, B] = rows;
  const judged = A.applied + B.applied >= 10;
  const working = !judged || (A.rate ?? 0) >= (B.rate ?? 0);
  const rubric = h('section', { class: 'glass pane', 'aria-labelledby': 'rubric-h' },
    h('div', { class: 'pane-head' }, h('h2', { id: 'rubric-h' }, 'Is your scoring working?'),
      h('span', { class: 'hint' }, 'callbacks per application')),
    rows.map(x => h('div', { class: 'tier-row' }, tier(x.t),
      h('div', {}, h('div', { class: 'detail' }, `${plural(x.applied, 'application')} · ${plural(x.cb, 'callback')} · ${x.found} found`),
        h('div', { class: 'track' }, h('i', { style: `width:${x.rate == null ? 0 : Math.round(x.rate * 100)}%` }))),
      h('span', { class: 'rate' }, x.rate == null ? '–' : Math.round(x.rate * 100) + '%'))),
    h('p', { class: 'verdict' + (working ? '' : ' warn') }, !judged
      ? `Early days: ${plural(A.applied + B.applied, 'Tier A or B application')} so far. Once there are 10, this shows whether Tier A really converts better.`
      : working ? 'Tier A is converting at least as well as Tier B. Your scoring is doing its job.'
        : 'Tier B is converting better than Tier A. Ask Claude for a search review: your scoring may need a change.'));

  // Gap plan
  const top = (D.gaps.skills || []).slice(0, 3);
  const lift = u => { const m = u.match(/^(.*): (\d+) ([A-Z]) -> (\d+) ([A-Z])$/);
    if (!m) return h('div', { class: 'lift' }, u);
    return h('div', { class: 'lift' }, h('span', {}, m[1].replace(/, /, ' · ')),
      h('span', { class: 'jump', 'aria-label': `from ${m[2]}, tier ${m[3]}, to ${m[4]}, tier ${m[5]}` },
        m[2], tier(m[3]), svg(ICON_ARROW, 13), m[4], tier(m[5]))); };
  const gaps = h('section', { class: 'glass pane', 'aria-labelledby': 'gaps-h' },
    h('div', { class: 'pane-head' }, h('h2', { id: 'gaps-h' }, 'What to learn next')),
    top.length ? top.map(s => h('div', { class: 'gap' },
      h('div', { class: 'skill' }, h('b', {}, s.skill), h('span', {}, `missing in ${plural(s.roles_with_gap, 'role')}`)),
      h('div', { class: 'why' }, s.tier_upgrades.length
        ? `Having it would move ${plural(s.tier_upgrades.length, 'open role')} up a tier:`
        : `Worth about ${s.avg_points_if_closed} points per role, with no tier changes yet.`),
      s.tier_upgrades.slice(0, 3).map(lift)))
      : h('p', { class: 'calm' }, 'Score a few roles and the skills holding you back will show up here.'),
    (D.gaps.notes || []).map(n => h('p', { class: 'aside' }, n[0].toUpperCase() + n.slice(1) + '.')),
    top.length ? h('p', { class: 'aside' }, 'Ask Claude “what should I learn?” for a plan to close the top one.') : null);

  // Closed
  const closed = R.filter(r => CLOSED.includes(r.Status));
  const stages = {};
  closed.filter(r => r.Status === 'Rejected').forEach(r => { const k = r['Rejected At'] || 'unknown stage'; stages[k] = (stages[k] || 0) + 1; });
  const closedEl = closed.length ? h('details', { class: 'glass closed' },
    h('summary', {}, h('span', {}, h('b', {}, plural(closed.length, 'closed role')),
      Object.keys(stages).length ? ' · rejected at ' + Object.entries(stages).map(([k, v]) => `${k.toLowerCase()} (${v})`).join(', ') : ''),
      svg(ICON_CHEVRON, 18)),
    h('table', {}, h('thead', {}, h('tr', {}, ['Company', 'Role', 'Outcome', 'Tier'].map(c => h('th', { scope: 'col' }, c)))),
      h('tbody', {}, closed.map(r => h('tr', {}, h('td', {}, r.Company), h('td', {}, r.Role),
        h('td', {}, r.Status + (r['Rejected At'] ? ` at ${r['Rejected At'].toLowerCase()}` : '')), h('td', {}, tier(r.Tier)))))))
    : null;

  app.replaceChildren(
    h('div', { class: 'lead' }, next, counts),
    h('div', { class: 'section-head' }, h('h2', {}, 'Pipeline'), h('span', { class: 'hint' }, 'best match first in each stage')),
    lanes,
    h('div', { class: 'insight' }, rubric, gaps),
    closedEl);
}
sel.onchange = render;
q.oninput = render;

// The artifact page keeps no data in its source: it reads one snapshot document that Job Buddy
// writes to the artifact's private store after every tracker change, and follows it live.
async function connect() {
  D = { mode: 'artifact', state: 'loading', rows: [], gaps: {} }; render();
  const timer = setTimeout(() => { if (D.state === 'loading') { D.state = 'offline'; render(); } }, 10000);
  const db = window.claude && window.claude.use ? await window.claude.use('db') : null;
  if (!db) { clearTimeout(timer); D.state = 'offline'; render(); return; }
  db.doc('dashboard/snapshot').onSnapshot(snap => {
    clearTimeout(timer);
    const d = snap.exists ? snap.data() : null;
    D = d && Array.isArray(d.rows) ? { mode: 'artifact', rows: d.rows, gaps: d.gaps || {}, generated: d.generated, person: d.person || {} }
      : { mode: 'artifact', rows: [], gaps: {} };
    today = new Date((D.generated || new Date().toISOString().slice(0, 10)) + 'T12:00:00');
    setTracks(); render();
  }, () => { clearTimeout(timer); D.state = 'offline'; render(); });
}
function start() {
  if (D.mode === 'artifact') {
    document.getElementById('where').textContent =
      'Kept up to date by Job Buddy from your tracker. Private to your Claude account; only you can see it unless you share it.';
    connect();
  } else { setTracks(); render(); }
}
start();
</script>
"""


# Only the columns the page shows. Notes, Top Gap, sources and dates the page never displays stay
# in the tracker, so the online copy holds as little as possible.
SHOWN = ("Company", "Role", "Track", "Tier", "Fit Score", "Status", "Rejected At", "Next Action",
         "Materials", "Job URL", "Date Found", "Last Update")


def snapshot(rows, gaps, generated, person=None):
    """The dashboard's data: what the local page embeds and what the artifact's store holds.
    person: {"name": first name only, "tracks": [track names]} from profile.md."""
    rows = [{k: r[k] for k in SHOWN if r.get(k) not in (None, "")} for r in rows]
    return {"generated": generated, "rows": rows, "person": person or {},
            "gaps": {"skills": gaps.get("skills", [])[:5], "notes": gaps.get("notes", [])}}


def _fill(part, data):
    # Embedded as JSON inside <script type="application/json">; escaping "<" stops any text in
    # the tracker (a job title, a note) from closing the tag and running as code.
    blob = json.dumps(data, ensure_ascii=False, default=str).replace("<", "\\u003c")
    return part.replace("__LOGO__", LOGO_MASK_PNG_B64).replace("__DATA__", blob)


def render(rows, gaps, generated, person=None):
    """The local dashboard.html: a complete document with the data embedded."""
    head = '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    return ('<!doctype html>\n<html lang="en" data-theme="light">\n<head>\n' + head + _fill(HEAD, {}) +
            '</head>\n<body>\n' + _fill(BODY, snapshot(rows, gaps, generated, person)) + '</body>\n</html>\n')


def render_artifact():
    """The page published once as the user's private Claude artifact. It carries no data: the
    publish step wraps it in a document, and the page reads dashboard/snapshot from its store."""
    return _fill(HEAD, {}) + _fill(BODY, {"mode": "artifact", "rows": [], "gaps": {}})
