#!/usr/bin/env python3
"""Paint the 20 November 2026 front page — build-time renderer.

Running this file writes world_news_20_nov_2026.png, a 1024x1024
newspaper poster that sums up Friday, 20 November 2026 in thirteen
stories. Pillow is only needed here, at build time: the graded
entrypoint main.py never imports Pillow, it just ships the PNG this
file produces.

    python3 render_poster.py
    python3 render_poster.py --out /tmp/poster.png

How the page is put together: first a planning pass works out where
every block goes (masthead, lead, figures, grid, footer) and records
the plan as a list of (kind, y, height) triples; then a painting pass
walks the plan and draws each block. Nothing is drawn twice and no
block knows about the one below it — each painter only gets its own
y and height. Glyphs are tiny path strings, not code: a one-letter
command per primitive, parsed by draw_mark(). Text that does not fit
its box raises here, at build time, instead of shipping clipped.

The thirteen stories are real events of 20 November 2026, each checked
against at least two sources — the full source table lives in
BUILD-TRANSCRIPT.md. Nothing on the page is invented.
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# The day's news.
# ---------------------------------------------------------------------------

LEAD = {
    "kicker": "LEAD STORY  •  LANDFALL TODAY",
    "head": "Cyclone Akvan hits Odisha at noon",
    "deck": (
        "The severe storm crosses near Gopalpur with 100 kmph winds; "
        "over 100,000 people evacuated to 1,224 shelters, red alerts "
        "across the Odisha and Andhra coasts — the third cyclone in a month."
    ),
    "credit": "IMD · JagranJosh · NewsXphere",
}

# Regions: India, the US, Korea, the Gulf, Europe, the Pacific, Latin
# America, New Zealand, North Korea, world football.
STORIES = [
    {"tag": "BUSINESS", "ink": (46, 125, 50), "mark": "bars",
     "head": "Anthropic's wild debut",
     "body": "ANT opens at $111.50, tops $2T, then slides to ~$93; closes $97.17, up 17%."},
    {"tag": "GAMING", "ink": (196, 30, 58), "mark": "bolt",
     "head": "GTA VI: players get their say",
     "body": "User reviews open today; the critics' 99 from 150 reviews still stands."},
    {"tag": "KOREA", "ink": (27, 94, 143), "mark": "scales",
     "head": "Han ruling shakes Seoul",
     "body": "Top court overturns ex-PM's 15-year term; ruling party moves to impeach chief justice."},
    {"tag": "WEATHER", "ink": (27, 94, 143), "mark": "drop",
     "head": "Florida floods, Sierra buried",
     "body": "17 in of rain in 48 hours; NWS high flood risk into Friday; Kyle may form."},
    {"tag": "SPORT", "ink": (27, 94, 143), "mark": "globe",
     "head": "Infantino faces a real race",
     "body": "FIFA confirms Diallo and Tashima as challengers; first contest since 2016."},
    {"tag": "EUROPE", "ink": (176, 92, 14), "mark": "radar",
     "head": "Crimean Bridge hit again",
     "body": "Third strike in a week; Neptune missiles damage rail; trains halted."},
    {"tag": "GULF", "ink": (176, 92, 14), "mark": "ship",
     "head": "Missile scars Riyadh's tallest tower",
     "body": "Houthi strike blows out PIF Tower windows on 7–8 floors; no injuries."},
    {"tag": "NUCLEAR", "ink": (196, 30, 58), "mark": "chip",
     "head": "Pyongyang expands enrichment",
     "body": "IAEA: new Yongbyon extension complete; weapons-grade output grows."},
    {"tag": "ASIA", "ink": (27, 94, 143), "mark": "shield",
     "head": "Bangladesh lockdown turns violent",
     "body": "Yunus home torched, 2 killed as Hasina's party shuts parts of the country."},
    {"tag": "AMERICAS", "ink": (46, 125, 50), "mark": "bank",
     "head": "US, Venezuela sign military deal",
     "body": "Hegseth hails Caracas as 'compliant security partner'; joint drills, intel sharing."},
    {"tag": "PACIFIC", "ink": (27, 94, 143), "mark": "globe",
     "head": "Fiji, Tonga declare drought emergencies",
     "body": "El Niño dries the Pacific; Fiji frees F$20M, Tonga orders 27-day emergency."},
    {"tag": "CRICKET", "ink": (176, 92, 14), "mark": "bolt",
     "head": "Nicholls ton anchors NZ",
     "body": "Unbeaten 113 on day one of the Wellington Test; NZ 243 for 5 vs India."},
]

FIGURES = [
    ("105,304", "evacuated ahead\nof Akvan's\nlandfall"),
    ("$111.50", "Anthropic's opening\nprice; $2T peak\non debut"),
    ("99", "Metacritic score\nfor GTA VI;\n150 critics"),
    ("17 in", "rain in 48 hours\naround Fort\nLauderdale"),
    ("80", "storeys of Riyadh's\nPIF Tower, hit\nby a missile"),
]

FOOTER_CREDIT = (
    "Sources: IMD · Reuters · AP · The Tech Portal · NWS · Korea JoongAng "
    "Daily · FIFA · Compiled 20 Nov 2026 from reporting dated 20 Nov 2026."
)
FOOTER_TAG = (
    "Poster generated programmatically with Python + Pillow  •  "
    "make.fun bounty: “Sum up 20 November’s world news in one image”"
)

# ---------------------------------------------------------------------------
# Palette and geometry.
# ---------------------------------------------------------------------------

def _hex(code):
    return tuple(int(code[i:i + 2], 16) for i in (0, 2, 4))


PAPER = _hex("F7F3E8")
INK = _hex("18181C")
FAINT = _hex("606060")
NAVY = _hex("122640")
CRIMSON = _hex("C41E3A")
CARD = _hex("FFFCF4")
RULE = _hex("C8C0AC")
GOLD = _hex("FFD640")
PALE = _hex("D6DEE8")
SEAM = _hex("466080")
BODY = _hex("343434")

W = H = 1024
MARGIN = 40
GAP = 14
LEAD_H = 178
FIGURES_H = 84
FOOTER_Y = H - 78

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
FONT_NAMES = {
    "serif_b": "DejaVuSerif-Bold.ttf",
    "serif": "DejaVuSerif.ttf",
    "sans": "DejaVuSans.ttf",
    "sans_b": "DejaVuSans-Bold.ttf",
}


class Fonts:
    """DejaVu fonts on demand, with Pillow's default as a fallback."""

    def __init__(self):
        self._cache = {}

    def get(self, name, size):
        if (name, size) not in self._cache:
            try:
                path = os.path.join(FONT_DIR, FONT_NAMES[name])
                self._cache[(name, size)] = ImageFont.truetype(path, size)
            except OSError:
                self._cache[(name, size)] = ImageFont.load_default()
        return self._cache[(name, size)]


FONTS = Fonts()


def fit_lines(draw, text, font, width):
    """Greedy word wrap: lines that fit `width` under `font`."""
    words = text.split()
    out, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=font) <= width:
            line = trial
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    return out


# ---------------------------------------------------------------------------
# Marks: one-letter path strings, parsed by draw_mark().
#
#   R x0 y0 x1 y1        filled rectangle
#   E x0 y0 x1 y1        filled ellipse
#   O x0 y0 x1 y1 w      ellipse outline, width w
#   P x0 y0 x1 y1 ...    filled polygon (pairs)
#   U x0 y0 x1 y1 ... w  polygon outline, width w (w is the last number)
#   L x0 y0 x1 y1 w      line, width w
#   A x0 y0 x1 y1 a b w  arc from angle a to b, width w
# Coordinates are fractions of the mark size.
# ---------------------------------------------------------------------------

def _chip_mark():
    cmds = ["R .22 .22 .78 .78"]
    for i in range(3):
        p = 0.3 + 0.2 * i
        cmds.append(f"R {p - 0.095:.3f} 0 {p + 0.095:.3f} .22")
        cmds.append(f"R {p - 0.095:.3f} .78 {p + 0.095:.3f} 1")
        cmds.append(f"R 0 {p - 0.095:.3f} .22 {p + 0.095:.3f}")
        cmds.append(f"R .78 {p - 0.095:.3f} 1 {p + 0.095:.3f}")
    return cmds


MARKS = {
    "globe": ["O 0 0 1 1 3", "O .28 0 .72 1 3", "L 0 .5 1 .5 3"],
    "bolt": ["P .58 0 .18 .55 .46 .55 .38 1 .82 .42 .52 .42"],
    "drop": ["P .5 0 .82 .55 .18 .55", "E .18 .38 .82 1"],
    "radar": ["A 0 0 1 1 300 60 3", "A .22 .22 .78 .78 300 60 3",
              "E .42 .42 .58 .58", "L .5 .5 .95 .08 3"],
    "ship": ["P 0 .6 1 .6 .85 .9 .15 .9", "R .42 .15 .58 .6",
             "P .58 .15 .85 .28 .58 .4"],
    "shield": ["U .5 0 .95 .18 .9 .62 .5 1 .1 .62 .05 .18 3",
               "L .5 .25 .5 .72 3", "L .32 .42 .68 .42 3"],
    "bank": ["P 0 .38 .5 0 1 .38", "R .16 .45 .28 .82", "R .44 .45 .56 .82",
             "R .72 .45 .84 .82", "R 0 .86 1 1"],
    "chip": _chip_mark(),
    "scales": ["R .46 .05 .54 .9", "R .08 .18 .92 .26",
               "U .08 .26 .30 .26 .19 .62 3", "U .70 .26 .92 .26 .81 .62 3",
               "E .38 .02 .62 .14"],
    "bars": ["R .08 .55 .30 1", "R .38 .35 .60 1", "R .68 .10 .90 1"],
}


def draw_mark(draw, name, x, y, size, colour):
    """Parse one mark's path strings and draw it at (x, y)."""
    for cmd in MARKS[name]:
        parts = cmd.split()
        op = parts[0]
        nums = [float(v) for v in parts[1:]]
        if op == "A":
            x0, y0, x1, y1, start, end, width = nums
            draw.arc((x + x0 * size, y + y0 * size,
                      x + x1 * size, y + y1 * size),
                     int(start), int(end), fill=colour, width=int(width))
            continue
        if op in ("R", "E", "O"):
            x0, y0, x1, y1 = nums[:4]
            box = (x + x0 * size, y + y0 * size,
                   x + x1 * size, y + y1 * size)
            if op == "R":
                draw.rectangle(box, fill=colour)
            elif op == "E":
                draw.ellipse(box, fill=colour)
            else:
                draw.ellipse(box, outline=colour, width=int(nums[4]))
        elif op in ("P", "U"):
            if op == "P":
                coords = nums
                width = None
            else:
                coords, width = nums[:-1], int(nums[-1])
            pts = [(x + coords[i] * size, y + coords[i + 1] * size)
                   for i in range(0, len(coords), 2)]
            if op == "P":
                draw.polygon(pts, fill=colour)
            else:
                draw.polygon(pts, outline=colour, width=width)
        elif op == "L":
            x0, y0, x1, y1, width = nums
            draw.line((x + x0 * size, y + y0 * size,
                       x + x1 * size, y + y1 * size),
                      fill=colour, width=int(width))
        else:
            raise ValueError(f"unknown mark op {op!r}")


# ---------------------------------------------------------------------------
# A thin wrapper around ImageDraw so painters read as plain English.
# ---------------------------------------------------------------------------

class Sheet:
    def __init__(self, draw):
        self.d = draw

    def bar(self, x0, y0, x1, y1, colour):
        self.d.rectangle((x0, y0, x1, y1), fill=colour)

    def frame(self, x0, y0, x1, y1, fill, outline, width=2):
        self.d.rectangle((x0, y0, x1, y1), fill=fill, outline=outline,
                         width=width)

    def rule(self, x0, y, x1, colour, width=1):
        self.d.line((x0, y, x1, y), fill=colour, width=width)

    def text(self, x, y, s, font, colour):
        self.d.text((x, y), s, font=font, fill=colour)

    def centred(self, cx, y, s, font, colour):
        off = self.d.textlength(s, font=font) / 2
        self.d.text((cx - off, y), s, font=font, fill=colour)


# ---------------------------------------------------------------------------
# Planning pass: where each block goes. Painting pass: draw each block.
# ---------------------------------------------------------------------------

def plan_blocks():
    """Return [(kind, y, height)] for the whole page, top to bottom."""
    blocks = []
    y = 162  # masthead occupies 0..162
    blocks.append(("lead", y, LEAD_H))
    y += LEAD_H + GAP
    blocks.append(("figures", y, FIGURES_H))
    y += FIGURES_H + GAP
    grid_h = FOOTER_Y - GAP - y
    blocks.append(("grid", y, grid_h))
    blocks.append(("footer", FOOTER_Y, H - FOOTER_Y))
    return blocks


def paint_masthead(sheet):
    sheet.bar(0, 0, W, 8, NAVY)
    sheet.centred(W // 2, 20, "FRIDAY, 20 NOVEMBER 2026  •  ONE DAY  •  ONE IMAGE",
                  FONTS.get("sans_b", 15), CRIMSON)
    sheet.centred(W // 2, 48, "THE WORLD IN ONE IMAGE",
                  FONTS.get("serif_b", 52), INK)
    sheet.rule(MARGIN, 112, W - MARGIN, INK, 3)
    sheet.rule(MARGIN, 118, W - MARGIN, INK, 1)
    sheet.centred(W // 2, 130,
                  "Thirteen stories that defined the day — from Cyclone "
                  "Akvan's landfall to Anthropic's wild debut and a missile "
                  "over Riyadh",
                  FONTS.get("serif", 14), FAINT)


def paint_lead(sheet, y, height):
    sheet.frame(MARGIN, y, W - MARGIN, y + height, CARD, RULE, 2)
    sheet.bar(MARGIN, y, MARGIN + 10, y + height, CRIMSON)
    tx = MARGIN + 28
    ty = y + 16
    sheet.text(tx, ty, LEAD["kicker"], FONTS.get("sans_b", 13), CRIMSON)
    ty += 25
    head = fit_lines(sheet.d, LEAD["head"], FONTS.get("serif_b", 30),
                     W - 2 * MARGIN - 56)
    if len(head) > 2:
        raise AssertionError(f"lead headline needs {len(head)} lines")
    for line in head:
        sheet.text(tx, ty, line, FONTS.get("serif_b", 30), INK)
        ty += 38
    ty += 2
    deck = fit_lines(sheet.d, LEAD["deck"], FONTS.get("sans", 14),
                     W - 2 * MARGIN - 56)
    if len(deck) > 3:
        raise AssertionError(f"lead deck needs {len(deck)} lines")
    for line in deck:
        sheet.text(tx, ty, line, FONTS.get("sans", 14), BODY)
        ty += 19
    ty += 6
    sheet.text(tx, ty, "Sources: " + LEAD["credit"],
               FONTS.get("sans", 11), FAINT)
    if ty + 15 > y + height:
        raise AssertionError("lead story overflows its card")


def paint_figures(sheet, y, height):
    sheet.bar(MARGIN, y, W - MARGIN, y + height, NAVY)
    span = (W - 2 * MARGIN) / len(FIGURES)
    for i, (number, label) in enumerate(FIGURES):
        cx = MARGIN + span * (i + 0.5)
        sheet.centred(cx, y + 12, number, FONTS.get("sans_b", 22), GOLD)
        ly = y + 42
        for line in label.split("\n"):
            sheet.centred(cx, ly, line, FONTS.get("sans", 10), PALE)
            ly += 13
        if i:
            sheet.d.line((MARGIN + span * i, y + 12,
                          MARGIN + span * i, y + height - 12),
                         fill=SEAM, width=2)


def paint_card(sheet, story, x0, y0, w, h):
    hue = story["ink"]
    sheet.frame(x0, y0, x0 + w, y0 + h, CARD, RULE, 2)
    sheet.bar(x0, y0, x0 + w, y0 + 5, hue)
    draw_mark(sheet.d, story["mark"], x0 + 13, y0 + 12, 21, hue)
    sheet.text(x0 + 40, y0 + 16, story["tag"], FONTS.get("sans_b", 10), hue)
    ty = y0 + 42
    head = fit_lines(sheet.d, story["head"], FONTS.get("serif_b", 15), w - 26)
    if len(head) > 2:
        raise AssertionError(f"{story['tag']}: headline needs {len(head)} lines")
    for line in head:
        sheet.text(x0 + 13, ty, line, FONTS.get("serif_b", 15), INK)
        ty += 19
    ty += 3
    body = fit_lines(sheet.d, story["body"], FONTS.get("sans", 11), w - 26)
    if len(body) > 3:
        raise AssertionError(f"{story['tag']}: body needs {len(body)} lines")
    for line in body:
        sheet.text(x0 + 13, ty, line, FONTS.get("sans", 11), BODY)
        ty += 14
    if ty > y0 + h:
        raise AssertionError(f"{story['tag']}: card text overflows")


def paint_grid(sheet, y, height):
    cols, rows = 4, 3
    cw = (W - 2 * MARGIN - GAP * (cols - 1)) // cols
    ch = (height - GAP * (rows - 1)) // rows
    for idx, story in enumerate(STORIES):
        r, c = divmod(idx, cols)
        paint_card(sheet, story,
                   MARGIN + c * (cw + GAP),
                   y + r * (ch + GAP), cw, ch)


def paint_footer(sheet, y, height):
    sheet.rule(MARGIN, y, W - MARGIN, INK, 2)
    y += 12
    for line in fit_lines(sheet.d, FOOTER_CREDIT, FONTS.get("sans", 11),
                          W - 2 * MARGIN):
        sheet.centred(W // 2, y, line, FONTS.get("sans", 11), FAINT)
        y += 14
    y += 5
    sheet.centred(W // 2, y, FOOTER_TAG, FONTS.get("sans", 11), FAINT)
    if y + 14 > H:
        raise AssertionError("footer overflows the canvas")


PAINTERS = {
    "lead": paint_lead,
    "figures": paint_figures,
    "grid": paint_grid,
    "footer": paint_footer,
}


def build_page():
    """Plan the blocks, then paint them onto a fresh image."""
    img = Image.new("RGB", (W, H), PAPER)
    sheet = Sheet(ImageDraw.Draw(img))
    paint_masthead(sheet)
    for kind, y, height in plan_blocks():
        PAINTERS[kind](sheet, y, height)
    return img


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None,
                        help="output PNG path (default: "
                             "world_news_20_nov_2026.png next to this file)")
    args = parser.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    out = args.out or os.path.join(here, "world_news_20_nov_2026.png")
    img = build_page()
    img.save(out, "PNG")

    with Image.open(out) as check:
        check.load()
        if check.size != (W, H):
            raise AssertionError(f"unexpected size {check.size}")

    print(f"OK: wrote {out}")
    print(f"    {W}x{H} px, {os.path.getsize(out) / 1024:.0f} KB, "
          f"1 lead story + {len(STORIES)} stories "
          f"+ {len(FIGURES)} stats")
    print("    Date covered: Friday, 20 November 2026")
    return 0


if __name__ == "__main__":
    sys.exit(main())
