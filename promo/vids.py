# Framey promo videos (9:16, for Instagram Reels and YouTube Shorts). Usage: python3 vids.py <which: promo|lock|tut|all>
import os, io, json, base64, subprocess, wave, shutil, math, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = os.environ.get("WORK", os.path.dirname(os.path.abspath(__file__)))
A = os.environ["ASSETS"]            # cap.py output: a_shoot.png ... final.json
ICON = os.environ["ICON"]; OUTDIR = os.environ["OUTDIR"]; FF = os.environ.get("FFMPEG", "ffmpeg")
WHICH = sys.argv[1] if len(sys.argv) > 1 else "all"
W, H, FPS = 1080, 1920, 30
BEAT = 60 / 128
OR = (254, 97, 0); BG = (17, 17, 17); WHITE = (255, 255, 255); GREY = (190, 190, 196)
FB = os.environ.get("FONT_BOLD", "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf")
def font(p, s):
    f = ImageFont.truetype(p, s)
    try:
        ax = f.get_variation_axes(); f.set_variation_by_axes([32, 800] if len(ax) == 2 else [800])
    except Exception: pass
    return f
def dec(u):  # decode a photo and shrink it (saves memory on small machines)
    im = Image.open(io.BytesIO(base64.b64decode(u.split(",")[1]))).convert("RGB"); im.thumbnail((900, 1200), Image.LANCZOS); return im
fin = json.load(open(A + "/final.json"))
locked = [dec(u) for u in fin["frames"]]
hop = locked
if os.path.exists(A + "/green.json"):
    _cl = json.load(open(A + "/green.json")).get("clean")
    if _cl: hop = [dec(u) for u in _cl]
    del _cl
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3

_bg = []
def bg(t=0):
    if not _bg:
        g = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(g)
        d.ellipse([-350, 1150, 1430, 2600], fill=(78, 32, 6)); _bg.append(g.filter(ImageFilter.GaussianBlur(170)))
    return _bg[0].copy()

def text_layer(lines, size=96, gap=1.08, width=W - 120):
    """lines: list of [(text, color), ...] per line. Returns RGBA image of the block."""
    f = font(FB, size); lh = int(size * gap)
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    ws = [sum(d0.textlength(t, font=f) for t, _ in ln) for ln in lines]
    im = Image.new("RGBA", (width, lh * len(lines) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        x = (width - ws[i]) / 2
        for t, c in ln: d.text((x, i * lh), t, font=f, fill=c); x += d.textlength(t, font=f)
    return im

def pop(base, layer, cx, top, t, delay=0.0):
    k = ease((t - delay) / 0.28)
    if k <= 0: return
    s = 0.86 + 0.14 * k
    L = layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))), Image.LANCZOS)
    if k < 1:
        a = L.split()[3].point(lambda v: int(v * k)); L.putalpha(a)
    base.paste(L, (int(cx - L.width / 2), int(top + (layer.height - L.height) / 2)), L)

def rounded(im, r):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], r, fill=255)
    o = im.convert("RGBA"); o.putalpha(m); return o

_phone = {}
def phone(path, h):
    key = (path, h)
    if key in _phone: return _phone[key]
    s = Image.open(path).convert("RGB"); w = int(s.width * h / s.height); s = s.resize((w, h), Image.LANCZOS)
    pad = 16; r = int(w * 0.11)
    ph = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(ph).rounded_rectangle([0, 0, ph.width - 1, ph.height - 1], r + pad, fill=(44, 44, 46, 255))
    sc = rounded(s, r); ph.paste(sc, (pad, pad), sc)
    sh = Image.new("RGBA", (ph.width + 160, ph.height + 160), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([80, 100, 80 + ph.width, 100 + ph.height], r + pad, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(36)); sh.paste(ph, (80, 80), ph)
    _phone[key] = sh; return sh

def put_phone(base, path, h, cx, top, t, delay=0.0, rot=0):
    p = phone(path, h)
    if rot: p = p.rotate(rot, resample=Image.BICUBIC, expand=True)
    k = ease((t - delay) / 0.4)
    y = top + (1 - k) * 260
    base.paste(p, (int(cx - p.width / 2), int(y - 80)), p)

def tap(base, x, y, t, at):
    k = (t - at) / 0.45
    if 0 <= k <= 1:
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); r = 40 + 50 * k
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, int(255 * (1 - k))), width=8)
        base.paste(ov, (0, 0), ov)

_badge = []
def badge(im):
    """Small 'Framey' tag with the app icon, at the top of every scene."""
    if not _badge:
        ic = rounded(Image.open(ICON).convert("RGB").resize((76, 76), Image.LANCZOS), 18)
        f = font(FB, 48); tw = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength("Framey", font=f))
        bw, bh = 12 + 76 + 16 + tw + 30, 100
        b = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
        d.rounded_rectangle([0, 0, bw - 1, bh - 1], bh // 2, fill=(0, 0, 0, 120))
        b.paste(ic, (12, 12), ic); d.text((12 + 76 + 16, 20), "Framey", font=f, fill=(255, 255, 255)); _badge.append(b)
    b = _badge[0]; im = im.convert("RGB"); im.paste(b, ((W - b.width) // 2, 64), b); return im

def scene_frames(name, dur, draw):
    if os.environ.get("SKIP") and os.path.exists(f"{D}/r/{name}.mp4"): return f"{D}/r/{name}.mp4"
    d = f"{D}/r/{name}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    n = round(dur * FPS)
    for i in range(n):
        im = draw(i / FPS)
        if not (name.endswith("7end") or name == "tut_end"): im = badge(im)
        im.convert("RGB").save(f"{d}/{i:04d}.jpg", quality=92)
    out = f"{D}/r/{name}.mp4"; tmp = out[:-4] + ".tmp.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{d}/%04d.jpg", "-threads", "1", "-x264-params", "rc-lookahead=0:sliced-threads=0", "-c:v", "libx264", "-crf", "18",
                    "-preset", "veryfast", "-pix_fmt", "yuv420p", "-color_range", "tv", tmp], check=True)
    os.replace(tmp, out); return out

os.makedirs(D + "/r", exist_ok=True)
scenes = []

# 1. Hook: the clay ball hopping, big words
T_HOOK = BEAT * 8
L1 = text_layer([[("Make your toys", WHITE)], [("come alive", OR)]], 104)
def s1(t):
    im = bg(); k = int(t * 8) % len(hop); f = hop[k]
    w = 960; h = int(f.height * w / f.width); fr = rounded(f.resize((w, h), Image.LANCZOS), 48)
    im.paste(fr, ((W - w) // 2, 560), fr)
    pop(im, L1, W / 2, 200, t)
    if t > BEAT * 4: pop(im, text_layer([[("Stop-motion on your phone", GREY)]], 54), W / 2, 560 + h + 70, t, BEAT * 4)
    return im
scenes.append(("1hook", T_HOOK, s1))

# 2. Snap, nudge, repeat
T6 = BEAT * 6
L2 = text_layer([[("Snap. Nudge.", WHITE)], [("Repeat.", OR)]], 104)
def s2(t):
    im = bg(); put_phone(im, A + "/a_shoot.png", 1240, W / 2, 560, t, 0.05)
    pop(im, L2, W / 2, 190, t)
    for at in (0.8, 1.75): tap(im, W / 2, 560 + 16 + int(1240 * 0.915), t, at)
    return im
scenes.append(("2snap", T6, s2))

# 3. Lock: real shaky phone footage, before and after
raw = [dec(u) for u in fin["raw"]]
fix = locked
L3 = text_layer([[("Shaky hands?", WHITE)], [("Lock", OR), (" fixes it.", WHITE)]], 100)
def panel(f, w):
    h = int(f.height * w / f.width); return rounded(f.resize((w, h), Image.LANCZOS), 36)
def s3(t):
    im = bg(); k = int(t * 5) % len(raw); w = 450
    a = panel(raw[k], w); b = panel(fix[k], w); y = 660
    im.paste(a, (70, y), a); im.paste(b, (W - 70 - w, y), b)
    d = ImageDraw.Draw(im); f = font(FB, 44)
    for x0, txt, col in ((70, "Without Lock", GREY), (W - 70 - w, "With Lock", OR)):
        tw = d.textlength(txt, font=f); d.text((x0 + (w - tw) / 2, y + a.height + 30), txt, font=f, fill=col)
    d.rounded_rectangle([W - 70 - w - 7, y - 7, W - 70 + 7, y + b.height + 7], 42, outline=OR, width=6)
    pop(im, L3, W / 2, 210, t)
    pop(im, text_layer([[("Same photos, phone wobbling", GREY)]], 44), W / 2, y + a.height + 130, t, 0.4)
    return im
scenes.append(("3lock", BEAT * 8, s3))

# 4. Green screen
L4 = text_layer([[("Green screen.", WHITE)], [("Go anywhere.", OR)]], 104)
def s4(t):
    im = bg(); put_phone(im, A + "/g_green.png", 1240, W / 2, 560, t, 0.05)
    pop(im, L4, W / 2, 190, t); return im
scenes.append(("4green", T6, s4))

# 5. Music
L5 = text_layer([[("Add any song", WHITE)], [("in seconds", OR)]], 104)
def s5(t):
    im = bg(); put_phone(im, A + "/song.png", 1240, W / 2, 560, t, 0.05)
    pop(im, L5, W / 2, 190, t); return im
scenes.append(("5music", T6, s5))

# 6. Titles + drawing, two phones
L6 = text_layer([[("Titles. Doodles.", WHITE)], [("Your movie.", OR)]], 100)
def s6(t):
    im = bg()
    put_phone(im, A + "/c_title.png", 940, W / 2 - 255, 660, t, 0.0, rot=6)
    put_phone(im, A + "/b_draw.png", 940, W / 2 + 255, 700, t, 0.18, rot=-6)
    pop(im, L6, W / 2, 190, t); return im
scenes.append(("6titles", T6, s6))

# 7. End card
icon = Image.open(ICON).convert("RGB").resize((420, 420), Image.LANCZOS); icon = rounded(icon, 96)
def s7(t):
    im = bg(); k = ease(t / 0.35); s = 0.7 + 0.3 * k
    ic = icon.resize((int(420 * s), int(420 * s)), Image.LANCZOS)
    im.paste(ic, (int((W - ic.width) / 2), int(470 + (420 - ic.height) / 2)), ic)
    pop(im, text_layer([[("Framey", WHITE)]], 150), W / 2, 960, t, 0.15)
    pop(im, text_layer([[("The ", GREY), ("stop-motion app", WHITE), (" for your phone", GREY)]], 54), W / 2, 1150, t, 0.3)
    k3 = ease((t - 0.5) / 0.3)
    if k3 > 0:  # orange "COMING SOON" badge
        f = font(FB, 64); d = ImageDraw.Draw(im); txt = "COMING SOON"; tw = d.textlength(txt, font=f)
        bw, bh = tw + 110, 112; s3 = 0.8 + 0.2 * k3
        badge = Image.new("RGBA", (int(bw), bh), (0, 0, 0, 0)); bd = ImageDraw.Draw(badge)
        bd.rounded_rectangle([0, 0, bw - 1, bh - 1], bh // 2, fill=OR + (255,)); bd.text((55, 18), txt, font=f, fill=(17, 17, 17))
        badge = badge.resize((int(bw * s3), int(bh * s3)), Image.LANCZOS)
        im.paste(badge, (int((W - badge.width) / 2), int(1280 + (bh - badge.height) / 2)), badge)
    pop(im, text_layer([[("Follow", OR), (" to be the first to try it", WHITE)]], 54), W / 2, 1460, t, 0.9)
    k2 = int(t * 8) % len(hop); f = hop[k2]; w = 300; h = int(f.height * w / f.width)
    return im
scenes.append(("7end", BEAT * 8, s7))

wb = base64.b64decode(fin["wav"].split(",")[1]); open(D + "/r/song.wav", "wb").write(wb); del fin, wb
with wave.open(D + "/r/song.wav") as w_: SR = w_.getframerate(); SONG = np.frombuffer(w_.readframes(w_.getnframes()), np.int16).astype(np.float32) / 32768

def audio(dur, path, clicks=()):
    n = int(dur * SR); mix = np.tile(SONG, n // len(SONG) + 1)[:n] * 0.8
    fo = int(1.2 * SR); mix[-fo:] *= np.linspace(1, 0, fo)
    rng = np.random.default_rng(1); cl = int(0.06 * SR); click = rng.uniform(-1, 1, cl) * np.exp(-np.linspace(0, 9, cl)) * 0.6
    for at in clicks:
        s0 = int(at * SR)
        if s0 + cl < n: mix[s0:s0 + cl] += click
    mix = np.clip(mix, -1, 1)
    with wave.open(path, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes())

def build(name, sc, clicks=()):
    files = [scene_frames(f"{name}_{n}", d, fn) for n, d, fn in sc]
    dur = sum(d for _, d, _ in sc)
    with open(f"{D}/r/{name}.txt", "w") as f:
        for p in files: f.write(f"file '{p}'\n")
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{D}/r/{name}.txt", "-c", "copy", f"{D}/r/{name}_v.mp4"], check=True)
    audio(dur, f"{D}/r/{name}.wav", clicks)
    out = f"{OUTDIR}/framey-{name}.mp4"; tmp = out[:-4] + ".tmp.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", f"{D}/r/{name}_v.mp4", "-i", f"{D}/r/{name}.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out); print(name, round(dur, 2), out); return out

END = ("7end", BEAT * 8, s7)
if WHICH in ("promo", "all"):
    t0 = scenes[0][1]
    build("promo-1", scenes, clicks=(t0 + 0.8, t0 + 1.75))

# Video 2: Lock, before and after
LA = text_layer([[("Can't hold your", WHITE)], [("phone still?", OR)]], 104)
def la(t):
    im = bg(); f = raw[int(t * 5) % len(raw)]; w = 820; h = int(f.height * w / f.width); fr = rounded(f.resize((w, h), Image.LANCZOS), 48)
    im.paste(fr, ((W - w) // 2, 560), fr); pop(im, LA, W / 2, 200, t)
    pop(im, text_layer([[("Every photo jumps around...", GREY)]], 54), W / 2, 560 + h + 60, t, 1.0)
    return im
LB = text_layer([[("Framey's ", WHITE), ("Lock", OR)], [("fixes it", WHITE)]], 104)
def lb(t):
    im = s3(t); return im
if WHICH in ("lock", "all"):
    build("lock-short", [("a", BEAT * 8, la), ("b", BEAT * 10, s3), END])

# Video 3: the tutorial with the Coming Soon ending
if WHICH in ("tut", "all"):
    src = os.environ.get("TUTORIAL")
    endv = scene_frames("tut_end", BEAT * 8, s7); audio(BEAT * 8, f"{D}/r/tut_end.wav")
    out = f"{OUTDIR}/framey-tutorial.mp4"; tmp = out[:-4] + ".tmp.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", src, "-i", endv, "-i", f"{D}/r/tut_end.wav", "-filter_complex",
                    "[0:v]fps=30,format=yuv420p,setsar=1[v0];[1:v]fps=30,format=yuv420p,setsar=1[v1];[0:a]aresample=44100,aformat=channel_layouts=mono[a0];[2:a]aresample=44100,aformat=channel_layouts=mono[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "21", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out); print("tutorial", out)
