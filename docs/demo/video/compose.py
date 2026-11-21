#!/usr/bin/env python3
"""Compose the narrated demo video from rendered terminal frames, narration WAVs and cards.

Layout (1920x1080): terminal viewport (top), caption band (bottom), scene chip (top-left),
watermark (top-right). Hermes scenes use a smoothed "follow the new text" camera so text stays
readable; other scenes use a fixed close-up. Captions are burned in and also exported as SRT.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

W, H = 1920, 1080
VIEW = (0, 0, 1920, 930)          # terminal viewport
CAP_TOP = 930                      # caption band starts here
NAVY = (41, 88, 140)
INK = (32, 36, 44)
GREY = (110, 118, 130)
TERM_BG = (30, 30, 30)
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
WATERMARK = "© 2026 trykarkedekho.com"
FPS = 30
SR = 44100


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


@dataclass
class Piece:
    img: Image.Image
    dur: float


# ------------------------------------------------------------------ narration
def load_narration(voice_dir: Path) -> dict[str, dict]:
    """Return {key: {text, wav(np.ndarray|None), dur}}; missing WAVs get an estimated silent duration."""
    out = {}
    for line in (voice_dir / "narration.txt").read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, text = line.split("|", 1)
        wav_path = voice_dir / f"vo_{key}.wav"
        if wav_path.exists():
            with wave.open(str(wav_path)) as w:
                frames = w.readframes(w.getnframes())
                ch, sw, sr = w.getnchannels(), w.getsampwidth(), w.getframerate()
            a = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
            if ch == 2:
                a = a.reshape(-1, 2).mean(axis=1)
            if sr != SR:  # simple linear resample
                idx = np.linspace(0, len(a) - 1, int(len(a) * SR / sr))
                a = np.interp(idx, np.arange(len(a)), a)
            out[key] = {"text": text, "wav": a, "dur": len(a) / SR}
        else:
            out[key] = {"text": text, "wav": None, "dur": len(text.split()) / 2.7}
    return out


def caption_text(text: str) -> str:
    """Narration is spelled for the speech engine; captions use the written forms."""
    return (text.replace("Try karke dekho dot com", "trykarkedekho.com")
                .replace("hermes budget router", "hermes-budget-router"))


def caption_chunks(text: str, max_chars: int = 110) -> list[str]:
    """Split into caption lines of at most two rows (~max_chars), on sentence/clause boundaries."""
    parts = re.split(r"(?<=[.?!:])\s+", text.strip())
    chunks: list[str] = []
    for p in parts:
        while len(p) > max_chars:
            cut = p.rfind(",", 0, max_chars)
            cut = cut if cut > 20 else p.rfind(" ", 0, max_chars)
            chunks.append(p[:cut + 1].strip())
            p = p[cut + 1:].strip()
        if p:
            chunks.append(p)
    return chunks


def timed_captions(text: str, start: float, dur: float) -> list[tuple[float, float, str]]:
    chunks = caption_chunks(caption_text(text))
    total = sum(len(c) for c in chunks) or 1
    t, out = start, []
    for c in chunks:
        d = dur * len(c) / total
        out.append((t, t + d, c))
        t += d
    return out


# ------------------------------------------------------------------ drawing
def draw_caption(img: Image.Image, text: str | None) -> None:
    import os
    d = ImageDraw.Draw(img)
    d.rectangle([0, CAP_TOP, W, H], fill=(12, 14, 18))
    if not text or os.environ.get("BURN", "1") == "0":
        return
    f = font(SANS, 40)
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if d.textlength(trial, font=f) > W - 160 and cur:
            lines.append(cur)
            cur = w_
        else:
            cur = trial
    lines.append(cur)
    lines = lines[:2]
    y = CAP_TOP + (H - CAP_TOP - len(lines) * 52) // 2
    for ln in lines:
        x = (W - d.textlength(ln, font=f)) / 2
        d.text((x, y), ln, font=f, fill=(255, 255, 255))
        y += 52


def draw_overlays(img: Image.Image, chip: str | None, dark: bool = True) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    fw = font(SANS, 24)
    tw = d.textlength(WATERMARK, font=fw)
    col = (255, 255, 255, 150) if dark else (41, 88, 140, 200)
    d.text((W - tw - 28, 20), WATERMARK, font=fw, fill=col)
    if chip:
        fc = font(SANS_B, 28)
        cw = d.textlength(chip, font=fc)
        d.rounded_rectangle([20, 14, 20 + cw + 36, 62], radius=10, fill=(41, 88, 140, 235))
        d.text((38, 21), chip, font=fc, fill=(255, 255, 255, 255))


def card(lines: list[tuple[str, int, tuple, bool]], bg=(255, 255, 255), accent=True) -> Image.Image:
    """Simple centred text card. lines: (text, size, colour, bold)."""
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    if accent:
        d.rectangle([0, 0, W, 16], fill=NAVY)
    total = sum(s * 1.45 for _, s, _, _ in lines)
    y = (CAP_TOP - total) / 2 + 10
    for text, size, colour, bold in lines:
        f = font(SANS_B if bold else SANS, size)
        x = (W - d.textlength(text, font=f)) / 2
        d.text((x, y), text, font=f, fill=colour)
        y += size * 1.45
    return img


def comparison_card(data: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 16], fill=NAVY)
    t = font(SANS_B, 54)
    title = "Same agent. Same setup. Different questions."
    d.text(((W - d.textlength(title, font=t)) / 2, 70), title, font=t, fill=INK)
    cols = [data["simple"], data["complex"]]
    box_w, gap = 760, 80
    x0 = (W - 2 * box_w - gap) / 2
    for i, c in enumerate(cols):
        x = x0 + i * (box_w + gap)
        d.rounded_rectangle([x, 190, x + box_w, 800], radius=24, outline=NAVY, width=4,
                            fill=(244, 247, 251) if i == 0 else (236, 242, 249))
        fl, fv, fs = font(SANS, 34), font(SANS_B, 92), font(SANS, 34)
        d.text((x + 50, 225), c["label"], font=font(SANS_B, 40), fill=NAVY)
        d.text((x + 50, 285), f"“{c['question']}”", font=font(SANS, 28), fill=GREY)
        d.text((x + 50, 360), "Router picked", font=fl, fill=GREY)
        d.text((x + 50, 405), c["model"], font=font(SANS_B, 56), fill=INK)
        d.text((x + 50, 500), "Measured cost", font=fl, fill=GREY)
        d.text((x + 50, 545), c["cost"], font=fv, fill=NAVY)
        d.text((x + 50, 680), c["detail"], font=fs, fill=INK)
    note = font(SANS, 30)
    for k, line in enumerate(data["notes"]):
        d.text(((W - d.textlength(line, font=note)) / 2, 835 + k * 42), line, font=note, fill=GREY)
    return img


# ------------------------------------------------------------------ terminal scenes
def content_box(im: Image.Image, skip_bottom: int = 0) -> tuple | None:
    diff = ImageChops.difference(im, Image.new("RGB", im.size, TERM_BG)).convert("L")
    if skip_bottom:
        diff = diff.crop((0, 0, im.width, im.height - skip_bottom))
    return diff.point(lambda p: 255 if p > 30 else 0).getbbox()


def fit_into_view(crop: Image.Image) -> Image.Image:
    vx0, vy0, vx1, vy1 = VIEW
    vw, vh = vx1 - vx0, vy1 - vy0
    s = min(vw / crop.width, vh / crop.height)
    sized = crop.resize((max(1, int(crop.width * s)), max(1, int(crop.height * s))), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), TERM_BG)
    canvas.paste(sized, (vx0 + (vw - sized.width) // 2, vy0 + (vh - sized.height) // 2 + 30))
    return canvas


def static_scene(frames: list[dict], max_scale: float = 1.7) -> list[Piece]:
    box = None
    for f in frames:
        bb = content_box(Image.open(f["frame"]))
        if bb:
            box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
    if box is None:
        box = (0, 0, 800, 400)
    pad = 24
    x0, y0, x1, y1 = max(0, box[0] - pad), max(0, box[1] - pad), box[2] + pad, box[3] + pad
    vw, vh = VIEW[2] - VIEW[0], VIEW[3] - VIEW[1] - 60
    s = min(vw / (x1 - x0), vh / (y1 - y0), max_scale)
    cw, ch = vw / s, vh / s  # expand crop to the viewport aspect so text isn't over-zoomed
    x1, y1 = x0 + cw, y0 + ch
    return [Piece(fit_into_view(Image.open(f["frame"]).crop((int(x0), int(y0), int(x1), int(y1)))), f["dur"])
            for f in frames]


def follow_scene(frames: list[dict], win_w: int = 1700, status_rows_px: int = 120) -> list[Piece]:
    """Camera that follows where the terminal changed most recently, smoothed."""
    first = Image.open(frames[0]["frame"])
    tw, th = first.size
    win_h = int(win_w * (VIEW[3] - VIEW[1] - 60) / (VIEW[2] - VIEW[0]))
    focus_y, prev, out = th - win_h / 2, None, []
    for f in frames:
        im = Image.open(f["frame"])
        if prev is not None:
            diff = ImageChops.difference(im, prev).convert("L").crop((0, 0, tw, th - status_rows_px))
            bb = diff.point(lambda p: 255 if p > 40 else 0).getbbox()
            if bb:
                target = bb[3] - win_h * 0.35  # keep newest text in the lower-middle of the window
                target = min(max(target, win_h / 2), th - win_h / 2)
                focus_y += (target - focus_y) * 0.35
        prev = im
        y0 = int(min(max(focus_y - win_h / 2, 0), th - win_h))
        out.append(Piece(fit_into_view(im.crop((0, y0, min(win_w, tw), y0 + win_h))), f["dur"]))
    return out


def ink(path: str) -> int:
    """Count of pixels that differ clearly from the terminal background (full resolution)."""
    im = Image.open(path)
    hist = ImageChops.difference(im, Image.new("RGB", im.size, TERM_BG)).convert("L").histogram()
    return sum(hist[40:])


def trim_tail(frames: list[dict]) -> list[dict]:
    """Drop only the trailing near-empty frames (after `clear`, or Hermes' short exit summary), so a
    held frame shows the scene's content. Reference = the busiest frame in the scene's last 40%."""
    if len(frames) < 3:
        return frames
    inks = [ink(f["frame"]) for f in frames]
    ref = max(inks[int(len(inks) * 0.6):]) or 1
    end = len(frames)
    while end > 1 and inks[end - 1] < 0.4 * ref:
        end -= 1
    return frames[:end]


# ------------------------------------------------------------------ assembly
def build(timeline: Path, voice_dir: Path, data: dict, out_dir: Path) -> None:
    tl = json.loads(timeline.read_text())
    fr, m, total = tl["frames"], tl["markers"], tl["duration"]
    narr = load_narration(voice_dir)
    bounds = {"s1": (0, m["2"]), "s2": (m["2"], m["3"]), "s3": (m["3"], m["4"]), "s4": (m["4"], total)}
    chips = {"s1": "1 · Health check", "s2": "2 · Simple question → router picks Haiku",
             "s3": "3 · Complex question → router picks Opus", "s4": "4 · What each answer cost"}

    sections: list[tuple[str, list[Piece], str | None, bool]] = []
    title = card([("Pick the model before the conversation starts.", 64, INK, True),
                  ("A budget-aware router for the Hermes AI agent", 40, GREY, False),
                  ("", 30, GREY, False),
                  ("A real, unedited run · 21 Nov 2026", 32, NAVY, False)])
    sections.append(("title", [Piece(title, 1.0)], None, False))
    for key in ("s1", "s2", "s3", "s4"):
        a, b = bounds[key]
        frames = trim_tail([f for f in fr if a <= f["t"] < b])
        pieces = follow_scene(frames) if key in ("s2", "s3") else static_scene(frames)
        sections.append((key, pieces, chips[key], True))
    sections.append(("compare", [Piece(comparison_card(data), 1.0)], None, False))
    end = card([("hermes-budget-router", 72, NAVY, True),
                ("Free and open source · github.com/RajaMDM/hermes-budget-router", 36, INK, False),
                ("", 24, GREY, False),
                ("Made by Raja Shahnawaz Soni", 40, INK, True),
                ("© 2026 trykarkedekho.com", 36, NAVY, False),
                ("Code: MIT licence · Video: all rights reserved", 26, GREY, False)])
    sections.append(("end", [Piece(end, 1.0)], None, False))

    # timing: each section lasts max(visual, narration + lead + tail)
    lead, tail = 0.4, 0.7
    # extra narration clips anchored inside a section: key -> (section, seconds into that section)
    anchors = {"s3b": ("s3", m["footer_s3"] - m["3"] + 0.3)} if "footer_s3" in m and "s3b" in narr else {}
    plan, captions, audio_events, t = [], [], [], 0.0
    for key, pieces, chip, dark in sections:
        vis = sum(p.dur for p in pieces)
        nd = narr[key]["dur"] if key in narr else 0
        lead_k = {"s1": 1.6}.get(key, lead)  # let the health-check output appear before it's described
        need = nd + lead_k + tail
        extras = [(k, off) for k, (sec, off) in anchors.items() if sec == key]
        for k, off in extras:
            off = max(off, lead_k + nd + 0.3)  # never overlap the section's main narration
            anchors[k] = (key, off)
            need = max(need, off + narr[k]["dur"] + tail)
        length = max(vis, need, 3.0 if key in ("title", "end") else 0, 7.0 if key == "compare" else 0)
        if vis < length:  # hold the last visual frame
            pieces[-1].dur += length - vis
        if key in narr:
            captions += timed_captions(narr[key]["text"], t + lead_k, nd)
            audio_events.append((t + lead_k, narr[key]["wav"]))
        for k, _ in extras:
            off = anchors[k][1]
            captions += timed_captions(narr[k]["text"], t + off, narr[k]["dur"])
            audio_events.append((t + off, narr[k]["wav"]))
        plan.append((t, pieces, chip, dark))
        t += length
    duration = t

    # render pieces, splitting at caption boundaries
    out_dir.mkdir(parents=True, exist_ok=True)
    fdir = out_dir / "frames"
    fdir.mkdir(exist_ok=True)
    for old in fdir.glob("*.png"):
        old.unlink()
    cuts = sorted({round(x, 3) for c in captions for x in (c[0], c[1])})
    concat, n = [], 0

    def caption_at(tt: float) -> str | None:
        for s, e, txt in captions:
            if s <= tt < e:
                return txt
        return None

    for start, pieces, chip, dark in plan:
        tt = start
        for p in pieces:
            seg_start, seg_end = tt, tt + p.dur
            inner = [c for c in cuts if seg_start < c < seg_end]
            for a, b in zip([seg_start] + inner, inner + [seg_end]):
                if b - a < 1e-3:
                    continue
                img = p.img.copy()
                draw_overlays(img, chip, dark)
                draw_caption(img, caption_at((a + b) / 2))
                path = fdir / f"{n:05d}.png"
                img.save(path)
                concat.append((path, b - a))
                n += 1
            tt = seg_end
    lst = out_dir / "concat.txt"
    with lst.open("w") as fh:
        for path, d in concat:
            fh.write(f"file '{path.resolve()}'\nduration {d:.4f}\n")
        fh.write(f"file '{concat[-1][0].resolve()}'\n")

    # audio
    mix = np.zeros(int(duration * SR) + SR, dtype=np.float32)
    for at, wav in audio_events:
        if wav is None:
            continue
        i = int(at * SR)
        mix[i:i + len(wav)] += wav[: len(mix) - i]
    peak = np.abs(mix).max() or 1
    mix = (mix / peak * 0.89 * 32767).astype(np.int16) if peak > 1 else mix.astype(np.int16)
    with wave.open(str(out_dir / "narration.wav"), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(mix.tobytes())

    # captions file
    def ts(x: float) -> str:
        h, r = divmod(x, 3600)
        mi, s = divmod(r, 60)
        return f"{int(h):02d}:{int(mi):02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"
    (out_dir / "captions.srt").write_text("\n".join(
        f"{i}\n{ts(s)} --> {ts(e)}\n{txt}\n" for i, (s, e, txt) in enumerate(captions, 1)))

    # video
    import os
    burned = out_dir / ("demo-narrated.mp4" if os.environ.get("BURN", "1") != "0" else "demo-narrated-cc.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-i", str(out_dir / "narration.wav"), "-vf", f"fps={FPS},format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
                    "-shortest", "-movflags", "+faststart", str(burned)], check=True)
    print(json.dumps({"duration": round(duration, 1), "frames": n, "captions": len(captions),
                      "video": str(burned)}, indent=1))


if __name__ == "__main__":
    import sys
    data = json.loads(Path(sys.argv[3]).read_text())
    build(Path(sys.argv[1]), Path(sys.argv[2]), data, Path(sys.argv[4]))
