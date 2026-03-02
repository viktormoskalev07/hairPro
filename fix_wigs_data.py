"""Fix wigs_data.json: re-classify all wigs to new professional category IDs."""
import json, os
from collections import Counter

DATA_FILE = "components/wigs_data.json"

# Same category IDs as in categorize_and_expand.py
KEYWORDS = {
    "women-classic":      ["bob","lob","straight","classic","blunt","fringe","sleek","sassoon","french bob","italian bob","side part","french crop"],
    "women-long":         ["long","wavy","cascade","layers","flowing","balayage","ombre","silk","mermaid","curtain bangs","balayage"],
    "women-curly":        ["curl","curly","ringlet","coil","frizz","bouncy","beach curl","romantic wave","deep wave"],
    "women-short":        ["pixie","short","mushroom","crop","bowl"],
    "women-updo":         ["bun","updo","braid","braided","knot","ponytail","chignon","fishtail","dutch crown","french twist","low chignon","braided crown"],
    "women-colored":      ["pink","blue","purple","teal","rainbow","pastel","rose gold","lavender","emerald","sapphire","sunset","cotton candy","neon shag","geometric pink","ocean blue","forest green","strawberry","peach","dusty lavender","ice blonde","burgundy"],
    "men-classic":        ["pompadour","quiff","side part","slick","executive","ivy league","hard part","crew cut","classic side","salt and pepper quiff"],
    "men-fade":           ["fade","taper","skin fade","high fade","mid fade","low fade","mohawk"],
    "men-textured":       ["wolf cut","shag","wavy surfer","messy"],
    "men-long":           ["man bun","man-bun","ponytail","viking","norse","half up","long flowing"],
    "unisex-natural":     ["afro","dread","loc","twist out","freeform","coily natural","natural black","classic afro","midnight dread"],
    "unisex-alternative": ["neon buzz","geometric color","liberty spikes","navy blue mohawk","neon shag"],
}

HEURISTICS_WOMEN = ["blonde","wave","highlights","chestnut","copper","auburn","honey","caramel","tousled","classic updo","jet black curtain","auburn shag","blunt fringe","cinnamon","platinum lob","sleek high"]
HEURISTICS_MEN_FADE = ["undercut","crew","slick back","comb over"]
HEURISTICS_UNISEX_NAT = ["dreadlock","afro","coil"]

def classify(name: str) -> str:
    nl = name.lower()
    for cat_id, kws in KEYWORDS.items():
        for kw in kws:
            if kw in nl:
                return cat_id
    # heuristics
    if any(w in nl for w in ["long","lob","bob","curl","wave","braid","updo","bun","pixie","ombre","balayage","layer","straight"]):
        return "women-classic"
    if any(w in nl for w in HEURISTICS_WOMEN):
        return "women-classic"
    if any(w in nl for w in HEURISTICS_MEN_FADE):
        return "men-fade"
    if any(w in nl for w in HEURISTICS_UNISEX_NAT):
        return "unisex-natural"
    return "women-classic"

with open(DATA_FILE, encoding="utf-8") as f:
    wigs = json.load(f)

valid_ids = set(KEYWORDS.keys())
result = []
for w in wigs:
    # Check image exists
    path = "public" + w["src"]
    if not os.path.exists(path):
        print(f"MISSING (skip): {w['src']}")
        continue

    # Re-classify if not a proper new category ID
    old_cat = w.get("category", "")
    if old_cat not in valid_ids:
        new_cat = classify(w["name"])
        print(f"RECLASSIFY: {w['name'][:40]:40s}  {old_cat!r:25s}  ->  {new_cat!r}")
        w["category"] = new_cat

    # Drop audit field (not needed in frontend)
    w.pop("audit", None)
    result.append(w)

print(f"\nKept {len(result)} wigs total\n")

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("wigs_data.json saved.\n")
print("Category breakdown:")
for cat, n in sorted(Counter(w["category"] for w in result).items()):
    print(f"  {cat:30s}  {n:3d}")
