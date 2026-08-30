#!/usr/bin/env python3
"""
Build comic.json for /comic.html.
 - Preserves panel images + vertices + template positions from newest.json
 - Applies pink STEP N badges via tpl overrides
 - Adds MANY small caption user-bubbles per non-intro panel, chunking each
   slide into short phrases so every word from the slideshow appears.

Panel coordinate system: 0..800 wide, 0..626 tall (matches designs.html
VIEW_W/VIEW_H). Bubbles specify {x, y, w, h} in that space.
"""

import json
from datetime import datetime, timezone

SRC = "/Users/akashn/opencraw/newest.json"
DST = "/Users/akashn/opencraw/comic.json"

with open(SRC) as f:
    project = json.load(f)

# ── Pink STEP badges ───────────────────────────────────────────────────
STEP_BADGES = {
    "tpl-5":  "STEP 1", "tpl-11": "STEP 2", "tpl-17": "STEP 3",
    "tpl-22": "STEP 4", "tpl-27": "STEP 5", "tpl-32": "STEP 6",
    "tpl-38": "STEP 7", "tpl-41": "STEP 8", "tpl-45": "STEP 9",
}
STEP_BADGE_WIDTHS = {"tpl-38": 28, "tpl-41": 28, "tpl-45": 28}
bo = project.setdefault("bo", {})
for tpl_id, label in STEP_BADGES.items():
    existing = bo.get(tpl_id, {})
    existing.pop("deleted", None)
    existing["text"] = label
    existing["type"] = "pinkbox"
    if tpl_id in STEP_BADGE_WIDTHS:
        existing["rx"] = STEP_BADGE_WIDTHS[tpl_id]
        existing["ry"] = 10
    bo[tpl_id] = existing

# ── Caption bubble helper ──────────────────────────────────────────────
# Each caption is a `caption` style user bubble (yellow rectangle with a
# black border + hard drop shadow — the "Marvel narration box" look).
# CAPTION style natural size is 300×110; TEXT_MARGIN mx/my is 34/30 so a
# ~110×22 caption comfortably holds ~4–6 words at fontScale 0.55.

# Colors index (from FONTS/COLORS in designs.html):
#   0=#fdf23f yellow  1=white  2=red  3=blue  4=green
#   5=#ff8fb8 pink    6=orange 7=purple 8=black 9=#d9c9a3 cream
# Fonts index:
#   0=system-ui 1=Bangers 2=Bungee 3=Permanent Marker 4=Luckiest Guy
#   5=Titan One 6=Sigmar 7=Creepster 8=Rock Salt 9=Modak 10=Comic Neue

CAPTION_FILL = 0     # yellow — matches the existing yellowbox palette
CAPTION_FONT = 10    # Comic Neue

def cap(x, y, w, h, text, style="caption", fill=CAPTION_FILL, font=CAPTION_FONT, scale=0.6):
    return {
        "type": "style",
        "styleKey": style,
        "x": x, "y": y, "w": w, "h": h,
        "text": text,
        "fillIndex": fill,
        "fontIndex": font,
        "fontScale": scale,
        "noShape": False,
        "src": None,
    }

ub = []

# ── P1 · Step 1 — Establish Guidelines ─────────────────────────────────
# panel bounds: x=429..800, y=0..161. Existing template row occupies y≈14..92.
# Fill the lower band with slide bullets.
ub += [
    cap(438,  98, 165, 14, "Set clear guidelines of expectations early on.", scale=0.5),
    cap(608,  98, 190, 14, "Avoid misunderstandings & annoyed roommates.",   scale=0.5),
    cap(438, 115, 120, 14, "Cover: cleanliness.",                             scale=0.55),
    cap(563, 115, 110, 14, "Guests — day",                                    scale=0.55),
    cap(678, 115, 120, 14, "and overnight.",                                  scale=0.55),
    cap(438, 132, 165, 14, "Who is permitted to stay where?",                 scale=0.5),
    cap(608, 132, 190, 14, "How to notify your roommate?",                    scale=0.5),
    cap(438, 149, 100, 12, "Communication.",                                  scale=0.55),
    cap(543, 149, 255, 12, "Roommate/suitemate agreement made with your Don.", scale=0.42),
]

# ── P2 · Step 2 — Respect Personal Space ───────────────────────────────
# panel bounds: x=0..~377, y=161..344. Existing bubbles at y=195..262.
ub += [
    cap(  6, 272, 180, 14, "Do NOT enter your roommate's space",              scale=0.5),
    cap(190, 272, 180, 14, "without their permission.",                       scale=0.5),
    cap(  6, 289, 180, 14, "Would you want someone entering",                 scale=0.5),
    cap(190, 289, 180, 14, "your space when you're not there?",               scale=0.5),
    cap(  6, 306, 180, 14, "Don't go through their belongings",               scale=0.5),
    cap(190, 306, 180, 14, "or space when they aren't present.",              scale=0.5),
    cap(  6, 323, 180, 14, "Keep your things on your side.",                  scale=0.5),
    cap(190, 323, 180, 14, "Exception: passing through.",                     scale=0.5),
]

# ── P3 · Step 3 — Respect Belongings ───────────────────────────────────
# narrow panel: x=344..528, y=161..344. Existing bubbles at y=195..246.
ub += [
    cap(346, 258, 180, 14, "Ask before you borrow.",                          scale=0.5),
    cap(346, 275, 180, 14, "Don't assume it's OK just",                       scale=0.5),
    cap(346, 292, 180, 14, "because it's in a shared space.",                 scale=0.48),
    cap(346, 309, 180, 14, "Return things how you found them",                scale=0.46),
    cap(346, 326, 180, 14, "(or better!) Speak up if damaged.",               scale=0.46),
]

# ── P4 · Step 4 — Clean Up After Yourself ──────────────────────────────
# panel: x=496..800, y=161..344. Existing bubbles at y=195..246.
ub += [
    cap(500, 260, 296, 14, "If YOU make the mess, YOU clean the mess.",       scale=0.5),
    cap(500, 277, 296, 14, "Don't leave it for your roommate!",               scale=0.5),
    cap(500, 294, 296, 14, "A 2-minute cleanup beats a weekend deep clean.",  scale=0.44),
    cap(500, 311, 296, 14, "Never leave trash or open food lying around.",    scale=0.44),
    cap(500, 328, 296, 14, "Build a cleaning schedule — stick to it all year.", scale=0.42),
]

# ── P5 · Step 5 — Address Concerns ─────────────────────────────────────
# short panel: x=0..411, y=344..468. Existing bubbles at y=368..412.
ub += [
    cap( 10, 420, 200, 14, "Bottling up annoyance → explosive argument.",     scale=0.44),
    cap(212, 420, 195, 14, "Speak your mind as problems emerge.",             scale=0.5),
    cap( 10, 437, 200, 14, "Work together to find solutions.",                scale=0.5),
    cap(212, 437, 195, 14, "Unsure how to raise it?",                         scale=0.5),
    cap( 10, 454, 395, 12, "Talk to your residence Don — they can guide the conversation.", scale=0.43),
]

# ── P6 · Step 6 — Don't Expect Best Friends ────────────────────────────
# panel: x=397..800, y=344..468. Existing bubbles at y=368..412.
ub += [
    cap(405, 420, 200, 14, "You MIGHT end up best friends —",                 scale=0.5),
    cap(605, 420, 190, 14, "but don't EXPECT it.",                            scale=0.55),
    cap(405, 437, 390, 14, "The expectation creates an uncomfortable dynamic.", scale=0.44),
    cap(405, 454, 390, 12, "Be aware: interests, schedules, friends may not align.", scale=0.42),
]

# ── P7 · Step 7 — Be Open to Change ────────────────────────────────────
# panel: x=0..290, y=468..626. Existing bubbles at y=487..540.
ub += [
    cap(  8, 548, 280, 14, "Living with someone you (potentially)",            scale=0.48),
    cap(  8, 565, 280, 14, "just met at move-in is a new experience.",         scale=0.46),
    cap(  8, 582, 280, 14, "It will bring about new customs.",                 scale=0.5),
    cap(  8, 599, 280, 14, "Keep an open mind to differences and change.",     scale=0.44),
    cap(  8, 616, 280, 10, "Go with the flow!",                                scale=0.55),
]

# ── P8 · Step 8 — Remember Shared Space ────────────────────────────────
# panel: x=264..519, y=468..626. Existing bubbles at y=490..547.
ub += [
    cap(268, 555, 246, 14, "Your home for the next 8 MONTHS is a shared one.", scale=0.42),
    cap(268, 572, 246, 14, "Bringing people over? WARN your roommate.",       scale=0.44),
    cap(268, 589, 246, 14, "Before loud music — ask about their noise comfort.", scale=0.42),
    cap(268, 606, 246, 14, "Garbage & food out impacts them too, not just you.", scale=0.42),
]

# ── P9 · Step 9 — Concerns? Problems? ──────────────────────────────────
# panel: x=502..800, y=468..626. Existing bubbles at y=490..556.
ub += [
    cap(508, 570, 288, 14, "1) Talk with your roommate FIRST — always.",      scale=0.44),
    cap(508, 587, 288, 14, "2) Speak with your residence Don.",               scale=0.5),
    cap(508, 604, 288, 14, "3) Office of Residence & Student Life.",          scale=0.46),
    cap(508, 615, 288, 10, "4) Set (or revisit) a roommate agreement meeting.", scale=0.42),
]

project["ub"] = ub
project["f"] = project.get("f", "Comic Neue")
project["savedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

with open(DST, "w") as f:
    json.dump(project, f)

print(f"wrote {DST}")
print(f"  pink STEP badges: {len(STEP_BADGES)}")
print(f"  small caption bubbles added: {len(ub)}")
