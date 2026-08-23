---
name: add-stratagems
description: >-
  Discover, map, generate, and ship new HELLDIVERS 2 stratagems for the
  StreamController plugin, including plugin PRs, local testing, and
  StreamController-Store hash bumps. Use when the user invokes add-stratagems,
  asks to add new stratagems, run discover, ship a plugin version, open a store
  PR, or restore the local StreamController install.
disable-model-invocation: true
---

# Add Helldivers 2 Stratagems

End-to-end workflow for new in-game stratagems. Read [AGENTS.md](../../../AGENTS.md) for label rules. Read [local.md](local.md) before any local StreamController or store-fork step.

Do **not** commit or push unless the user asks.

Resolve paths at runtime. Never assume a home directory, clone location, GitHub user, or remotes. See [local.md](local.md).

## Phase selection

| User says | Run |
|-----------|-----|
| invoke skill / add new stratagems / discover | Phases 1-5, then stop |
| commit / PR / ship | Phase 6 |
| test locally / link into StreamController | Phase 7 |
| store PR | Phase 8 (plugin must already be on `origin/main`) |
| restore store plugin / re-enable auto-update | Phase 9 |

## Phase 1: Fresh main

Work in the plugin repo root (directory that contains `update/config.py` and `manifest.json` with id `net_jslay_helldivers_2`).

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git checkout -b feat/vX.Y.Z-new-stratagems
```

`X.Y.Z` is current `manifest.json` version with the minor bumped (2.3.1 → 2.4.0). Patch bumps are for fixes only.

## Phase 2: Discover

```bash
python3 --version
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r update/requirements.txt
python -m update discover -v
```

`discover` only prints candidates. It does **not** write `config.py`. Suggested `"svg"` values that copy the wiki name are usually wrong.

## Phase 3: Map into `update/config.py`

`STRATAGEM_MAPPINGS` is the only file to edit by hand. Never edit `stratagems.json`, `locales/en_US.json`, or icons except via generate.

### Treat wiki-missing as a rename first

If discover reports `WIKI ENTRIES NOT FOUND` plus a new wiki name that is clearly the same stratagem (same sequence, wiki redirect, "renamed from" on the wiki page):

- Keep the existing **key**
- Update `wiki` (and `name` if the game renamed it)
- Keep `svg` unless the SVG repo also renamed the file

### Match wiki to SVG yourself

Wiki uses model numbers (`MG-43 Machine Gun`). SVG repo uses short names (`Machine Gun`). Cross-check unmapped SVG names from discover, then the SVG repo: https://github.com/nvigneux/Helldivers-2-Stratagems-icons-svg

Normalize by stripping prefixes like `A/GM-17`, `B/FLAM-80`, `EXO-51`, `M-103`, `40-K`.

### Missing SVGs

Mission/objective items often have no SVG. Reuse:

- Intel / data / camera → `Upload Data`
- Drills that share an icon on the wiki → that drill's SVG (`Prospecting Drill`, `Hive Breaker Drill`, …)

### Keys, names, grouping

- **Never rename existing keys** (action IDs). New keys: PascalCase, short, unique (`Meltagun`, `BulletStorm`, `SupplyFRV`)
- `name`: 2-3 words for labels. Keep the distinctive word last
- Add a `# WARBOND / SHIP MODULE` comment section matching existing style
- Confirm the wiki page exists and the sequence looks real before adding

## Phase 4: Generate and verify

```bash
source .venv/bin/activate
python -m update generate-all --skip-pages -v
python -m update discover -v    # must be 0 new wiki, 0 unmapped SVGs
python -m update validate       # no errors; extra CLASS/custom icons are fine
```

Always `--skip-pages` unless the user gives an explicit `--pages-dir`. The default pages path is not the StreamController install.

Expect only: `config.py`, `stratagems.json`, `locales/en_US.json`, **new** icon PNGs, version files. If existing PNGs rewrite with no visual change, leave them unstaged.

## Phase 5: Version

Bump both:

- `manifest.json` → `version`
- `main.py` → `plugin_version=`

Same `X.Y.Z` as the branch name.

## Phase 6: Plugin PR

Only after the user asks to commit/push/PR.

- Title: `vX.Y.Z: Add new stratagems from recent warbonds` (or the actual reason)
- Body: terse bullets, list new keys/names, call out renames that kept their key
- Push to `origin` and open the PR against that remote's default branch
- Follow the user's git/PR rules (HEREDOC commit, `gh pr create`)

If they name a related issue, put the full URL in the PR body.

## Phase 7: Local install test

See [local.md](local.md). Summary:

1. Locate the StreamController data dir and the installed `net_jslay_helldivers_2` plugin
2. Backup that plugin directory if it is a real directory
3. Symlink this git checkout over it
4. Set `store.auto-update` to `false` **before** StreamController restarts (auto-update compares SHAs and `rmtree`s the plugin path; that can follow the symlink into this repo)
5. Restart or launch StreamController
6. Launch the tester if asked:

```bash
source .venv/bin/activate
python test_stratagems.py
```

## Phase 8: Store PR

Only after the plugin change is on `origin/main` (merge commit SHA).

Locate a StreamController-Store checkout (see [local.md](local.md)). Need remotes: `upstream` → `StreamController/StreamController-Store`, `origin` → the user's fork.

```bash
git fetch upstream
git checkout -B update-plugin-helldivers_2-<fullsha> upstream/main
```

In `Plugins.json`, set the helldivers entry `hash` to the **full** plugin-repo `origin/main` SHA (merge commit, not the feature commit). Schema is `{ "url", "hash" }` (not `commits`).

- Push to `origin`
- `gh pr create --repo StreamController/StreamController-Store --base main --head <fork-owner>:<branch>`
- Title: `update(helldivers_2): update hash for main`
- Body: new hash, plugin version, plugin PR URL, plus any issue URL they asked to link
- Check the store PR template boxes if they already tested locally

## Phase 9: Restore local install

See [local.md](local.md). Remove the symlink, move the backup back, set `store.auto-update` to `true`. Tell the user to restart StreamController if it is running.
