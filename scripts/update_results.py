#!/usr/bin/env python3
"""
Pull live 2026 World Cup results and write them to data/results.json, then rebuild.

No manual score entry needed: this maps each finished match to our fixture list by
the pair of teams, records the score (oriented to our home/away), flags penalty
shootouts, and lets build.py regenerate index.html.

Data sources (first available wins):
  1. football-data.org  — set env DC_FOOTBALL_TOKEN (free key). Clean PK data.
  2. TheSportsDB free   — keyless fallback (set DC_SPORTSDB_LEAGUE if needed).

Run:
  DC_FOOTBALL_TOKEN=xxxx python3 scripts/update_results.py
  python3 scripts/update_results.py            # uses TheSportsDB fallback
  python3 scripts/update_results.py --selftest # offline mapping test, no network

Designed to run unattended in CI (see .github/workflows/build.yml).
"""
import os, sys, json, re, datetime, unicodedata, urllib.request, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)
import build  # reuse GROUP_SCHEDULE + canonical names

# ---- name normalization: API names -> our canonical names ----
ALIASES = {
    "korea republic":"South Korea","south korea":"South Korea","republic of korea":"South Korea",
    "cote d'ivoire":"Ivory Coast","côte d'ivoire":"Ivory Coast","ivory coast":"Ivory Coast",
    "usa":"United States","united states":"United States","united states of america":"United States",
    "turkiye":"Turkiye","turkey":"Turkiye","türkiye":"Turkiye",
    "czechia":"Czechia","czech republic":"Czechia",
    "dr congo":"Congo DR","democratic republic of congo":"Congo DR","congo dr":"Congo DR","congo dr.":"Congo DR",
    "curacao":"Curacao","curaçao":"Curacao",
    "bosnia and herzegovina":"Bosnia and Herzegovina","bosnia & herzegovina":"Bosnia and Herzegovina","bosnia-herzegovina":"Bosnia and Herzegovina",
    "cape verde":"Cape Verde","cabo verde":"Cape Verde",
    "iran":"Iran","ir iran":"Iran","islamic republic of iran":"Iran",
}
def canon(name):
    if not name: return None
    n = unicodedata.normalize("NFKD", name).encode("ascii","ignore").decode().strip().lower()
    if n in ALIASES: return ALIASES[n]
    # title-case fallback, then check it's a real team
    guess = " ".join(w.capitalize() for w in n.split())
    return guess

# valid team set + pair->fixture lookup
TEAMS = {t for ts in build.REAL_GROUPS.values() for t in ts}
def _sq(s):  # squash to letters/digits only, dropping "and" — separator-insensitive
    s = unicodedata.normalize("NFKD", s or "").encode("ascii","ignore").decode().lower()
    s = re.sub(r"\band\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s)
def resolve(name):
    c = canon(name)
    if c in TEAMS: return c
    cl = (c or "").lower()
    for t in TEAMS:
        if t.lower()==cl: return t
    s = _sq(name)
    for t in TEAMS:
        ts = _sq(t)
        if len(ts) >= 4 and (ts in s or s in ts): return t
    return None

PAIR_TO = {}      # frozenset(home,away) -> (num, home, away)
for (num,grp,md,date,venue,home,away) in build.GROUP_SCHEDULE:
    PAIR_TO[frozenset((home,away))] = (num, home, away)

def record(api_home, api_away, hs, as_, pk_winner=None):
    """Return (num, (home_score,away_score), pk_winner_or_None) oriented to our fixtures, or None."""
    h, a = resolve(api_home), resolve(api_away)
    if not h or not a: return None
    key = frozenset((h, a))
    if key not in PAIR_TO: return None     # not a group-stage pair we track (e.g. knockout)
    num, myH, myA = PAIR_TO[key]
    if h == myH: res = (int(hs), int(as_))
    else:        res = (int(as_), int(hs))
    pkw = resolve(pk_winner) if pk_winner else None
    return num, res, pkw

ROUND_MAP = {"LAST_32":"R32","LAST_16":"R16","QUARTER_FINALS":"QF",
             "SEMI_FINALS":"SF","THIRD_PLACE":"BRONZE","FINAL":"FINAL"}

# ---------- source 1: football-data.org ----------
def fetch_football_data(token):
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    req = urllib.request.Request(url, headers={"X-Auth-Token": token})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    out, unmapped, ko = {}, [], []
    for m in data.get("matches", []):
        stage = m.get("stage")
        ft = m.get("score", {}).get("fullTime", {})
        fin = m.get("status") == "FINISHED"
        if stage in ROUND_MAP:  # knockout match
            h = resolve((m.get("homeTeam") or {}).get("name"))
            a = resolve((m.get("awayTeam") or {}).get("name"))
            if not h or not a: continue   # team still TBD
            pkw = None
            if m.get("score", {}).get("duration") == "PENALTY_SHOOTOUT":
                w = m["score"].get("winner")
                pkw = h if w=="HOME_TEAM" else a if w=="AWAY_TEAM" else None
            ko.append({"round": ROUND_MAP[stage], "home": h, "away": a,
                       "hs": ft.get("home"), "as": ft.get("away"),
                       "status": "final" if fin else "scheduled", "pkWinner": pkw,
                       "date": (m.get("utcDate") or "")[:10]})
            continue
        # group stage
        if not fin or ft.get("home") is None: continue
        pkw = None
        if m.get("score", {}).get("duration") == "PENALTY_SHOOTOUT":
            w = m["score"].get("winner")
            pkw = m["homeTeam"]["name"] if w=="HOME_TEAM" else m["awayTeam"]["name"] if w=="AWAY_TEAM" else None
        r = record(m["homeTeam"]["name"], m["awayTeam"]["name"], ft["home"], ft["away"], pkw)
        if r: out[r[0]] = (r[1], r[2])
        else: unmapped.append(f'{m["homeTeam"]["name"]} vs {m["awayTeam"]["name"]}')
    if unmapped: print("  ⚠ unmapped FINISHED matches:", " | ".join(unmapped))
    return out, ko

# ---------- source 2: TheSportsDB (keyless) ----------
def fetch_sportsdb():
    league = os.environ.get("DC_SPORTSDB_LEAGUE", "4429")  # FIFA World Cup
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsseason.php?id={league}&s=2026"
    data = json.load(urllib.request.urlopen(url, timeout=30))
    out = {}
    for e in (data.get("events") or []):
        if (e.get("strStatus") or "").lower() not in ("match finished","ft","finished","aet","pen"):
            if e.get("intHomeScore") is None: continue
        hs, as_ = e.get("intHomeScore"), e.get("intAwayScore")
        if hs is None or as_ is None: continue
        r = record(e.get("strHomeTeam"), e.get("strAwayTeam"), hs, as_)
        if r: out[r[0]] = (r[1], r[2])
    return out

def selftest():
    samples = [("Mexico","South Africa",2,0),("Korea Republic","Czechia",2,1),
               ("USA","Paraguay",4,1),("Côte d'Ivoire","Ecuador",1,0),("Germany","Curaçao",7,1)]
    ok=0
    for h,a,hs,as_ in samples:
        r=record(h,a,hs,as_)
        print(f"  {h} {hs}-{as_} {a}  ->  {r}")
        if r: ok+=1
    print(f"selftest mapped {ok}/{len(samples)}"); return ok==len(samples)

def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    results, ko, src = {}, [], None
    token = os.environ.get("DC_FOOTBALL_TOKEN")
    try:
        if token:
            results, ko = fetch_football_data(token); src="football-data.org"
        else:
            results = fetch_sportsdb(); src="TheSportsDB"
    except Exception as e:
        print("  ! live fetch failed:", e)
        # fall back to whatever's already in results.json (keep last good)
    if not results and not ko:
        print("No results fetched; leaving results.json unchanged.")
    else:
        payload = {"updated": datetime.datetime.now(datetime.timezone.utc).isoformat(), "source": src,
                   "results": {str(k): list(v[0]) for k,v in results.items()},
                   "pk": {str(k): v[1] for k,v in results.items() if v[1]},
                   "knockout": ko}
        os.makedirs(DATA, exist_ok=True)
        json.dump(payload, open(os.path.join(DATA,"results.json"),"w"), indent=2)
        print(f"Wrote {len(results)} group + {len(ko)} knockout results from {src} -> data/results.json")
    subprocess.check_call([sys.executable, os.path.join(HERE,"build.py")])

if __name__ == "__main__":
    main()
