#!/usr/bin/env python3
"""
Rebuild project.json from newest.json:
 - Every non-intro panel's STEP N badge becomes pinkbox (via tpl override).
 - Each non-intro panel gets a user-added narrator bubble with verbose
   content pulled from the Roommate Etiquette slideshow.
"""

import json
from datetime import datetime, timezone

SRC = "/Users/akashn/opencraw/newest.json"
DST = "/Users/akashn/opencraw/project.json"

with open(SRC) as f:
    project = json.load(f)

# ── 1. Pink STEP badges via tpl overrides ─────────────────────────────
# Map: tpl id → step label
STEP_BADGES = {
    "tpl-5":  "STEP 1",   # p1
    "tpl-11": "STEP 2",   # p2
    "tpl-17": "STEP 3",   # p3
    "tpl-22": "STEP 4",   # p4
    "tpl-27": "STEP 5",   # p5
    "tpl-32": "STEP 6",   # p6
    "tpl-38": "STEP 7",   # p7  (was "STEP 7 · new customs")
    "tpl-41": "STEP 8",   # p8  (was "STEP 8 · *SHARED*")
    "tpl-45": "STEP 9",   # p9  (was "*STILL STUCK?*")
}
# tpl-38, tpl-41, tpl-45 originally held longer combined labels
# ("STEP 7 · new customs", "STEP 8 · *SHARED*", "*STILL STUCK?*"),
# so their rx is oversize. Shrink them to standard STEP-badge width.
STEP_BADGE_WIDTHS = {"tpl-38": 28, "tpl-41": 28, "tpl-45": 28}
bo = project.setdefault("bo", {})
for tpl_id, label in STEP_BADGES.items():
    existing = bo.get(tpl_id, {})
    existing.pop("deleted", None)             # un-delete if user removed it
    existing["text"] = label
    existing["type"] = "pinkbox"
    if tpl_id in STEP_BADGE_WIDTHS:
        existing["rx"] = STEP_BADGE_WIDTHS[tpl_id]
        existing["ry"] = 10
    bo[tpl_id] = existing

# ── 2. Verbose narrator user bubbles per non-intro panel ──────────────
# All-caps display: narrator style has upper=True in STYLES, so text is
# auto-uppercased at render time — write in normal case here.
SLIDES = {
    "p1": "Set clear guidelines from the start. Agree on schedules and day-to-day rules to avoid misunderstandings. Cover: cleanliness, guests (day + overnight — who's permitted, how to notify), and communication. You'll build a roommate/suitemate agreement with your Don at the beginning of the semester.",
    "p2": "Respect each other's personal space. Don't enter your roommate's space uninvited. Don't go through their belongings when they're not present. Keep your stuff on your side of the room. Exception: passing through their section to reach your half. Remember — shared space does not mean shared everything.",
    "p3": "Respect each other's belongings. Ask before you borrow — don't assume it's okay just because it's in a shared space. Return things how you found them (or better!). Speak up promptly if something gets damaged or misplaced.",
    "p4": "Clean up after yourself. If you make the mess, clean the mess — don't leave it for your roommate. Don't let small messes pile up: a 2-minute clean-up beats a weekend deep clean. Never leave trash or open food out. Build a cleaning schedule together and stick to it.",
    "p5": "Address concerns as they come. Bottling up annoyance leads to explosive arguments. Speak your mind as problems emerge and work together on solutions. Unsure how to bring something up? Ask your residence Don to help guide the conversation.",
    "p6": "Don't expect to be best friends. You might become close — great! But that expectation can create an uncomfortable dynamic. Be friendly, but know that their interests, schedules, and friends may not line up with yours.",
    "p7": "Be open to change. Living with someone you (potentially) just met at move-in is a new experience and will bring new customs. Keep an open mind about differences and change — go with the flow!",
    "p8": "Remember it's a shared space. This is your home for the next 8 months. Warn your roommate before bringing people over. Ask what their comfort level is with music and noise. Trash and open food affect them too — not just you.",
    "p9": "Concerns? Problems? 1) Talk with your roommate first — this should always be the first step. 2) Speak with your residence Don. 3) Reach out to the Office of Residence & Student Life. 4) Have (or revisit) your roommate/suitemate agreement meeting.",
}

# Placement per panel. narrator style renders a cream rectangular caption
# with a black border + drop shadow. Sized so ~40–60 words fit at readable
# size and positioned in the lower portion of each panel so it doesn't
# overlap the existing yellow-box header line.
#
#   x,y are top-left in stage coords (0-800 wide, 0-626 tall).
NARRATORS = {
    "p1": {"x": 445, "y":  95, "w": 350, "h":  60},   # top-right panel bottom band
    "p2": {"x":  10, "y": 275, "w": 360, "h":  65},   # row2-left
    "p3": {"x": 350, "y": 275, "w": 175, "h":  65},   # row2-mid (narrow!)
    "p4": {"x": 505, "y": 275, "w": 290, "h":  65},   # row2-right
    "p5": {"x":  10, "y": 420, "w": 395, "h":  44},   # row3-left (short row)
    "p6": {"x": 405, "y": 420, "w": 390, "h":  44},   # row3-right
    "p7": {"x":  10, "y": 570, "w": 275, "h":  50},   # row4-left
    "p8": {"x": 275, "y": 570, "w": 240, "h":  50},   # row4-mid
    "p9": {"x": 510, "y": 570, "w": 285, "h":  50},   # row4-right
}

# COLORS index: ['#fdf23f','#ffffff','#ff3b30','#4a90e2','#37c26a','#ff8fb8',
#                '#ff8c1a','#a259ff','#000000','#d9c9a3']
# FONTS index:  ['system-ui','Bangers','Bungee','Permanent Marker','Luckiest Guy',
#                'Titan One','Sigmar','Creepster','Rock Salt','Modak','Comic Neue']
NARRATOR_FILL_IDX = 9    # #d9c9a3 (cream/tan — matches narrator's default fill)
NARRATOR_FONT_IDX = 10   # Comic Neue

ub = []
for panel_id, text in SLIDES.items():
    box = NARRATORS[panel_id]
    ub.append({
        "type": "style",
        "styleKey": "narrator",
        "x": box["x"], "y": box["y"], "w": box["w"], "h": box["h"],
        "text": text,
        "fillIndex": NARRATOR_FILL_IDX,
        "fontIndex": NARRATOR_FONT_IDX,
        "fontScale": 0.7,     # shrink font so verbose content fits
        "noShape": False,
        "src": None,
    })

project["ub"] = ub
project["f"] = project.get("f", "Comic Neue")
project["savedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

with open(DST, "w") as f:
    json.dump(project, f)

print(f"wrote {DST}")
print(f"  {len(bo)} bubble overrides ({len(STEP_BADGES)} STEP badges pink)")
print(f"  {len(ub)} verbose narrator bubbles added")
