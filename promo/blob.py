# Blob series: short, hook-first stop-motion episodes for Reels / Shorts (1080x1920).
# Each episode: big hook text from frame one -> the stop-motion clip with pop-up captions and sound
# effects -> an instant slow-motion replay of the best moment -> a question for the comments,
# "Framey, the stop-motion app, coming soon" and "Follow for Part 2".
# Usage: python3 blob.py <scene> [<scene> ...]     (scenes are described in blob.json)
#        python3 blob.py --preview <scene>          (writes a few still frames only, no video)
import os, sys, glob, json, math, subprocess, wave, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

V = "/mnt/files/v"
D = os.environ.get("WORK", "/home/user/work"); CF = D + "/cool"
OUT = os.environ.get("OUTDIR", "/home/user/vout"); FF = os.environ.get("FFMPEG", "ffmpeg")
FB = V + "/Inter.ttf"; ICON = V + "/icon.png"
W, H, FPS, SR = 1080, 1920, 30, 44100
OR = (254, 97, 0); WHITE = (255, 255, 255); GREY = (205, 205, 212); INK = (17, 17, 17)
EP = json.load(open(V + "/blob.json"))
CLIP_Y, CLIP_W = 470, 1080


def font(size):
    f = ImageFont.truetype(FB, size)
    try:
        ax = f.get_variation_axes(); f.set_variation_by_axes([32, 850] if len(ax) == 2 else [850])
    except Exception:
        pass
    return f


_tl = {}
def text_block(lines, size, stroke=7, width=W - 80):
    """lines: [[[text, 'w'|'o'|'g'], ...], ...] -> RGBA image, centered, with a dark outline."""
    key = (json.dumps(lines), size, stroke)
    if key in _tl: return _tl[key]
    col = {"w": WHITE, "o": OR, "g": GREY}
    f = font(size); lh = int(size * 1.12); d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    im = Image.new("RGBA", (width, lh * len(lines) + stroke * 2 + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        tw = sum(d0.textlength(t, font=f) for t, _ in ln); x = (width - tw) / 2
        for t, c in ln:
            d.text((x, stroke + i * lh), t, font=f, fill=col[c], stroke_width=stroke, stroke_fill=(0, 0, 0))
            x += d0.textlength(t, font=f)
    _tl[key] = im; return im


def paste_pop(base, layer, top, age, dur=0.22):
    """Paste a layer centered horizontally; it springs in over `dur` seconds after it appears."""
    if age < 0: return
    k = min(1, age / dur); s = 1 + 0.18 * math.sin(k * math.pi) if k < 1 else 1
    s *= 0.85 + 0.15 * min(1, k * 1.6)
    L = layer if abs(s - 1) < 1e-3 else layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))), Image.LANCZOS)
    base.paste(L, (int((W - L.width) / 2), int(top + (layer.height - L.height) / 2)), L)


_badge = []
def badge(im):
    """The Framey icon + name tag at the top of every frame."""
    if not _badge:
        ic = Image.open(ICON).convert("RGB").resize((76, 76), Image.LANCZOS)
        m = Image.new("L", ic.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 75, 75], 18, fill=255); ic = ic.convert("RGBA"); ic.putalpha(m)
        f = font(48); tw = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength("Framey", font=f))
        bw, bh = 12 + 76 + 16 + tw + 30, 100
        b = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
        d.rounded_rectangle([0, 0, bw - 1, bh - 1], bh // 2, fill=(0, 0, 0, 140))
        b.paste(ic, (12, 12), ic); d.text((104, 20), "Framey", font=f, fill=WHITE); _badge.append(b)
    b = _badge[0]; im.paste(b, ((W - b.width) // 2, 64), b)


_bgc = {}
def backdrop(fr, idx):
    """Full-screen blurred, darkened copy of the clip frame behind everything (no black borders)."""
    if idx not in _bgc:
        if len(_bgc) > 6: _bgc.clear()
        r = H / fr.height; small = fr.resize((max(1, int(fr.width * r / 10)), H // 10), Image.BILINEAR)
        small = small.filter(ImageFilter.GaussianBlur(4)).resize((int(fr.width * r), H), Image.BILINEAR)
        x0 = (small.width - W) // 2; g = small.crop((x0, 0, x0 + W, H))
        _bgc[idx] = Image.blend(g, Image.new("RGB", (W, H), INK), 0.5)
    return _bgc[idx].copy()


def load_clip(name):
    fs = sorted(glob.glob(f"{CF}/{name}_*.jpg"))
    if not fs: raise SystemExit(f"No frames for {name} in {CF}: run precool.py {name} first")
    h = int(760 * CLIP_W / 960)
    return [Image.open(f).convert("RGB").resize((CLIP_W, h), Image.LANCZOS) for f in fs]


# ---------------------------------------------------------------- sound
def tone(f0, f1, dur, vib=0.0, amp=0.5):
    t = np.arange(int(dur * SR)) / SR; f = np.linspace(f0, f1, len(t)) * (1 + vib * np.sin(2 * np.pi * 14 * t))
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5 / dur)

def noise(dur, amp=0.5, smooth=1, rise=False):
    rng = np.random.default_rng(int(dur * 1000)); n = rng.uniform(-1, 1, int(dur * SR))
    if smooth > 1: n = np.convolve(n, np.ones(smooth) / smooth, "same") * math.sqrt(smooth)
    env = np.sin(np.linspace(0, np.pi, len(n))) if rise else np.exp(-np.linspace(0, 7, len(n)))
    return amp * n * env

SFX = {
    "boing": lambda: tone(170, 560, 0.28, vib=0.06, amp=0.55),
    "pop": lambda: tone(900, 1400, 0.07, amp=0.5) + noise(0.05, 0.15),
    "clack": lambda: noise(0.06, 0.6, smooth=3) + tone(420, 380, 0.06, amp=0.3),
    "splat": lambda: noise(0.22, 0.7, smooth=12),
    "whoosh": lambda: noise(0.45, 0.45, smooth=30, rise=True),
    "rumble": lambda: noise(0.9, 0.5, smooth=60),
    "ding": lambda: np.concatenate([tone(988, 988, 0.16, amp=0.4), tone(1319, 1319, 0.42, amp=0.45)]),
    "vroom": lambda: tone(90, 160, 0.5, vib=0.25, amp=0.45),
}

def music(dur):
    """A light bouncy loop: kick on every beat, a plucky bass line, a hat on the off-beats (120 bpm)."""
    n = int(dur * SR); mix = np.zeros(n); beat = SR // 2
    kick = tone(120, 45, 0.18, amp=0.55); hat = noise(0.04, 0.12)
    notes = [55, 55, 82.4, 73.4, 55, 55, 98, 82.4]
    for i, s in enumerate(range(0, n, beat)):
        for snd, at in ((kick, s), (hat, s + beat // 2)):
            e = min(n, at + len(snd)); mix[at:e] += snd[: e - at] if at < n else 0
        b = tone(notes[i % 8], notes[i % 8], 0.3, amp=0.28); e = min(n, s + len(b)); mix[s:e] += b[: e - s]
    return mix * 0.55


# ---------------------------------------------------------------- one episode
def episode(name, preview=False):
    ep = EP[name]; clip = load_clip(name); n = len(clip)
    a, b = ep["replay"]; a, b = max(0, a), min(n - 1, b)
    T_A = n / 8; T_B = (b - a + 1) / 4; T_C = 2.2; dur = T_A + T_B + T_C
    hook = text_block(ep["hook"], 88); epl = text_block([[["BLOB  ·  EPISODE " + str(ep["ep"]), "o"]]], 40, stroke=5)
    subs = sorted(ep["subs"], key=lambda s: s[0])
    replay = text_block([[["INSTANT REPLAY", "o"]]], 64); slower = text_block([[["(slower)", "g"]]], 44, stroke=5)
    ask = text_block(ep["ask"], 76)
    tag1 = text_block([[["Framey", "o"], [" · the stop-motion app", "w"]]], 46, stroke=5)
    tag2 = text_block([[["COMING SOON  ·  ", "g"], ["FOLLOW FOR PART 2", "o"]]], 44, stroke=5)
    cy = CLIP_Y; ch = clip[0].height

    def frame(t):
        if t < T_A: idx = min(n - 1, int(t * 8)); phase = "A"
        elif t < T_A + T_B: idx = min(b, a + int((t - T_A) * 4)); phase = "B"
        else: idx = n - 1; phase = "C"
        fr = clip[idx]; im = backdrop(fr, idx); im.paste(fr, (0, cy)); badge(im)
        if phase == "A":
            paste_pop(im, epl, 190, t); paste_pop(im, hook, 245, t - 0.05)
            cur = [s for s in subs if s[0] <= idx]
            if cur:
                s = cur[-1]; L = text_block(s[1], 80); paste_pop(im, L, cy + ch + 40, t - s[0] / 8)
        elif phase == "B":
            tb = t - T_A; paste_pop(im, replay, 250, tb); paste_pop(im, slower, 340, tb - 0.1)
        else:
            tc = t - T_A - T_B; dk = Image.new("RGBA", (W, H), (0, 0, 0, int(150 * min(1, tc / 0.25)))); im.paste(dk, (0, 0), dk); badge(im)
            paste_pop(im, ask, 560, tc); paste_pop(im, text_block([[["Comment below", "g"]]], 50, stroke=5), 560 + ask.height + 10, tc - 0.2)
            paste_pop(im, tag1, 1330, tc - 0.45); paste_pop(im, tag2, 1410, tc - 0.6)
        return im

    if preview:
        os.makedirs(D + "/preview", exist_ok=True)
        ts = [0.3, T_A * 0.6, T_A - 0.1, T_A + T_B * 0.5, dur - 0.3]
        ims = [frame(t).resize((270, 480)) for t in ts]; sheet = Image.new("RGB", (270 * len(ims), 480))
        for i, x in enumerate(ims): sheet.paste(x, (270 * i, 0))
        sheet.save(f"{D}/preview/blob-{name}.jpg", quality=80); print("preview", name, round(dur, 2)); return

    d = f"{D}/r/blob-{name}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for i in range(round(dur * FPS)): frame(i / FPS).save(f"{d}/{i:04d}.jpg", quality=90)
    v = f"{D}/r/blob-{name}_v.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{d}/%04d.jpg", "-threads", "1", "-c:v", "libx264", "-crf", "20",
                    "-preset", "veryfast", "-pix_fmt", "yuv420p", v], check=True)
    mix = music(dur)
    def hit(at, kind):
        s = SFX[kind](); i0 = int(at * SR); e = min(len(mix), i0 + len(s))
        if i0 < len(mix): mix[i0:e] += s[: e - i0]
    for f, kind in ep["sfx"]:
        hit(f / 8, kind)
        if a <= f <= b: hit(T_A + (f - a) / 4, kind)
    hit(T_A + T_B, "ding")
    fo = int(0.6 * SR); mix[-fo:] *= np.linspace(1, 0, fo); mix = np.clip(mix, -1, 1)
    wv = f"{D}/r/blob-{name}.wav"
    with wave.open(wv, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes())
    os.makedirs(OUT, exist_ok=True); out = f"{OUT}/framey-blob-{name}.mp4"; tmp = out[:-4] + ".tmp.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", v, "-i", wv, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-ar", "44100", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out); shutil.rmtree(d, ignore_errors=True); print("blob", name, round(dur, 2), out)


if __name__ == "__main__":
    args = sys.argv[1:]; pv = "--preview" in args
    for nm in [x for x in args if not x.startswith("--")]:
        if not pv and os.path.exists(f"{V}/vout/framey-blob-{nm}.mp4"): print("skip", nm); continue
        episode(nm, preview=pv)
