# "Want to make things like this? Use Framey" + how-it-works walkthrough (second half of a promo).
import os, sys, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw
sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:]]
import ad
from ad import W, H, FPS, OR, YEL, WHITE, F, spring, ease, ctext, icon, background, screen, phone
OUT = ad.OUT
STEPS = [  # (start, end, number, title, subtitle, state-maker)
    (2.6, 5.2, "1", "SET UP YOUR TOY", "Any toy. Any table.", lambda u: {"n": 0, "bx": 120}),
    (5.2, 7.8, "2", "SNAP A PHOTO", "Tap the big orange button.", lambda u: {"n": 1 if u > 0.6 else 0, "bx": 120, "flash": max(0, 1 - abs(u - 0.6) / 0.25) if u > 0.6 else 0, "press": max(0, 1 - abs(u - 0.6) / 0.25)}),
    (7.8, 10.4, "3", "MOVE IT A LITTLE", "The ghost shows your last frame.", lambda u: {"n": 1, "bx": 120 + 55 * ease(u / 1.2), "onion": 120}),
    (10.4, 13.0, "4", "SNAP AGAIN. REPEAT.", "LOCK keeps every frame steady.", lambda u: {"n": 1 + min(5, int(u * 2.4)), "bx": 175 + 55 * min(5, int(u * 2.4)), "rail": "Lock", "locked": True,
                                                                                                  "flash": max(0, 1 - ((u * 2.4) % 1) * 4) if u * 2.4 < 5 else 0}),
    (13.0, 16.4, "5", "HIT PLAY", "Your toy comes alive.", lambda u: {"n": 14, "bx": 120 + u / 3.4 * 300, "by": 40 * abs(math.sin(u * 5)), "rec": True}),
]
DUR = 19.6

def frame(t):
    im = background(t); d = ImageDraw.Draw(im, "RGBA")
    if t < 2.6:
        ctext(d, 700, "WANT TO MAKE", 100, WHITE, 900, spring(t / 0.5))
        ctext(d, 820, "THINGS LIKE THIS?", 100, WHITE, 900, spring((t - 0.25) / 0.5))
        s = spring((t - 0.9) / 0.6)
        if s > 0.05:
            sz = int(220 * s); ic, m = icon(sz); im.paste(ic, (int(W / 2 - sz / 2), int(1080 - sz / 2)), m); d = ImageDraw.Draw(im, "RGBA")
            ctext(d, 1290, "Use Framey", 120, OR, 900, s)
    elif t < 16.4:
        for s0, s1, num, title, sub, mk in STEPS:
            if s0 <= t < s1:
                u = t - s0; st = mk(u)
                k = ease((t - 2.6) / 0.8); ph = phone(screen(st), (1 - k) * 1.0)
                sc = 0.66 + 0.34 * k * 0.9; ph = ph.resize((int(ph.width * sc), int(ph.height * sc)), Image.BICUBIC)
                y = 340 + (1 - k) * 900
                im.paste(ph, (int((W - ph.width) / 2), int(y)), ph); d = ImageDraw.Draw(im, "RGBA")
                a = spring(u / 0.45)
                d.ellipse([W / 2 - 330 - 50 * a, 205 - 50 * a, W / 2 - 330 + 50 * a, 205 + 50 * a], fill=OR)
                d.text((W / 2 - 330, 205), num, font=F(int(10 + 60 * a)), fill=WHITE, anchor="mm")
                d.text((W / 2 - 250, 205), title, font=F(int(10 + 62 * a)), fill=WHITE, anchor="lm", stroke_width=5, stroke_fill=(0, 0, 0))
                ctext(d, 1700, sub, 52, YEL, 800, spring((u - 0.2) / 0.5), stroke=5)
                # step dots
                for i in range(5):
                    on = i < int(num); d.ellipse([W / 2 - 110 + i * 50 - 11, 300 - 11, W / 2 - 110 + i * 50 + 11, 300 + 11], fill=OR if on else (80, 70, 90))
    else:
        u = t - 16.4
        for k in range(16):
            a = k * math.pi / 8 + u * 0.4; r1 = 230 * ease(u / 0.7); r2 = r1 + 90 * ease(u / 0.7)
            d.line([W / 2 + r1 * math.cos(a), 640 + r1 * math.sin(a), W / 2 + r2 * math.cos(a), 640 + r2 * math.sin(a)], fill=OR + (200,), width=14)
        sz = int(320 * spring(u / 0.6))
        if sz > 10: ic, m = icon(sz); im.paste(ic, (int(W / 2 - sz / 2), int(640 - sz / 2)), m)
        d = ImageDraw.Draw(im, "RGBA")
        ctext(d, 940, "Framey", 150, WHITE, 900, spring((u - 0.3) / 0.6))
        ctext(d, 1060, "the stop-motion app for your phone", 46, (210, 210, 220), 700, spring((u - 0.5) / 0.6))
        ctext(d, 1160, "COMING SOON", 64, YEL, 900, spring((u - 0.7) / 0.6))
        ctext(d, 1290, "FOLLOW @frameyapp", 62, OR, 900, spring((u - 1.0) / 0.6))
    ic, m = icon(56); bw = 56 + 14 + int(d.textlength("Framey", font=F(36, 800))) + 40; x0 = (W - bw) // 2
    d.rounded_rectangle([x0, 48, x0 + bw, 128], 40, fill=(0, 0, 0, 230)); im.paste(ic, (x0 + 12, 60), m); d.text((x0 + 82, 88), "Framey", font=F(36, 800), fill=WHITE, anchor="lm")
    return im

def audio(path):
    sr = 24000; n = int((DUR + 0.5) * sr); a = np.zeros(n, np.float32); rng = np.random.default_rng(5); BEAT = 60 / 110
    def add(t, s, g=1.0):
        i = int(t * sr); e = min(n, i + len(s))
        if i < n: a[i:e] += g * s[: e - i]
    tt = np.arange(int(0.35 * sr)) / sr
    kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
    hat = rng.standard_normal(int(0.05 * sr)) * np.exp(-np.arange(int(0.05 * sr)) / sr * 90)
    click = rng.standard_normal(int(0.06 * sr)) * np.exp(-np.arange(int(0.06 * sr)) / sr * 60)
    def tone(f, d, g=0.2):
        x = np.arange(int(d * sr)) / sr; return np.sin(2 * np.pi * f * x) * np.exp(-x * 4) * g
    b, k = 0.0, 0
    while b < 16.4:
        add(b, kick, 0.5); add(b + BEAT / 2, hat, 0.1)
        if k % 2 == 0: add(b, tone([55, 65.4, 49, 55][(k // 4) % 4], BEAT * 1.8, 0.3))
        b += BEAT; k += 1
    for s in [5.8] + [10.4 + i / 2.4 for i in range(5)]: add(s, click, 0.5)
    for t0 in (2.55, 5.15, 7.75, 10.35, 12.95, 16.35):
        L = int(0.4 * sr); add(t0, rng.standard_normal(L) * np.sin(np.linspace(0, np.pi, L)) * 0.1)
    for i, f in enumerate((523, 659, 784, 1047)): add(16.4 + i * 0.12, tone(f, 1.2, 0.18))
    a = np.clip(a / max(1, np.abs(a).max() / 0.9), -1, 1)
    with wave.open(path, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((a * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if "--preview" in sys.argv:
        ts = [1.6, 3.5, 6.0, 8.8, 11.5, 14.5, 18.0]; sh = Image.new("RGB", (216 * len(ts), 384))
        for i, t in enumerate(ts): sh.paste(frame(t).resize((216, 384)), (216 * i, 0))
        sh.save(OUT + "/howto_preview.jpg"); print("preview"); sys.exit()
    JD = os.environ.get("WORK", "/tmp") + "/howjpg"; os.makedirs(JD, exist_ok=True)
    for i in range(int(DUR * FPS)): frame(i / FPS).save(f"{JD}/{i:04d}.jpg", quality=90)
    audio(JD + "/a.wav")
    subprocess.run([ad.FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", JD + "/%04d.jpg", "-i", JD + "/a.wav", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT + "/framey-howto.mp4"], check=True)
    print("howto done")
