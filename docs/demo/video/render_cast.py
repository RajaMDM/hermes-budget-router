"""Render an asciinema v2/v3 cast to PNG frames with exact, idle-compressed timing.

Outputs frames/NNNNN.png plus timeline.json: [{"t": start_seconds, "dur": seconds, "frame": path}] and
markers: the output time at which each '# N.' scene note first appears (for voiceover/caption sync).
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path
import pyte
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BG = (30, 30, 30); FG = (230, 230, 230)
NAMED = {"black": (0, 0, 0), "red": (205, 49, 49), "green": (13, 188, 121), "brown": (229, 229, 16),
         "yellow": (229, 229, 16), "blue": (36, 114, 200), "magenta": (188, 63, 188), "cyan": (17, 168, 205),
         "white": (229, 229, 229), "brightblack": (102, 102, 102), "brightred": (241, 76, 76),
         "brightgreen": (35, 209, 139), "brightyellow": (245, 245, 67), "brightblue": (59, 142, 234),
         "brightmagenta": (214, 112, 214), "brightcyan": (41, 184, 219), "brightwhite": (255, 255, 255)}

from fontTools.ttLib import TTFont
CMAP = set(TTFont(FONT).getBestCmap())
SUBST = {"\U0001f4ca": "\u25a4", "\U0001f4c8": "\u25b2", "\u23f1": "\u25f7", "\u23f2": "\u25f7", "\ufe0f": "", "\u30fd": " "}

def draw_braille(d, ch, x, y, cw, chh, fill):
    bits = ord(ch) - 0x2800
    dots = [(0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (0, 3, 0x40), (1, 3, 0x80)]
    r = max(1, cw // 6)
    for cx, cy, bit in dots:
        if bits & bit:
            px = x + cw * (0.3 + 0.4 * cx); py = y + chh * (0.15 + 0.22 * cy)
            d.ellipse([px - r, py - r, px + r, py + r], fill=fill)

def colour(c, default):
    if c in (None, "default"): return default
    if c in NAMED: return NAMED[c]
    if isinstance(c, str) and re.fullmatch(r"[0-9a-fA-F]{6}", c): return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
    return default

EXTRA_MARKERS = {"footer_s3": r"(?m)^\s*\u2014 Model: claude-opus"}


def load(cast: Path):
    lines = cast.read_text().splitlines()
    head = json.loads(lines[0]); v = head.get("version", 2)
    cols = head.get("term", {}).get("cols") or head.get("width"); rows = head.get("term", {}).get("rows") or head.get("height")
    evs, t = [], 0.0
    for l in lines[1:]:
        try: e = json.loads(l)
        except json.JSONDecodeError: continue
        if not isinstance(e, list) or len(e) < 3: continue
        t = t + e[0] if v >= 3 else e[0]
        if e[1] == "o": evs.append((t, e[2]))
    return cols, rows, evs

def render(cast: Path, out: Path, font_size: int = 15, idle: float = 1.2, hold_end: float = 3.0,
           crop_rows: int | None = None):
    cols, rows, evs = load(cast)
    screen = pyte.Screen(cols, rows); stream = pyte.ByteStream(screen)
    f = ImageFont.truetype(FONT, font_size); fb = ImageFont.truetype(FONT_B, font_size)
    cw = round(f.getlength("M")); ch = round(font_size * 1.32)
    W, H = cols * cw, (crop_rows or rows) * ch
    (out / "frames").mkdir(parents=True, exist_ok=True)
    timeline, markers = [], {}
    clock, last_t, n = 0.0, None, 0
    def draw() -> Image.Image:
        img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
        for y in range(crop_rows or rows):
            line = screen.buffer[y]; x = 0
            while x < cols:
                c = line[x]; style = (c.fg, c.bg, c.bold, c.reverse); run = c.data; x2 = x + 1
                while x2 < cols and (line[x2].fg, line[x2].bg, line[x2].bold, line[x2].reverse) == style:
                    run += line[x2].data; x2 += 1
                fg = colour(c.fg, FG); bg = colour(c.bg, BG)
                if c.bold and c.fg in NAMED and "bright" + c.fg in NAMED: fg = NAMED["bright" + c.fg]
                if c.reverse: fg, bg = bg, fg
                if bg != BG: d.rectangle([x * cw, y * ch, x2 * cw, (y + 1) * ch], fill=bg)
                if run.strip():
                    font = fb if c.bold else f
                    if all(ord(k) < 128 or ord(k) in CMAP for k in run):
                        d.text((x * cw, y * ch + 2), run, font=font, fill=fg)
                    else:
                        for k_i, k in enumerate(run):
                            px = (x + k_i) * cw
                            if 0x2800 <= ord(k) <= 0x28FF:
                                draw_braille(d, k, px, y * ch, cw, ch, fg)
                            elif ord(k) < 128 or ord(k) in CMAP:
                                d.text((px, y * ch + 2), k, font=font, fill=fg)
                            else:
                                d.text((px, y * ch + 2), SUBST.get(k, " "), font=font, fill=fg)
                x = x2
        cx, cy = screen.cursor.x, screen.cursor.y
        if not screen.cursor.hidden and cy < (crop_rows or rows):
            d.rectangle([cx * cw, cy * ch + 2, cx * cw + cw - 1, (cy + 1) * ch - 1], fill=(220, 220, 220))
        return img
    i = 0
    while i < len(evs):
        t, data = evs[i]
        # batch events within 40 ms into one frame
        chunk = data; j = i + 1
        while j < len(evs) and evs[j][0] - t < 0.04:
            chunk += evs[j][1]; j += 1
        if last_t is not None:
            gap = min(t - last_t, idle); clock += gap
            timeline[-1]["dur"] = gap
        stream.feed(chunk.encode("utf-8", "replace"))
        text = "\n".join(screen.display)
        for m in re.finditer(r"# (\d)\. ", text):
            markers.setdefault(m.group(1), round(clock, 2))
        for name, pat in EXTRA_MARKERS.items():
            if name not in markers and re.search(pat, text):
                markers[name] = round(clock, 2)
        p = out / "frames" / f"{n:05d}.png"; draw().save(p); n += 1
        timeline.append({"t": round(clock, 3), "dur": 0.1, "frame": str(p)})
        last_t = evs[j - 1][0]; i = j
    timeline[-1]["dur"] = hold_end
    (out / "timeline.json").write_text(json.dumps({"size": [W, H], "frames": timeline, "markers": markers,
                                                    "duration": round(clock + hold_end, 2)}, indent=1))
    return W, H, len(timeline), clock + hold_end, markers

if __name__ == "__main__":
    print(render(Path(sys.argv[1]), Path(sys.argv[2])))
