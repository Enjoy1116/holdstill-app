# STOP-MOTION TIP explainer: "ease in & ease out" shown with animated spacing diagrams. Drawn 100% with code.
# Usage: python3 tips.py [--preview]     RESUME-style: writes missing JPEG frames + a.wav into $WORK/tipsjpg, then stops.
import os, sys, math, wave
import numpy as np
from PIL import Image, ImageDraw
import ad
from ad import W, H, FPS, OR, YEL, WHITE, INK, F, spring, ease, ctext, icon, background, ball
OUT = ad.OUT
DUR = 25.0
GREEN, RED, GREY = (70, 210, 120), (238, 52, 64), (120, 112, 140)
X0, X1 = 230, 850; N = 12; MOVE = 12 / 8.0; HOLD = 0.45   # 12 frames per trip, shown at 8 fps (stop-motion feel)
CYC = 2 * (MOVE + HOLD)

def smooth(u): return u * u * (3 - 2 * u)
def positions(eased):
    return [X0 + (smooth(i / (N - 1)) if eased else i / (N - 1)) * (X1 - X0) for i in range(N)]
PA, PB = positions(False), positions(True)

def step_index(t):
    """stop-motion: which of the 12 frames is showing at time t (ping-pong with holds)."""
    c = t % CYC
    if c < HOLD: return 0
    if c < HOLD + MOVE: return min(N - 1, int((c - HOLD) / MOVE * N))
    if c < 2 * HOLD + MOVE: return N - 1
    return max(0, N - 1 - int((c - 2 * HOLD - MOVE) / MOVE * N))

S = 1.25   # lanes are drawn on a layer and scaled up so the toy reads big on a phone
def lane(d, y, pos, t, label=None, col=WHITE, chart=True, appear=1.0, words=None):
    LY = 150; lay = Image.new("RGBA", (W, 360), (0, 0, 0, 0)); g = ImageDraw.Draw(lay, "RGBA")
    i = step_index(t); fwd = (t % CYC) < CYC / 2
    g.rounded_rectangle([X0 - 90, LY - 110, X1 + 90, LY + (190 if chart else 100)], 40, fill=(255, 255, 255, 18), outline=(255, 255, 255, 50), width=3)
    g.line([X0 - 60, LY + 58, X1 + 60, LY + 58], fill=(255, 255, 255, 80), width=4)
    if chart:   # spacing chart: one dot per frame
        ty = LY + 115; g.line([X0, ty, X1, ty], fill=(255, 255, 255, 90), width=4)
        for k, x in enumerate(pos):
            if k / (N - 1) > appear: break
            on = k == i; r = 13 if on else 8
            g.ellipse([x - r, ty - r, x + r, ty + r], fill=col if on else (255, 255, 255, 170))
        if words and appear >= 1:
            for wx, wt, wc in words: g.text((wx, LY + 160), wt, font=F(30, 800), fill=wc, anchor="mm")
    if appear >= 1:   # onion skin: ghosts of the 2 previous frames
        for gg in (2, 1):
            j = i - gg if fwd else i + gg
            if 0 <= j < N: ball(g, pos[j], LY, 56, ghost=True)
    ball(g, pos[i], LY, 56, look=1 if fwd else -1)
    if label:
        f = F(36, 900); tw = g.textlength(label, font=f)
        g.rounded_rectangle([X0 - 64, LY - 96, X0 - 64 + tw + 40, LY - 46], 25, fill=col)
        g.text((X0 - 44, LY - 71), label, font=f, fill=INK, anchor="lm")
    lay = lay.resize((int(W * S), int(360 * S)), Image.BICUBIC)
    im = d._image; im.alpha_composite(lay, (int(W / 2 - W * S / 2), int(y - LY * S))) if im.mode == "RGBA" else im.paste(lay, (int(W / 2 - W * S / 2), int(y - LY * S)), lay)

def title(d, s, u, col=WHITE, y=300, sz=96):
    ctext(d, y, s, sz, col, 900, spring(u / 0.5), stroke=6)

def sub(d, s, u, y=1640, col=WHITE, sz=52):
    ctext(d, y, s, sz, col, 800, spring(u / 0.5), stroke=5)

def frame(t):
    im = background(t); d = ImageDraw.Draw(im, "RGBA")
    if t < 2.6:   # HOOK
        lane(d, 1240, PA, t, chart=False)
        ctext(d, 560, "YOUR STOP-MOTION", 92, WHITE, 900, spring(t / 0.5), stroke=6)
        ctext(d, 690, "LOOKS ROBOTIC?", 118, RED, 900, spring((t - 0.3) / 0.5), stroke=6)
        ctext(d, 840, "1 trick fixes it", 60, YEL, 800, spring((t - 0.9) / 0.5), stroke=5)
    elif t < 7.6:   # MOST PEOPLE
        u = t - 2.6
        title(d, "MOST PEOPLE DO THIS", u)
        ctext(d, 560, f"FRAME {step_index(t) + 1:02d} / {N}", 64, (205, 198, 222), 800, spring((u - 0.4) / 0.5))
        lane(d, 880, PA, t, "ROBOTIC", RED, appear=ease(u / 1.2), words=[(W / 2, "same step every frame", (220, 220, 230))])
        sub(d, "The toy moves the SAME amount", u - 0.6, 1250)
        sub(d, "every single frame.", u - 0.8, 1322)
        sub(d, "So it starts and stops like a robot.", u - 2.2, 1470, YEL, 48)
    elif t < 13.2:   # PROS
        u = t - 7.6
        title(d, "PROS DO THIS", u, GREEN)
        ctext(d, 560, f"FRAME {step_index(t) + 1:02d} / {N}", 64, (205, 198, 222), 800, spring((u - 0.4) / 0.5))
        lane(d, 880, PB, t, "SMOOTH", GREEN, appear=ease(u / 1.2), words=[(X0 + 50, "tiny steps", GREEN), (W / 2, "BIG steps", WHITE), (X1 - 50, "tiny steps", GREEN)])
        sub(d, "Tiny moves at the start and end,", u - 1.6, 1250)
        sub(d, "bigger moves in the middle.", u - 1.8, 1322)
        sub(d, "It's called EASE IN & EASE OUT", u - 2.8, 1470, YEL, 52)
    elif t < 18.6:   # SIDE BY SIDE
        u = t - 13.2
        title(d, "SEE THE DIFFERENCE?", u, YEL)
        lane(d, 680, PA, t, "BEFORE", RED)
        lane(d, 1130, PB, t, "AFTER", GREEN)
        sub(d, "Same 12 frames. Different spacing.", u - 0.8, 1500, WHITE, 50)
        sub(d, "Which one feels alive?", u - 1.6, 1590, YEL, 58)
    elif t < 21.0:   # TRY IT
        u = t - 18.6
        title(d, "TRY IT!", u, OR, 520, 140)
        sub(d, "Next time you animate a toy,", u - 0.3, 760, WHITE, 56)
        sub(d, "start and stop with TINY moves.", u - 0.5, 840, WHITE, 56)
        b = spring((u - 1.0) / 0.5)
        if b > 0.05:
            d.rounded_rectangle([120, 1010, W - 120, 1150], 70, fill=GREEN)
            ctext(d, 1080, 'Comment "SMOOTH"', 66, INK, 900, b)
            ctext(d, 1220, "if you learned something new", 46, (220, 220, 230), 700, b)
        lane(d, 1480, PB, t, chart=False)
    else:   # END CARD
        u = t - 21.0
        for k in range(16):
            a = k * math.pi / 8 + u * 0.4; r1 = 230 * ease(u / 0.7); r2 = r1 + 90 * ease(u / 0.7)
            d.line([W / 2 + r1 * math.cos(a), 640 + r1 * math.sin(a), W / 2 + r2 * math.cos(a), 640 + r2 * math.sin(a)], fill=OR + (200,), width=14)
        sz = int(320 * spring(u / 0.6))
        if sz > 10: ic, m = icon(sz); im.paste(ic, (int(W / 2 - sz / 2), int(640 - sz / 2)), m)
        d = ImageDraw.Draw(im, "RGBA")
        ctext(d, 940, "Framey", 150, WHITE, 900, spring((u - 0.3) / 0.6))
        ctext(d, 1060, "the stop-motion app for your phone", 46, (210, 210, 220), 700, spring((u - 0.5) / 0.6))
        ctext(d, 1160, "COMING SOON", 64, YEL, 900, spring((u - 0.7) / 0.6))
        b = spring((u - 1.0) / 0.6)
        if b > 0.05:
            d.rounded_rectangle([140, 1290, W - 140, 1420], 65, fill=OR); ctext(d, 1355, "FOLLOW FOR MORE TIPS", 60, WHITE, 900, b)
        ctext(d, 1500, "this video was drawn with code", 36, (170, 165, 185), 600, spring((u - 1.3) / 0.6))
    ic, m = icon(56); bw = 56 + 14 + int(d.textlength("Framey", font=F(36, 800))) + 40; x0 = (W - bw) // 2
    d.rounded_rectangle([x0, 48, x0 + bw, 128], 40, fill=(0, 0, 0, 230)); im.paste(ic, (x0 + 12, 60), m); d.text((x0 + 82, 88), "Framey", font=F(36, 800), fill=WHITE, anchor="lm")
    return im

def audio(path):
    sr = 24000; n = int((DUR + 0.5) * sr); a = np.zeros(n, np.float32); rng = np.random.default_rng(11); BEAT = 60 / 96
    def add(t, s, g=1.0):
        i = int(t * sr); e = min(n, i + len(s))
        if 0 <= i < n: a[i:e] += g * s[: e - i]
    tt = np.arange(int(0.35 * sr)) / sr
    kick = np.sin(2 * np.pi * (50 + 120 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
    hat = rng.standard_normal(int(0.04 * sr)) * np.exp(-np.arange(int(0.04 * sr)) / sr * 100)
    tick = rng.standard_normal(int(0.03 * sr)) * np.exp(-np.arange(int(0.03 * sr)) / sr * 140)
    def tone(f, d, g=0.2):
        x = np.arange(int(d * sr)) / sr; return np.sin(2 * np.pi * f * x) * np.exp(-x * 4) * g
    b, k = 0.0, 0
    while b < 21.0:
        add(b, kick, 0.45); add(b + BEAT / 2, hat, 0.08)
        if k % 2 == 0: add(b, tone([65.4, 55, 49, 58.3][(k // 4) % 4], BEAT * 1.8, 0.3))
        if k % 4 == 2: add(b, tone([392, 440, 330, 349][(k // 4) % 4], 0.5, 0.06))
        b += BEAT; k += 1
    last = None   # shutter tick on every stop-motion frame change
    for i in range(int(21.0 * FPS)):
        s = step_index(i / FPS)
        if s != last and i > 0: add(i / FPS, tick, 0.18)
        last = s
    add(0.05, tone(220, 0.5, 0.3)); add(0.35, tone(180, 0.5, 0.25))   # "robot" boop
    for t0 in (2.55, 7.55, 13.15, 18.55, 20.95):
        L = int(0.4 * sr); add(t0, rng.standard_normal(L) * np.sin(np.linspace(0, np.pi, L)) * 0.12)
    for i, f in enumerate((523, 659, 784, 1047)): add(21.0 + i * 0.12, tone(f, 1.2, 0.18))
    a = np.clip(a / max(1, np.abs(a).max() / 0.9), -1, 1)
    with wave.open(path, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((a * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
        ts = [1.6, 5.5, 11.0, 15.0, 20.0, 23.5]; sh = Image.new("RGB", (270 * len(ts), 480))
        for i, t in enumerate(ts): sh.paste(frame(t).resize((270, 480)), (270 * i, 0))
        sh.save(OUT + "/tips_preview.jpg"); print("preview"); sys.exit()
    JD = os.environ.get("WORK", "/tmp") + "/tipsjpg"; os.makedirs(JD, exist_ok=True)
    if not os.path.exists(JD + "/a.wav"): audio(JD + "/a.wav")
    for i in range(int(DUR * FPS)):
        p = f"{JD}/{i:04d}.jpg"
        if not os.path.exists(p): frame(i / FPS).save(p, quality=90)
    print("FRAMES DONE")
