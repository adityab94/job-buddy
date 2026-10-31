# The dashboard

Two copies of the same page, built by `scripts/jb.py` from the tracker:

- **Local** (always): `dashboard.html` in the job-search folder. Works offline, sends nothing
  anywhere. Opened by double-click or in the built-in browser.
- **In Claude** (optional, the user chooses): a private artifact in the user's own Claude
  account. Always one click away in the Claude sidebar, also on their phone, and it updates
  itself. Only they can see it unless they share it from its Share menu.

`jb.py tracker upsert` and `jb.py dashboard <workspace>` write `dashboard.html` and
`dashboard-data.json` (the online copy's data: only the columns the page shows, no notes, no
CV). The online page is published once and never carries data in its source; it reads one
document, `dashboard/snapshot`, from its own store and follows it live.

## Offering it (setup, or when they ask "can I see this on my phone?")

Only when the Artifact and ArtifactData tools exist in this session. If they don't, say the
online dashboard isn't available in this Claude app and carry on with the local file; record
`- Online dashboard: not available here` under `## Dashboard` in profile.md.

Ask once, plainly: "Would you like your dashboard in your Claude sidebar as well? It's private
to your Claude account and updates itself. It stores your roles, tiers, scores and statuses
there, but not your CV or notes. You can still use the local file." Record the answer under
`## Dashboard` in profile.md (`- Online dashboard: off` when they decline) and don't ask again
unless they raise it.

## Creating it (once)

1. `jb.py dashboard <workspace> --artifact-page` writes `dashboard-artifact.html`.
2. Publish that file with the Artifact tool: `icon: "chart"`, description "Your private Job
   Buddy dashboard, updated from your tracker.", and
   `capabilities: {"db": {"rules": [{"path": "dashboard", "read": "view", "write": "owner"}]}}`
   (only the owner can change the data).
3. Write the data: ArtifactData `set`, `url` = the new link, `collection: "dashboard"`,
   `doc_id: "snapshot"`, `file_path` = `<workspace>/dashboard-data.json` (a new document, so
   no `if_version`).
4. Record under `## Dashboard` in profile.md:
   `- Online dashboard: <link>`, `- Page version: <this skill's Version>`,
   `- Data version: <the version the set returned>`.
5. Give them the link and offer to pin it to their sidebar (Artifact `pin`, only on a yes).

## Keeping it current

At the end of any task that changed the tracker (not after every row), when profile.md has an
online dashboard link:

1. ArtifactData `set` the snapshot again from `dashboard-data.json`, with
   `if_version` = the recorded Data version. Record the new version it returns.
2. If the write is refused because the version moved (they opened it elsewhere, or a second
   computer), read it with ArtifactData `get` and `out_dir` (so the data isn't pulled into the
   conversation), take the version from the result, and set again once.
3. If the artifact is gone (deleted, or no access), say so in one line and offer to create a
   new one. Never recreate it unasked.

Mention it in one line ("Your dashboard is updated") rather than describing the update.

When this skill's Version is newer than the recorded Page version, the page design has changed:
run `jb.py dashboard <workspace> --artifact-page`, read the artifact once (Artifact `read` with
its `url`, which a publish from a new conversation requires), publish `dashboard-artifact.html`
to the same `url` without `capabilities` (keeps the rules and the data), and update Page
version.

## Turning it off

If they ask to stop: remove the link from profile.md and set `- Online dashboard: off`. Delete
the artifact itself only if they ask for that too; deletion can't be undone.
