// Job Buddy: browser collector.
// Claude runs this inside the Claude desktop app's built-in browser (works on Windows and Mac).
// It fetches public job feeds, filters them in the page, and returns only short rows,
// so the raw listings never reach Claude's context.
//
// Usage (Claude pastes this file, then calls):
//   await JSA.run(CONFIG)          // from a builtindublin.ie page: ATS + remote feeds + Built In
//   await JSA.jobsie(CONFIG)       // from any jobs.ie page (sister site of IrishJobs)
// Indeed is covered by Indeed's own connector (search_jobs), not by this script.
//
// CONFIG = {
//   include: ["revenue operations","revops","business systems"],   // title must contain one
//   exclude: ["account executive","sdr","director","intern"],      // title must contain none
//   places:  ["dublin","ireland"],                                // on-site/hybrid locations
//   remote:  ["ireland","emea","europe","worldwide","anywhere"],   // acceptable remote regions ([] = no remote)
//   days: 14,                                                     // max posting age
//   seen: ["wayflyer|gtm engineer", ...],                         // company|title keys already handled
//   companies: [{n:"Intercom",ats:"greenhouse",s:"intercom"}, ...],
//   feeds: ["remotive","arbeitnow","remoteok"],                   // optional remote/EU feeds
//   builtin: true                                                 // search Built In Dublin with each include term
// }
window.JSA = (() => {
  const low = s => (s || '').toLowerCase();
  const key = (c, t) => low(c).replace(/[^a-z0-9]/g, '') + '|' + low(t).replace(/\s+/g, ' ').trim();
  const ageDays = d => { const t = typeof d === 'number' ? d : Date.parse(d); return isNaN(t) || !d ? null : Math.round((Date.now() - t) / 864e5); };
  const relDays = s => { s = low(s); if (/hour|today|just/.test(s)) return 0; if (/yesterday/.test(s)) return 1;
    const m = s.match(/(\d+)\s*(day|week|month)/); return m ? +m[1] * ({ day: 1, week: 7, month: 30 })[m[2]] : null; };

  function keep(cfg, r) {
    const t = low(r.t), l = low(r.l);
    if (!cfg.include.some(w => t.includes(low(w)))) return 'title';
    if ((cfg.exclude || []).some(w => t.includes(low(w)))) return 'excluded';
    const isRemote = /remote|anywhere|worldwide/.test(l) || r.remote;
    const placeOk = cfg.places.some(p => l.includes(low(p)));
    const remoteOk = isRemote && (cfg.remote || []).some(p => l.includes(low(p)) || (p === 'anywhere' && /anywhere|worldwide/.test(l)));
    if (!placeOk && !remoteOk) return 'location';
    if (r.age != null && r.age > (cfg.days || 14)) return 'old';
    if ((cfg.seen || []).includes(key(r.c, r.t))) return 'seen';
    return null;
  }

  const j = async u => { const r = await fetch(u); if (!r.ok) throw new Error(r.status); return r.json(); };
  const ats = {
    greenhouse: async x => (await j(`https://boards-api.greenhouse.io/v1/boards/${x.s}/jobs`)).jobs.map(p =>
      ({ c: x.n, t: p.title, l: p.location?.name, age: ageDays(p.first_published || p.updated_at), u: p.absolute_url, id: 'gh:' + p.id })),
    lever: async x => (await j(`https://api.lever.co/v0/postings/${x.s}?mode=json`)).map(p =>
      ({ c: x.n, t: p.text, l: [p.categories?.location, p.workplaceType].join(' '), age: ageDays(p.createdAt), u: p.hostedUrl, id: 'lv:' + p.id })),
    ashby: async x => (await j(`https://api.ashbyhq.com/posting-api/job-board/${x.s}`)).jobs.map(p =>
      ({ c: x.n, t: p.title, l: [p.location, ...(p.secondaryLocations || []).map(s => s.location), p.isRemote ? 'remote' : ''].join(' '), age: ageDays(p.publishedAt), u: p.jobUrl, id: 'ab:' + p.id })),
    smartrecruiters: async x => (await j(`https://api.smartrecruiters.com/v1/companies/${x.s}/postings?limit=100`)).content.map(p =>
      ({ c: x.n, t: p.name, l: [p.location?.city, p.location?.country, p.location?.remote ? 'remote' : ''].join(' '), age: ageDays(p.releasedDate), u: `https://jobs.smartrecruiters.com/${x.s}/${p.id}`, id: 'sr:' + p.id })),
    workable: async x => (await j(`https://apply.workable.com/api/v1/widget/accounts/${x.s}`)).jobs.map(p =>
      ({ c: x.n, t: p.title, l: [p.city, p.country, p.telecommuting ? 'remote' : ''].join(' '), age: ageDays(p.published_on || p.created_at), u: p.url, id: 'wk:' + p.shortcode })),
  };
  const feeds = {
    remotive: async () => (await j('https://remotive.com/api/remote-jobs?limit=300')).jobs.map(p =>
      ({ c: p.company_name, t: p.title, l: 'remote ' + p.candidate_required_location, age: ageDays(p.publication_date), u: p.url, remote: true })),
    arbeitnow: async () => (await j('https://www.arbeitnow.com/api/job-board-api')).data.map(p =>
      ({ c: p.company_name, t: p.title, l: p.location + (p.remote ? ' remote europe' : ''), age: ageDays(p.created_at * 1000), u: p.url, remote: p.remote })),
    remoteok: async () => (await j('https://remoteok.com/api')).filter(p => p.position).map(p =>
      ({ c: p.company, t: p.position, l: 'remote ' + (p.location || 'worldwide'), age: ageDays(p.date), u: p.url, remote: true })),
  };
  async function builtin(cfg) {
    const out = [];
    for (const q of cfg.include) {
      const d = new DOMParser().parseFromString(await (await fetch('/jobs?search=' + encodeURIComponent(q) + '&daysSinceUpdated=' + (cfg.days || 14))).text(), 'text/html');
      d.querySelectorAll('[data-id="job-card"]').forEach(card => {
        const a = card.querySelector('a[href*="/job/"]'); if (!a) return;
        const txt = card.innerText.replace(/\s+/g, ' ');
        const comp = card.querySelector('[data-id="company-title"]')?.innerText || txt.split(' ')[0];
        out.push({ c: comp, t: a.innerText.trim(), l: txt, age: relDays(txt), u: new URL(a.getAttribute('href'), location.origin).href });
      });
    }
    return out;
  }

  function finish(cfg, all, errors) {
    const stats = {}, rows = [], dup = new Set();
    for (const r of all) {
      const why = keep(cfg, r); if (why) { stats[why] = (stats[why] || 0) + 1; continue; }
      const k = key(r.c, r.t); if (dup.has(k)) { stats.duplicate = (stats.duplicate || 0) + 1; continue; } dup.add(k);
      rows.push([r.src, r.c, r.t, (r.l || '').replace(/\s+/g, ' ').slice(0, 60), r.age ?? '?', r.u].join(' | '));
    }
    return `checked ${all.length} | kept ${rows.length} | dropped ${JSON.stringify(stats)}` +
      (errors.length ? `\nerrors: ${errors.join('; ')}` : '') + '\n' + rows.join('\n');
  }

  async function run(cfg) {
    const all = [], errors = [];
    const tag = (src, list) => list.forEach(r => { r.src = src; all.push(r); });
    await Promise.all([
      ...(cfg.companies || []).map(x => (ats[x.ats] ? ats[x.ats](x) : Promise.reject(new Error('unknown ats')))
        .then(l => tag(x.ats, l)).catch(e => errors.push(`${x.n}(${x.ats}): ${e.message}`))),
      ...(cfg.feeds || []).map(f => feeds[f]().then(l => tag(f, l)).catch(e => errors.push(`${f}: ${e.message}`))),
    ]);
    if (cfg.builtin && location.hostname.includes('builtindublin')) {
      try { tag('builtin', await builtin(cfg)); } catch (e) { errors.push('builtin: ' + e.message); }
    }
    return finish(cfg, all, errors);
  }

  // Jobs.ie (sister site of IrishJobs): run from any jobs.ie page; one search per include term.
  async function jobsie(cfg) {
    const all = [], errors = [], place = (cfg.jobsiePlace || 'dublin');
    for (const q of cfg.include) {
      try {
        const slug = low(q).replace(/[^a-z0-9]+/g, '-');
        const d = new DOMParser().parseFromString(await (await fetch(`/jobs/${slug}/in-${place}?postedWithin=${cfg.days || 14}`)).text(), 'text/html');
        d.querySelectorAll('style,script').forEach(s => s.remove());
        d.querySelectorAll('article').forEach(a => {
          const g = s => a.querySelector(`[data-at="${s}"]`)?.textContent.trim() || '';
          const link = a.querySelector('[data-at="job-item-title"]'); if (!link) return;
          all.push({ src: 'jobs.ie', c: g('job-item-company-name'), t: link.textContent.trim(),
            l: g('job-item-location') + ' ' + g('job-item-salary-info'), age: relDays(g('job-item-timeago')),
            u: new URL(link.getAttribute('href'), location.origin).href });
        });
      } catch (e) { errors.push(`jobs.ie "${q}": ${e.message}`); }
    }
    return finish(cfg, all, errors);
  }

  return { run, jobsie, key };
})();
'JSA loaded';
