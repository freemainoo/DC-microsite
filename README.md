# 🏆 DC World Cup — Draft League Dashboard

A self-contained, **league-wide** dashboard for the DC World Cup draft: 8 owners,
6 teams each, all 48 teams of the 2026 World Cup owned uniquely. Pick any manager
from the header dropdown and every tab switches to their view.

## Scoring (results only)

**3** win · **1** draw · **0** loss · penalty shootout: **winner 3 / loser 1**. No goals or round bonuses.
Standings are computed live from match results and reproduce the organizer's sheet totals exactly.

## Views

- **Standings** — all 8 owners ranked live (W-D-L, teams alive, GD) + points chart.
- **{Manager}'s Team** — the selected manager's 6 teams: points, form, group table, fixtures + venues, alive status.
- **All Rosters** — every squad with per-team points and alive/out dots.
- **Fixtures (owner vs owner)** — every match is a head-to-head between two owners; shows the group and venue; filterable.
- **Draft Board** — the snake grid, a points-vs-pick value scatter, biggest steals & busts, and owner draft efficiency.
- **Head-to-Head** — league-wide manager-vs-manager matchup grid plus personal rivalry detail.
- **Bracket** — the live knockout bracket with owner-color dots per team.
- **Team Simulations** — exact enumeration of every remaining bracket outcome (even-odds or Elo-weighted), a "who can still win" leaderboard, decisive-game and clinch/elimination watch, and a click-through "Manual Simulator" what-if bracket with its own live leaderboard (sandboxed from real results).
- **Enter Results** — manual override of any score (saved in your browser).

Use the **“Viewing as” dropdown** in the header to become any manager (remembered next visit), or pick *League view* for a neutral overview.

## Architecture & data pipeline

```
data/draft.json     (owners, rosters, snake draft)   ─┐
data/results.json   (live scores, auto-written)       ├─►  scripts/build.py  ─►  index.html
scripts/build.py    (fixtures, schedule, scoring)     ─┘        ▲
scripts/update_results.py  ── pulls live results ──────────────┘
```

- **`scripts/build.py`** — single source for the draft, fixtures, venues, and scoring. Reads `data/results.json` (live) on top of a hardcoded seed, then writes `index.html` + `data/*.json`.
- **`scripts/update_results.py`** — pulls live 2026 World Cup results, maps each finished match to our fixtures (by team pair, orientation-aware, with penalty-shootout detection), writes `data/results.json`, and rebuilds.
- **`index.html`** — the deployable, dependency-free dashboard (just opens).

### Run locally

```bash
python3 scripts/build.py            # rebuild from current data
python3 scripts/update_results.py   # pull live results, then rebuild
python3 scripts/update_results.py --selftest   # offline name-mapping test
```

## Automatic live updates (no manual entry)

Once pushed to GitHub, **`.github/workflows/build.yml`** runs every 30 minutes: it pulls
live results, rebuilds, commits `data/results.json`, and redeploys GitHub Pages.

**Data source (pick one):**
- **Best:** get a free API key from [football-data.org](https://www.football-data.org/), then add it as a repo secret named **`DC_FOOTBALL_TOKEN`** (Settings → Secrets and variables → Actions). Cleanest data incl. penalty shootouts.
- **Keyless fallback:** leave the secret unset — it uses TheSportsDB's free endpoint automatically.

## Export to GitHub (step by step)

1. Create a new GitHub repo and upload this whole `DC World CUp/` folder.
2. **Settings → Pages → Source: GitHub Actions**.
3. (Optional but recommended) add the `DC_FOOTBALL_TOKEN` secret.
4. The workflow auto-runs; your live dashboard lands at `https://<user>.github.io/<repo>/`.

## Folder layout

```
DC World CUp/
├── index.html                    ← the dashboard (open this)
├── data/
│   ├── draft.json                 · owners, rosters, snake draft
│   ├── worldcup.json              · groups, fixtures, venues
│   └── results.json               · live scores (auto-written; created on first update)
├── scripts/
│   ├── template.html              · dashboard source
│   ├── build.py                   · data → index.html
│   └── update_results.py          · live results → results.json → build
├── .github/workflows/build.yml    ← auto pull + build + deploy
├── .gitignore
└── README.md
```

## Manual fixes

If a feed is wrong or lags, edit `KNOWN_RESULTS` (or `PK_WINNERS`) in `scripts/build.py` and
rebuild — anything in `results.json` from the feed still takes precedence, so for a hard override
clear that match from `results.json` too, or just use the in-dashboard **Enter Results** tab.
