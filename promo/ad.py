# FRAMEY AD: motion-graphics app ad made 100% in code. Phone mockup, feature beats, kinetic type, synth beat.
# Usage: python3 ad.py [--preview]
import os, sys, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

V = os.environ.get("FRAMEY_DIR", "/mnt/files/v"); OUT = os.environ.get("OUTDIR", V + "/vout"); FF = os.environ.get("FFMPEG", "ffmpeg")
W, H, FPS = 1080, 1920, 30; DUR = 23.0
FB = V + "/Inter.ttf"; ICON = V + "/icon.png"
OR, YEL, WHITE, INK = (255, 122, 26), (255, 214, 10), (255, 255, 255), (16, 14, 22)
_fc = {}
def F(sz, wt=900):
    k = (sz, wt)
    if k not in _fc:
        f = ImageFont.truetype(FB, sz)
        try:
            ax = f.get_variation_axes(); f.set_variation_by_axes([32, wt] if len(ax) == 2 else [wt])
        except Exception: pass
        _fc[k] = f
    return _fc[k]
def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def spring(x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    return 1 - math.exp(-6 * x) * math.cos(10 * x)
def ctext(d, y, s, sz, col=WHITE, wt=900, sc=1.0, stroke=0):
    if sc <= 0.02: return
    f = F(max(8, int(sz * sc)), wt)
    while d.textlength(s, font=f) > W - 90 and sz > 30: sz -= 4; f = F(max(8, int(sz * sc)), wt)
    d.text((W / 2, y), s, font=f, fill=col, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))

ICON_IM = None
def icon(size):
    global ICON_IM
    if ICON_IM is None: ICON_IM = Image.open(ICON).convert("RGB")
    ic = ICON_IM.resize((size, size), Image.LANCZOS); m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], int(size * 0.23), fill=255); return ic, m

def background(t):
    g = np.linspace(0, 1, H)[:, None]
    base = (np.array([18, 14, 26]) * (1 - g) + np.array([34, 18, 30]) * g)
    im = Image.fromarray(np.repeat(base[:, None, :], W, 1).astype(np.uint8))
    glow = Image.new("RGB", (W // 4, H // 4)); gd = ImageDraw.Draw(glow)
    for k, (cx, cy, r) in enumerate(((0.2, 0.25, 90), (0.85, 0.7, 110), (0.5, 0.95, 80))):
        x = W / 4 * (cx + 0.06 * math.sin(t * 0.7 + k * 2)); y = H / 4 * (cy + 0.04 * math.cos(t * 0.5 + k))
        gd.ellipse([x - r, y - r, x + r, y + r], fill=(120, 50, 10))
    glow = glow.filter(ImageFilter.GaussianBlur(40)).resize((W, H))
    return Image.blend(im, glow, 0.35)

# ---------- the Framey screen ----------
SW, SH = 520, 1080
def ball(d, x, y, r=46, look=1, ghost=False):
    if ghost: d.ellipse([x - r, y - r, x + r, y + r], fill=OR + (70,), outline=(120, 50, 10, 90), width=3); return
    d.ellipse([x - r, y - r, x + r, y + r], fill=OR, outline=(120, 50, 10), width=4)
    for ex in (-14, 14):
        d.ellipse([x + ex - 9 + 4 * look, y - 16, x + ex + 9 + 4 * look, y + 2], fill=WHITE); d.ellipse([x + ex - 4 + 7 * look, y - 11, x + ex + 4 + 7 * look, y - 3], fill=INK)
    d.arc([x - 16, y - 2, x + 16, y + 22], 20, 160, fill=(120, 40, 10), width=4)
def set_scene(d, x0, y0, w, h, space=False):
    if space:
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=(14, 16, 48))
        for k in range(40):
            sx = x0 + (k * 97) % w; sy = y0 + (k * 53) % (h * 2 // 3); d.ellipse([sx, sy, sx + 4, sy + 4], fill=(230, 230, 255))
        d.ellipse([x0 + w - 150, y0 + 50, x0 + w - 50, y0 + 150], fill=(90, 140, 255)); d.arc([x0 + w - 175, y0 + 85, x0 + w - 25, y0 + 115], 0, 360, fill=(200, 210, 255), width=4)
    else:
        d.rectangle([x0, y0, x0 + w, y0 + h], fill=(232, 222, 205))
        for k in range(1, 6): d.line([x0 + k * w / 6, y0, x0 + k * w / 6, y0 + h * 0.66], fill=(220, 208, 190), width=3)
    d.rectangle([x0, y0 + h * 0.66, x0 + w, y0 + h], fill=(176, 120, 72))
    for k in range(4): d.line([x0, y0 + h * (0.72 + k * 0.08), x0 + w, y0 + h * (0.72 + k * 0.08)], fill=(150, 98, 56), width=3)
    d.rectangle([x0 + 40, y0 + h * 0.5, x0 + 90, y0 + h * 0.66], fill=(60, 110, 220), outline=(30, 60, 140), width=3)
    d.polygon([(x0 + w - 70, y0 + h * 0.66), (x0 + w - 30, y0 + h * 0.66), (x0 + w - 30, y0 + h * 0.58), (x0 + w - 50, y0 + h * 0.54), (x0 + w - 70, y0 + h * 0.58)], fill=(255, 210, 60), outline=(170, 130, 20))

def screen(st):
    im = Image.new("RGB", (SW, SH), (14, 12, 20)); d = ImageDraw.Draw(im, "RGBA")
    d.text((26, 54), "Movie 1", font=F(30, 800), fill=WHITE); d.text((26, 92), f"{st['n']} frames", font=F(20, 500), fill=(170, 170, 180))
    d.rounded_rectangle([SW - 170, 58, SW - 24, 104], 23, fill=OR); d.text((SW - 97, 81), "Create video", font=F(18, 800), fill=WHITE, anchor="mm")
    vx, vy, vw, vh = 18, 140, SW - 36, 640
    set_scene(d, vx, vy, vw, vh, st.get("space", False))
    if st.get("onion") is not None: ball(d, st["onion"], vy + vh * 0.66 - 46, ghost=True)
    ball(d, st["bx"], vy + vh * 0.66 - 46 - st.get("by", 0), look=1)
    if st.get("hand", 0) > 0:   # a hand shadow reaching in from the right
        hx = vx + vw - 160 * st["hand"]; d.ellipse([hx, vy + 260, hx + 260, vy + 470], fill=(40, 30, 30, 150))
    if st.get("locked"): d.rounded_rectangle([vx + 14, vy + 14, vx + 130, vy + 52], 19, fill=(70, 210, 120)); d.text((vx + 72, vy + 33), "LOCKED", font=F(18, 900), fill=INK, anchor="mm")
    d.rectangle([vx, vy, vx + vw, vy + vh], outline=OR if st.get("rec") else (60, 60, 70), width=4)
    for i, lab in enumerate(("Lock", "Grid", "Timer", "Hands", "Flip")):
        y = vy + 30 + i * 62; on = st.get("rail") == lab
        d.rounded_rectangle([vx + vw - 96, y, vx + vw - 14, y + 46], 23, fill=OR if on else (30, 28, 40, 220))
        d.text((vx + vw - 55, y + 23), lab, font=F(17, 800), fill=WHITE, anchor="mm")
    for i in range(6):   # frame strip
        x = 24 + i * 80; y = 806; filled = i < min(st["n"], 6)
        d.rounded_rectangle([x, y, x + 70, y + 92], 10, fill=(232, 222, 205) if filled else (40, 38, 52), outline=OR if i == min(st["n"], 6) - 1 else (70, 70, 80), width=3)
        if filled: d.ellipse([x + 18 + i * 4, y + 44, x + 42 + i * 4, y + 68], fill=OR)
    r = 62 + 8 * st.get("press", 0); cx, cy = SW / 2, 990
    d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10], outline=WHITE, width=6); d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=OR)
    if st.get("flash", 0) > 0: im = Image.blend(im, Image.new("RGB", im.size, WHITE), 0.7 * st["flash"])
    return im

def phone(scr, tilt=0.0):
    pw, ph = SW + 44, SH + 44
    ph_im = Image.new("RGBA", (pw, ph), (0, 0, 0, 0)); pd = ImageDraw.Draw(ph_im)
    pd.rounded_rectangle([0, 0, pw - 1, ph - 1], 70, fill=(28, 28, 34), outline=(90, 90, 100), width=4)
    m = Image.new("L", scr.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, SW - 1, SH - 1], 52, fill=255)
    ph_im.paste(scr, (22, 22), m); pd.rounded_rectangle([pw / 2 - 70, 34, pw / 2 + 70, 66], 16, fill=(10, 10, 12))
    if abs(tilt) > 0.002:   # fake 3D: shrink one side
        k = tilt * 0.22
        quad = (0, -ph * k, 0, ph * (1 + k), pw, ph * (1 - k * 0.0) , pw, 0) if tilt > 0 else (0, 0, 0, ph, pw, ph * (1 - k), pw, ph * k)
        ph_im = ph_im.transform((pw, ph), Image.QUAD, quad, Image.BICUBIC)
    return ph_im

# ---------- timeline ----------
BPM = 110; BEAT = 60 / BPM
SNAPS = [3.3, 4.4, 5.5, 6.6]
def state(t):
    n = sum(1 for s in SNAPS if t >= s) + (2 if t >= 7 else 0)
    st = {"n": min(14, n + (0 if t < 7 else int((t - 7) * 2))), "bx": 120 + 55 * sum(1 for s in SNAPS if t >= s)}
    for s in SNAPS:
        if 0 <= t - s < 0.25: st["flash"] = 1 - (t - s) / 0.25; st["press"] = 1 - (t - s) / 0.25
    if 2.6 < t < 7.2: st["onion"] = st["bx"] - 55 if st["bx"] > 120 else None
    if 7.6 <= t < 10.4: st["rail"] = "Lock"; st["locked"] = t > 8.2
    if 10.4 <= t < 13.0:
        st["rail"] = "Hands"; st["hand"] = max(0, 1 - abs(t - 11.3) / 0.7)
        if 0 <= t - 12.2 < 0.25: st["flash"] = 1 - (t - 12.2) / 0.25
    if t >= 13.0: st["space"] = t < 15.6 or t >= 15.6
    if 15.6 <= t < 19.0:   # play: the ball rolls across
        st["bx"] = 120 + (t - 15.6) / 3.4 * 300; st["by"] = 40 * abs(math.sin((t - 15.6) * 5)); st["rec"] = True; st["n"] = 14
    return st

CAPS = [  # (start, end, line1, line2, colour)
    (3.0, 7.4, "SNAP.", "Move it a little. Snap again.", WHITE),
    (7.6, 10.4, "LOCK", "Shaky hands? Every frame stays steady.", (70, 210, 120)),
    (10.4, 13.0, "HANDS-FREE", "It snaps when your hand leaves the shot.", YEL),
    (13.0, 15.6, "GREEN SCREEN", "Put your toys anywhere. Even space.", (110, 200, 255)),
    (15.6, 19.0, "HIT PLAY.", "It's alive.", OR),
]

def frame(t):
    im = background(t); d = ImageDraw.Draw(im, "RGBA")
    if t < 2.6:   # hook
        a = spring(t / 0.6); ctext(d, 760, "THIS AD WAS MADE", 92, WHITE, 900, a)
        ctext(d, 880, "100% WITH CODE", 112, OR, 900, spring((t - 0.35) / 0.6))
        ctext(d, 1010, "no editing app. not one frame by hand.", 44, (200, 200, 210), 600, spring((t - 0.8) / 0.6))
        b = spring((t - 1.3) / 0.6)
        if b > 0.05: ctext(d, 1160, "for an app that lets YOU make stop-motion", 40, YEL, 800, b)
    elif t < 19.0:
        k = ease((t - 2.6) / 0.9); tilt = (1 - k) * 1.0
        if 7.6 <= t < 10.4 and t > 8.2: tilt = 0.12 * math.sin((t - 8.2) * 9)   # the phone wobbles, the screen stays LOCKED
        ph = phone(screen(state(t)), tilt)
        s = 0.62 + 0.38 * k; ph = ph.resize((int(ph.width * s), int(ph.height * s)), Image.BICUBIC)
        y = 300 + (1 - k) * 900; jx = 14 * math.sin((t - 8.2) * 31) if 8.2 < t < 10.4 else 0
        sh = Image.new("RGBA", ph.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([0, 0, ph.width - 1, ph.height - 1], 60, fill=(0, 0, 0, 120))
        sh = sh.filter(ImageFilter.GaussianBlur(30)); im.paste(sh, (int((W - ph.width) / 2 + jx + 20), int(y + 40)), sh)
        im.paste(ph, (int((W - ph.width) / 2 + jx), int(y)), ph)
        for s0, s1, l1, l2, col in CAPS:
            if s0 <= t < s1:
                u = t - s0; ctext(d, 170, l1, 110, col, 900, spring(u / 0.5), stroke=6)
                ctext(d, 1640, l2, 50, WHITE, 800, spring((u - 0.2) / 0.5), stroke=5)
        d = ImageDraw.Draw(im, "RGBA")
    else:   # end card
        u = t - 19.0
        for k in range(16):   # orange burst behind the icon
            a = k * math.pi / 8 + u * 0.4; r1 = 230 * ease(u / 0.7); r2 = r1 + 90 * ease(u / 0.7)
            d.line([W / 2 + r1 * math.cos(a), 640 + r1 * math.sin(a), W / 2 + r2 * math.cos(a), 640 + r2 * math.sin(a)], fill=OR + (200,), width=14)
        sz = int(320 * spring(u / 0.6))
        if sz > 10: ic, m = icon(sz); im.paste(ic, (int(W / 2 - sz / 2), int(640 - sz / 2)), m)
        d = ImageDraw.Draw(im, "RGBA")
        ctext(d, 940, "Framey", 150, WHITE, 900, spring((u - 0.3) / 0.6))
        ctext(d, 1060, "the stop-motion app for your phone", 46, (210, 210, 220), 700, spring((u - 0.5) / 0.6))
        ctext(d, 1160, "COMING SOON", 64, YEL, 900, spring((u - 0.7) / 0.6))
        b = spring((u - 1.1) / 0.6)
        if b > 0.05:
            d.rounded_rectangle([140, 1290, W - 140, 1420], 65, fill=OR); ctext(d, 1355, 'Comment "FRAMEY"', 64, WHITE, 900, b)
            ctext(d, 1480, "for early access  ·  follow @frameyapp", 40, WHITE, 700, b)
    # Framey badge on top
    ic, m = icon(56); bw = 56 + 14 + int(d.textlength("Framey", font=F(36, 800))) + 40; x0 = (W - bw) // 2
    d.rounded_rectangle([x0, 48, x0 + bw, 128], 40, fill=(0, 0, 0, 230)); im.paste(ic, (x0 + 12, 60), m); d.text((x0 + 12 + 56 + 14, 88), "Framey", font=F(36, 800), fill=WHITE, anchor="lm")
    return im

def audio(path):
    sr = 24000; n = int((DUR + 0.5) * sr); a = np.zeros(n, np.float32); rng = np.random.default_rng(3)
    def add(t, s, g=1.0):
        i = int(t * sr); e = min(n, i + len(s))
        if i < n: a[i:e] += g * s[: e - i]
    tt = np.arange(int(0.35 * sr)) / sr
    kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
    hat = rng.standard_normal(int(0.05 * sr)) * np.exp(-np.arange(int(0.05 * sr)) / sr * 90)
    click = rng.standard_normal(int(0.06 * sr)) * np.exp(-np.arange(int(0.06 * sr)) / sr * 60)
    def tone(f, d, g=0.2):
        x = np.arange(int(d * sr)) / sr; return np.sin(2 * np.pi * f * x) * np.exp(-x * 4) * g
    bass = [55, 55, 65.4, 49]
    b = 2.6
    while b < 19.0:
        k = int(round((b - 2.6) / BEAT)); add(b, kick, 0.55); add(b + BEAT / 2, hat, 0.12)
        if k % 2 == 0: add(b, tone(bass[(k // 4) % 4], BEAT * 1.8, 0.35))
        b += BEAT
    for s in SNAPS + [12.2]: add(s, click, 0.5)
    for t0 in (0.05, 2.5, 7.55, 10.35, 12.95, 15.55, 18.95):   # whooshes
        L = int(0.4 * sr); add(t0, rng.standard_normal(L) * np.sin(np.linspace(0, np.pi, L)) * 0.12)
    for i, f in enumerate((523, 659, 784, 1047)): add(19.0 + i * 0.12, tone(f, 1.2, 0.18))
    a = np.clip(a / max(1, np.abs(a).max() / 0.9), -1, 1)
    with wave.open(path, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((a * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
        ts = [1.4, 3.35, 5.0, 8.8, 11.3, 14.0, 17.0, 20.5]; sh = Image.new("RGB", (216 * len(ts), 384))
        for i, t in enumerate(ts): sh.paste(frame(t).resize((216, 384)), (216 * i, 0))
        sh.save(OUT + "/ad_preview.jpg"); print("preview"); sys.exit()
    JD = os.environ.get("WORK", "/home/user/work") + "/adjpg"; os.makedirs(JD, exist_ok=True)
    audio(JD + "/a.wav")
    for i in range(int(DUR * FPS)):
        p = f"{JD}/{i:04d}.jpg"
        if not os.path.exists(p): frame(i / FPS).save(p, quality=90)
    print("FRAMES DONE"); sys.exit()
    vv = JD + "/v.mp4"; out = OUT + "/framey-ad-1.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", JD + "/%04d.jpg", "-threads", "1", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", vv], check=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", vv, "-i", JD + "/a.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("ad", out)
