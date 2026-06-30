#!/usr/bin/env python3
"""
Build the self-contained DC World Cup *draft league* dashboard.

Pipeline:
  OWNERS (this file) + GROUP_SCHEDULE/KNOWN_RESULTS (this file)
      -> inject into scripts/template.html -> index.html  (+ data/*.json)

Draft league: 8 owners, 6 teams each, all 48 World Cup teams owned uniquely.
Scoring (results only): 3 win / 1 draw / 0 loss; in a penalty shootout the
winner gets 3 and the loser gets 1. No goals/round bonuses.

Re-run any time:  python3 scripts/build.py
"""
import json, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

SHEET = {"id": "1DimZR9C0GLFsrynySLqls2vBJ4580vcZxVcyZ9z9E6g", "gid": "0"}
ME = "Alon"

SCORING = {"win": 3, "draw": 1, "loss": 0, "pkWin": 3, "pkLoss": 1}

# ---- The draft: owner -> 6 teams (canonical names). All 48 teams, owned once. ----
OWNERS = {
    "Robert":   ["France","Croatia","South Korea","Australia","Bosnia and Herzegovina","Haiti"],
    "Max":      ["Spain","Japan","United States","Algeria","Congo DR","Curacao"],
    "Alon":     ["Portugal","Switzerland","Turkiye","Scotland","Paraguay","Iraq"],
    "Jay":      ["England","Norway","Uruguay","Sweden","Saudi Arabia","Jordan"],
    "Andrew B": ["Argentina","Belgium","Ecuador","Ivory Coast","Ghana","South Africa"],
    "Josh":     ["Brazil","Netherlands","Egypt","Czechia","Panama","New Zealand"],
    "Mrinal":   ["Germany","Colombia","Senegal","Canada","Cape Verde","Tunisia"],
    "Amit":     ["Morocco","Mexico","Austria","Iran","Qatar","Uzbekistan"],
}

# ---- Snake draft. Round 1 follows this order; even rounds reverse it.
# Each owner's roster above is listed in round order, so OWNERS[owner][r] is
# the team taken in round r+1. Verified against the sheet's pick numbers 1-17.
DRAFT_ORDER = ["Robert","Max","Alon","Jay","Andrew B","Josh","Mrinal","Amit"]
ROUNDS = 6

def build_draft():
    picks=[]; n=0
    for r in range(ROUNDS):
        order = DRAFT_ORDER if r%2==0 else list(reversed(DRAFT_ORDER))
        for owner in order:
            n+=1
            picks.append({"pick":n,"round":r+1,"slot":DRAFT_ORDER.index(owner)+1,
                          "owner":owner,"team":OWNERS[owner][r]})
    return picks

# ---- Real 2026 World Cup groups (names normalized to canonical). ----
REAL_GROUPS = {
    "A": ["Mexico","South Africa","South Korea","Czechia"],
    "B": ["Canada","Bosnia and Herzegovina","Qatar","Switzerland"],
    "C": ["Brazil","Morocco","Haiti","Scotland"],
    "D": ["United States","Paraguay","Australia","Turkiye"],
    "E": ["Germany","Curacao","Ivory Coast","Ecuador"],
    "F": ["Netherlands","Japan","Sweden","Tunisia"],
    "G": ["Belgium","Egypt","Iran","New Zealand"],
    "H": ["Spain","Cape Verde","Saudi Arabia","Uruguay"],
    "I": ["France","Senegal","Iraq","Norway"],
    "J": ["Argentina","Algeria","Austria","Jordan"],
    "K": ["Portugal","Congo DR","Uzbekistan","Colombia"],
    "L": ["England","Croatia","Ghana","Panama"],
}

# ---- Full group-stage schedule from the official FIFA poster (v17). ----
# (num, group, matchday, date, venue, home, away)
GROUP_SCHEDULE = [
    (1,"A",1,"Jun 11","Mexico City","Mexico","South Africa"),
    (2,"A",1,"Jun 11","Guadalajara","South Korea","Czechia"),
    (3,"B",1,"Jun 12","Toronto","Canada","Bosnia and Herzegovina"),
    (4,"D",1,"Jun 12","Los Angeles","United States","Paraguay"),
    (5,"C",1,"Jun 13","Boston","Haiti","Scotland"),
    (6,"D",1,"Jun 14","Vancouver","Australia","Turkiye"),
    (7,"C",1,"Jun 13","New York NJ","Brazil","Morocco"),
    (8,"B",1,"Jun 13","SF Bay Area","Qatar","Switzerland"),
    (9,"E",1,"Jun 14","Philadelphia","Ivory Coast","Ecuador"),
    (10,"E",1,"Jun 14","Houston","Germany","Curacao"),
    (11,"F",1,"Jun 14","Dallas","Netherlands","Japan"),
    (12,"F",1,"Jun 14","Monterrey","Sweden","Tunisia"),
    (13,"H",1,"Jun 15","Miami","Saudi Arabia","Uruguay"),
    (14,"H",1,"Jun 15","Atlanta","Spain","Cape Verde"),
    (15,"G",1,"Jun 15","Los Angeles","Iran","New Zealand"),
    (16,"G",1,"Jun 15","Seattle","Belgium","Egypt"),
    (17,"I",1,"Jun 16","New York NJ","France","Senegal"),
    (18,"I",1,"Jun 16","Boston","Iraq","Norway"),
    (19,"J",1,"Jun 16","Kansas City","Argentina","Algeria"),
    (20,"J",1,"Jun 16","SF Bay Area","Austria","Jordan"),
    (21,"L",1,"Jun 17","Toronto","Ghana","Panama"),
    (22,"L",1,"Jun 17","Dallas","England","Croatia"),
    (23,"K",1,"Jun 17","Houston","Portugal","Congo DR"),
    (24,"K",1,"Jun 17","Mexico City","Uzbekistan","Colombia"),
    (25,"A",2,"Jun 18","Atlanta","Czechia","South Africa"),
    (26,"B",2,"Jun 18","Los Angeles","Switzerland","Bosnia and Herzegovina"),
    (27,"B",2,"Jun 18","Vancouver","Canada","Qatar"),
    (28,"A",2,"Jun 18","Guadalajara","Mexico","South Korea"),
    (29,"C",2,"Jun 19","Philadelphia","Brazil","Haiti"),
    (30,"C",2,"Jun 19","Boston","Scotland","Morocco"),
    (31,"D",2,"Jun 19","SF Bay Area","Turkiye","Paraguay"),
    (32,"D",2,"Jun 19","Seattle","United States","Australia"),
    (33,"E",2,"Jun 20","Toronto","Germany","Ivory Coast"),
    (34,"E",2,"Jun 20","Kansas City","Ecuador","Curacao"),
    (35,"F",2,"Jun 20","Houston","Netherlands","Sweden"),
    (36,"F",2,"Jun 20","Monterrey","Tunisia","Japan"),
    (37,"H",2,"Jun 21","Miami","Uruguay","Cape Verde"),
    (38,"H",2,"Jun 21","Atlanta","Spain","Saudi Arabia"),
    (39,"G",2,"Jun 21","Los Angeles","Belgium","Iran"),
    (40,"G",2,"Jun 21","Vancouver","New Zealand","Egypt"),
    (41,"I",2,"Jun 22","New York NJ","Norway","Senegal"),
    (42,"I",2,"Jun 22","Philadelphia","France","Iraq"),
    (43,"J",2,"Jun 22","Dallas","Argentina","Austria"),
    (44,"J",2,"Jun 23","SF Bay Area","Jordan","Algeria"),
    (45,"L",2,"Jun 23","Boston","England","Ghana"),
    (46,"L",2,"Jun 23","Toronto","Panama","Croatia"),
    (47,"K",2,"Jun 23","Houston","Portugal","Uzbekistan"),
    (48,"K",2,"Jun 23","Guadalajara","Congo DR","Colombia"),
    (49,"C",3,"Jun 24","Miami","Scotland","Brazil"),
    (50,"C",3,"Jun 24","Atlanta","Morocco","Haiti"),
    (51,"B",3,"Jun 24","Vancouver","Switzerland","Canada"),
    (52,"B",3,"Jun 24","Seattle","Bosnia and Herzegovina","Qatar"),
    (53,"A",3,"Jun 24","Mexico City","Czechia","Mexico"),
    (54,"A",3,"Jun 24","Monterrey","South Africa","South Korea"),
    (55,"E",3,"Jun 25","Philadelphia","Curacao","Ivory Coast"),
    (56,"E",3,"Jun 25","New York NJ","Ecuador","Germany"),
    (57,"F",3,"Jun 25","Dallas","Japan","Sweden"),
    (58,"F",3,"Jun 25","Kansas City","Netherlands","Tunisia"),
    (59,"D",3,"Jun 25","Los Angeles","Turkiye","United States"),
    (60,"D",3,"Jun 25","SF Bay Area","Paraguay","Australia"),
    (61,"I",3,"Jun 26","Boston","Norway","France"),
    (62,"I",3,"Jun 26","Toronto","Senegal","Iraq"),
    (63,"G",3,"Jun 26","Seattle","Egypt","Iran"),
    (64,"G",3,"Jun 26","Vancouver","New Zealand","Belgium"),
    (65,"H",3,"Jun 26","Houston","Cape Verde","Saudi Arabia"),
    (66,"H",3,"Jun 26","Guadalajara","Uruguay","Spain"),
    (67,"L",3,"Jun 27","New York NJ","Panama","England"),
    (68,"L",3,"Jun 27","Philadelphia","Croatia","Ghana"),
    (69,"J",3,"Jun 27","Kansas City","Algeria","Austria"),
    (70,"J",3,"Jun 27","Dallas","Jordan","Argentina"),
    (71,"K",3,"Jun 27","Miami","Colombia","Portugal"),
    (72,"K",3,"Jun 27","Atlanta","Congo DR","Uzbekistan"),
]

KO_SCHEDULE = [
    ("Round of 32","Jun 28 – Jul 3"),
    ("Round of 16","Jul 4 – Jul 7"),
    ("Quarter-finals","Jul 9 – Jul 11"),
    ("Semi-finals","Jul 14 – Jul 15"),
    ("Third place","Jul 18"),
    ("Final","Jul 19  ·  MetLife Stadium, NY/NJ"),
]

# ---- Knockout bracket skeleton (official 2026 feeder map). ----
# Each: (match#, round, sideA, sideB). Slot codes:
#   W:A win of group A · R:B runner-up of group B · T:CDEFH best 3rd among those groups
#   w74 winner of match 74 · l101 loser of match 101
KO_BRACKET = [
    (73,"R32","R:A","R:B"), (74,"R32","W:E","T:ABCDF"), (75,"R32","W:F","R:C"),
    (76,"R32","W:C","R:F"), (77,"R32","W:I","T:CDFGH"), (78,"R32","R:E","R:I"),
    (79,"R32","W:A","T:CEFHI"), (80,"R32","W:L","T:EHIJK"), (81,"R32","W:D","T:BEFIJ"),
    (82,"R32","W:G","T:AEHIJ"), (83,"R32","R:K","R:L"), (84,"R32","W:H","R:J"),
    (85,"R32","W:B","T:EFGIJ"), (86,"R32","W:J","R:H"), (87,"R32","W:K","T:DEIJL"),
    (88,"R32","R:D","R:G"),
    (89,"R16","w74","w77"), (90,"R16","w73","w75"), (91,"R16","w76","w78"), (92,"R16","w79","w80"),
    (93,"R16","w83","w84"), (94,"R16","w81","w82"), (95,"R16","w86","w88"), (96,"R16","w85","w87"),
    (97,"QF","w89","w90"), (98,"QF","w93","w94"), (99,"QF","w91","w92"), (100,"QF","w95","w96"),
    (101,"SF","w97","w98"), (102,"SF","w99","w100"),
    (103,"BRONZE","l101","l102"), (104,"FINAL","w101","w102"),
]
# top-to-bottom order per round so feeders line up visually
KO_ORDER = {"R32":[74,77,73,75,83,84,81,82,76,78,79,80,86,88,85,87],
            "R16":[89,90,93,94,91,92,95,96], "QF":[97,98,99,100],
            "SF":[101,102], "FINAL":[104], "BRONZE":[103]}
KO_ROUND_META = [("R32","Round of 32","Jun 28 – Jul 3"), ("R16","Round of 16","Jul 4 – 7"),
                 ("QF","Quarter-finals","Jul 9 – 11"), ("SF","Semi-finals","Jul 14 – 15"),
                 ("FINAL","Final","Jul 19"), ("BRONZE","Third place","Jul 18")]

# ---- Known final results (as of June 14, 2026). ----
KNOWN_RESULTS = {            # match num : (home_score, away_score)
    1:  (2,0),   # Mexico 2-0 South Africa
    2:  (2,1),   # South Korea 2-1 Czechia
    3:  (1,1),   # Canada 1-1 Bosnia and Herzegovina
    4:  (4,1),   # United States 4-1 Paraguay
    5:  (0,1),   # Haiti 0-1 Scotland
    7:  (1,1),   # Brazil 1-1 Morocco
    8:  (1,1),   # Qatar 1-1 Switzerland
    6:  (2,0),   # Australia 2-0 Turkiye
    10: (7,1),   # Germany 7-1 Curacao
    11: (2,2),   # Netherlands 2-2 Japan
    9:  (1,0),   # Ivory Coast 1-0 Ecuador
    # Not yet final (Jun 14 evening): 12 Sweden-Tunisia
}

# Penalty-shootout outcomes (knockouts only). num : winning team.
# Winner scores a "win" (3); loser gets the consolation point (1).
PK_WINNERS = {}              # e.g. 75: "Brazil"

FLAGS = {
 "Argentina":"🇦🇷","England":"🏴","France":"🇫🇷","Spain":"🇪🇸","Brazil":"🇧🇷","Germany":"🇩🇪",
 "Netherlands":"🇳🇱","Portugal":"🇵🇹","Belgium":"🇧🇪","Colombia":"🇨🇴","Morocco":"🇲🇦","Norway":"🇳🇴",
 "Mexico":"🇲🇽","United States":"🇺🇸","Uruguay":"🇺🇾","Japan":"🇯🇵","Croatia":"🇭🇷","Switzerland":"🇨🇭",
 "Ecuador":"🇪🇨","Turkiye":"🇹🇷","Senegal":"🇸🇳","Austria":"🇦🇹","Paraguay":"🇵🇾","Sweden":"🇸🇪",
 "Canada":"🇨🇦","Ivory Coast":"🇨🇮","Czechia":"🇨🇿","Scotland":"🏴","Egypt":"🇪🇬","Ghana":"🇬🇭",
 "Algeria":"🇩🇿","Bosnia and Herzegovina":"🇧🇦","South Korea":"🇰🇷","Australia":"🇦🇺","Tunisia":"🇹🇳",
 "Iran":"🇮🇷","Congo DR":"🇨🇩","Panama":"🇵🇦","South Africa":"🇿🇦","Saudi Arabia":"🇸🇦",
 "New Zealand":"🇳🇿","Iraq":"🇮🇶","Qatar":"🇶🇦","Uzbekistan":"🇺🇿","Cape Verde":"🇨🇻","Haiti":"🇭🇹",
 "Jordan":"🇯🇴","Curacao":"🇨🇼",
}

def load_overrides():
    """Merge live results from data/results.json over the hardcoded seed.
    results.json (written by scripts/update_results.py) wins when present."""
    results = dict(KNOWN_RESULTS); pk = dict(PK_WINNERS); knockout = []
    p = os.path.join(DATA, "results.json")
    if os.path.exists(p):
        try:
            d = json.load(open(p, encoding="utf-8"))
            for k, v in (d.get("results") or {}).items():
                results[int(k)] = tuple(v)
            for k, v in (d.get("pk") or {}).items():
                pk[int(k)] = v
            knockout = d.get("knockout") or []
            print(f"  merged {len(d.get('results') or {})} group + {len(knockout)} knockout results"
                  + (f" (updated {d.get('updated')})" if d.get('updated') else ""))
        except Exception as e:
            print("  ! results.json unreadable, using seed:", e)
    return results, pk, knockout

ROUND_DATE = {m[0]: m[2] for m in KO_ROUND_META}

def build_matches(results, pk, knockout):
    matches = []
    for (num,grp,md,date,venue,home,away) in GROUP_SCHEDULE:
        m = {"id":f"m{num}","num":num,"grp":grp,"md":md,"date":date,"venue":venue,
             "home":home,"away":away,"status":"scheduled","hs":None,"as":None,
             "pk":False,"pkWinner":None}
        if num in results:
            m["hs"],m["as"] = results[num]; m["status"]="final"
        if num in pk:
            m["pk"]=True; m["pkWinner"]=pk[num]
        matches.append(m)
    # knockout matches from the live feed (teams known once drawn)
    for i, k in enumerate(knockout):
        rnd = k.get("round","R32")
        ha = "".join(c for c in "_".join(sorted([str(k.get("home")), str(k.get("away"))]))
                     if c.isalnum() or c=="_")
        matches.append({
            "id": f"k_{rnd}_{ha}", "num": 900+i, "grp": None, "round": rnd, "md": None,
            "date": k.get("date") or ROUND_DATE.get(rnd,""), "venue": k.get("venue",""),
            "home": k.get("home"), "away": k.get("away"),
            "hs": k.get("hs"), "as": k.get("as"),
            "status": k.get("status","scheduled"),
            "pk": bool(k.get("pkWinner")), "pkWinner": k.get("pkWinner"),
        })
    return matches

def validate():
    teams = [t for ts in OWNERS.values() for t in ts]
    all_wc = [t for ts in REAL_GROUPS.values() for t in ts]
    assert len(teams)==48, f"expected 48 drafted teams, got {len(teams)}"
    assert len(set(teams))==48, "duplicate team in draft!"
    missing = set(all_wc)-set(teams); extra = set(teams)-set(all_wc)
    assert not missing, f"undrafted teams: {missing}"
    assert not extra, f"unknown teams in draft: {extra}"

def main():
    validate()
    results, pk, knockout = load_overrides()
    matches = build_matches(results, pk, knockout)
    draft = build_draft()
    team_owner = {t:o for o,ts in OWNERS.items() for t in ts}
    team_pick = {p["team"]:p["pick"] for p in draft}
    team_round = {p["team"]:p["round"] for p in draft}
    payload = {
        "sheet": SHEET, "me": ME, "scoring": SCORING,
        "owners": OWNERS, "teamOwner": team_owner,
        "draft": draft, "draftOrder": DRAFT_ORDER, "rounds": ROUNDS,
        "teamPick": team_pick, "teamRound": team_round,
        "realGroups": REAL_GROUPS, "matches": matches,
        "koSchedule": [{"round":r,"dates":d} for (r,d) in KO_SCHEDULE],
        "koBracket": [{"num":n,"round":r,"a":a,"b":b} for (n,r,a,b) in KO_BRACKET],
        "koOrder": KO_ORDER,
        "koRounds": [{"key":k,"name":nm,"dates":d} for (k,nm,d) in KO_ROUND_META],
        "flags": FLAGS,
        "thirdsAdvanced": [], "eliminated": [],
        "builtAt": datetime.date.today().isoformat(),
    }
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA,"draft.json"),"w") as f:
        json.dump({"me":ME,"scoring":SCORING,"draftOrder":DRAFT_ORDER,
                   "owners":OWNERS,"draft":draft},f,indent=2,ensure_ascii=False)
    with open(os.path.join(DATA,"worldcup.json"),"w") as f:
        json.dump({"realGroups":REAL_GROUPS,"matches":matches,"flags":FLAGS},f,indent=2,ensure_ascii=False)
    with open(os.path.join(HERE,"template.html"),encoding="utf-8") as f:
        tpl = f.read()
    html = tpl.replace("__DATA__", json.dumps(payload,ensure_ascii=False))
    with open(os.path.join(ROOT,"index.html"),"w",encoding="utf-8") as f:
        f.write(html)
    finals = sum(1 for m in matches if m["status"]=="final")
    print(f"Built {os.path.join(ROOT,'index.html')}")
    print(f"  owners: {len(OWNERS)}  teams: 48  matches: {len(matches)}  finals: {finals}")

if __name__ == "__main__":
    main()
