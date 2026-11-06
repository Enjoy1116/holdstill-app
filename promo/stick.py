# STICKMAN SURVIVAL: narrated, hand-drawn stick-figure episodes for Reels / Shorts (1080x1920).
# Every drawing is redrawn 12 times a second with slightly wobbly lines, like a flipbook drawn
# frame by frame. Each episode: title card -> quick narrated shots with word-by-word captions,
# a ticking clock and "RULE #n" banners -> an A/B choice for the comments -> the Framey ending.
# Narration: one WAV per shot in $VOICE/<episode>_<shot#>.wav (made with the Speko voice tool).
# Usage: python3 stick.py <episode> [...]       python3 stick.py --preview <episode>
import os, sys, json, math, wave, shutil, subprocess, random, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

V = os.environ.get("FRAMEY_DIR", "/mnt/files/v")
D = os.environ.get("WORK", "/home/user/work"); VOICE = os.environ.get("VOICE", V + "/voice")
OUT = os.environ.get("OUTDIR", "/home/user/vout"); FF = os.environ.get("FFMPEG", "ffmpeg")
FB = V + "/Inter.ttf"; ICON = V + "/icon.png"
W, H, FPS, SR = 1080, 1920, 30, 24000
# quality knobs: smoother drawing (24 fps), steadier line, closer camera so the characters fill the frame
DRAW_FPS = int(os.environ.get("DRAW_FPS", 24)); JIT = float(os.environ.get("JITTER", 1.5)); CAM = float(os.environ.get("CAM_ZOOM", 1.0))
OR = (254, 97, 0); YEL = (255, 214, 10); WHITE = (255, 255, 255); GREY = (200, 200, 210); RED = (228, 40, 40)
CHALK = (238, 238, 232); ZOMB = (130, 214, 96)
EPS = json.load(open(V + "/stick.json"))


def font(size):
    f = ImageFont.truetype(FB, size)
    try:
        ax = f.get_variation_axes(); f.set_variation_by_axes([32, 900] if len(ax) == 2 else [900])
    except Exception:
        pass
    return f

_F = {}
def F(size):
    if size not in _F: _F[size] = font(size)
    return _F[size]


# ---------------------------------------------------------------- hand-drawn primitives
class Pen:
    """Draws with a slightly shaky hand; the shake changes on every drawn frame (the 'boil')."""
    def __init__(self, d, seed, j=3.0):
        self.d = d; self.r = random.Random(seed); self.j = j
    def p(self, x, y):
        return (x + self.r.uniform(-self.j, self.j), y + self.r.uniform(-self.j, self.j))
    def line(self, pts, col=CHALK, w=10):
        q = [self.p(x, y) for x, y in pts]
        self.d.line(q, fill=col, width=w, joint="curve")
        for x, y in (q[0], q[-1]): self.d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=col)
    def circle(self, cx, cy, r, col=CHALK, w=10, fill=None):
        cx, cy = self.p(cx, cy); rr = r + self.r.uniform(-self.j, self.j) * 0.6
        self.d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=col, width=w, fill=fill)
    def rect(self, x0, y0, x1, y1, col=CHALK, w=10, fill=None):
        if fill is not None: self.d.rectangle([x0, y0, x1, y1], fill=fill)
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], col, w)


def rot(a, L):  # angle in degrees, 0 = straight down, positive = toward +x
    r = math.radians(a); return (math.sin(r) * L, math.cos(r) * L)


OUTLINE = (14, 14, 20); HOOD = (254, 97, 0); HOOD_D = (190, 64, 0); SKIN = (246, 244, 236)
ZSKIN, ZSHIRT, ZLINE = (124, 196, 92), (86, 96, 120), (28, 52, 22)

def _curve(a, j, b, n=10):
    """Smooth curve from a to b that passes through the joint j."""
    c = (2 * j[0] - (a[0] + b[0]) / 2, 2 * j[1] - (a[1] + b[1]) / 2)
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]) for t in (i / n for i in range(n + 1))]

def _limb(d, pts, w0, w1, col, out=OUTLINE, ow=5):
    """Tapered stroke with round caps and a dark outline."""
    n = len(pts) - 1
    for pas, extra, c in ((0, ow, out), (1, 0, col)):
        for i in range(n):
            w = w0 + (w1 - w0) * i / n + extra * 2
            d.line([pts[i], pts[i + 1]], fill=c, width=max(1, int(w)))
            x, y = pts[i + 1]; r = w / 2; d.ellipse([x - r, y - r, x + r, y + r], fill=c)
        x, y = pts[0]; r = (w0 + extra * 2) / 2; d.ellipse([x - r, y - r, x + r, y + r], fill=c)

def stick(pen, x, y, L, pose, col=CHALK, face=1, w=11, eyes=None, kind=None, expr=None, look=None):
    """A clean, outlined stick character standing on (x, y), drawn at 2x and smoothed.
    pose: lean, tilt, drop, arms [(shoulder, elbow)]*2, legs [(hip, knee)]*2 in degrees (0 = down)."""
    kind = kind or ("zombie" if col == ZOMB else "you")
    expr = expr or ("zombie" if kind == "zombie" else "worried")
    if look is None: look = face * 0.5
    jit = pen.j * 0.45; rj = lambda p: (p[0] + pen.r.uniform(-jit, jit), p[1] + pen.r.uniform(-jit, jit))
    lean = pose.get("lean", 0) * face; hip = (x, y - 0.9 * L - pose.get("drop", 0) * L)
    legs = []
    for hp, kn in pose["legs"]:
        dx, dy = rot(hp * face, 0.45 * L); k = (hip[0] + dx, hip[1] + dy)
        dx, dy = rot((hp + kn) * face, 0.45 * L); legs.append((hip, rj(k), rj((k[0] + dx, k[1] + dy))))
    dx, dy = rot(180 + lean, 0.62 * L); neck = rj((hip[0] + dx, hip[1] + dy)); sh = (neck[0] - dx * 0.12, neck[1] - dy * 0.12)
    arms = []
    for s_, e_ in pose["arms"]:
        dx, dy = rot(s_ * face, 0.33 * L); el = (sh[0] + dx, sh[1] + dy)
        dx, dy = rot((s_ + e_) * face, 0.31 * L); arms.append((sh, rj(el), rj((el[0] + dx, el[1] + dy))))
    hr = 0.19 * L; head = (neck[0] + pose.get("tilt", 0) * face * L * 0.05, neck[1] - hr * 0.95)
    # 2x canvas around the figure
    pts = [p for c in legs + arms for p in c] + [head, neck, hip]
    bx0 = min(p[0] for p in pts) - hr * 1.6; by0 = min(p[1] for p in pts) - hr * 1.6
    bx1 = max(p[0] for p in pts) + hr * 1.6; by1 = max(max(p[1] for p in pts), y) + hr * 1.2
    S2 = 2; lw, lh = int((bx1 - bx0) * S2) + 2, int((by1 - by0) * S2) + 2
    if lw <= 2 or lh <= 2: return
    lay = Image.new("RGBA", (lw, lh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    T = lambda p: ((p[0] - bx0) * S2, (p[1] - by0) * S2)
    W2 = w * S2 * 1.15; ow = max(3, w * 0.45) * S2
    # soft ground shadow
    if pose.get("drop", 0) >= 0 and kind != "hang":
        gx, gy = T((x, y)); d.ellipse([gx - L * 0.32 * S2, gy - L * 0.035 * S2, gx + L * 0.32 * S2, gy + L * 0.035 * S2], fill=(0, 0, 0, 90))
    limb_c = SKIN if kind == "you" else ZSKIN
    if kind == "zombie" and expr != "dance": limb_c = ZSKIN
    order = [1, 0] if face > 0 else [0, 1]
    for i in order:  # back leg first
        a_, k_, f_ = legs[i]; _limb(d, [T(p) for p in _curve(a_, k_, f_)], W2 * 1.05, W2 * 0.9, (78, 112, 178) if kind == "you" else (96, 106, 132), ow=ow)
        fx, fy = T(f_); d.ellipse([fx - W2 * 0.9 + face * W2 * 0.5, fy - W2 * 0.55, fx + W2 * 0.9 + face * W2 * 0.5, fy + W2 * 0.45], fill=OUTLINE)
    a_, k_, f_ = arms[order[0]]; _limb(d, [T(p) for p in _curve(a_, k_, f_)], W2 * 0.95, W2 * 0.75, limb_c, ow=ow)
    hx_, hy_ = T(f_); d.ellipse([hx_ - W2 * 0.7, hy_ - W2 * 0.7, hx_ + W2 * 0.7, hy_ + W2 * 0.7], fill=limb_c, outline=OUTLINE, width=int(ow * 0.8))
    # torso: hoodie for you, torn shirt for zombies
    tc, td = (HOOD, HOOD_D) if kind == "you" else (ZSHIRT, (60, 66, 86))
    _limb(d, [T(p) for p in _curve(hip, ((hip[0] + neck[0]) / 2, (hip[1] + neck[1]) / 2), neck, 4)], W2 * 2.6, W2 * 2.3, tc, ow=ow)
    if kind == "zombie":
        mx, my = T(((hip[0] + neck[0]) / 2, (hip[1] + neck[1]) / 2))
        d.polygon([(mx - W2, my + W2 * 0.4), (mx - W2 * 0.3, my - W2 * 0.2), (mx + W2 * 0.2, my + W2 * 0.6)], fill=td)
    a_, k_, f_ = arms[order[1]]; _limb(d, [T(p) for p in _curve(a_, k_, f_)], W2 * 0.95, W2 * 0.75, limb_c, ow=ow)
    hx_, hy_ = T(f_); d.ellipse([hx_ - W2 * 0.7, hy_ - W2 * 0.7, hx_ + W2 * 0.7, hy_ + W2 * 0.7], fill=limb_c, outline=OUTLINE, width=int(ow * 0.8))
    # head
    cx, cy = T(head); R = hr * S2
    if kind == "you":  # hood behind the head
        d.ellipse([cx - R * 1.18, cy - R * 1.15, cx + R * 1.18, cy + R * 1.2], fill=HOOD_D, outline=OUTLINE, width=int(ow))
    hc = SKIN if kind == "you" else ZSKIN
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=hc, outline=OUTLINE, width=int(ow))
    d.ellipse([cx - R * 0.6, cy - R * 0.75, cx - R * 0.05, cy - R * 0.3], fill=tuple(min(255, c + 18) for c in hc))  # shine
    ex = R * 0.36; ey = cy - R * 0.08; lk = look * R * 0.12
    if kind == "zombie":
        glow = eyes[0] if eyes else (255, 70, 60)
        for sx in (-1, 1):
            X = cx + sx * ex + lk; d.ellipse([X - R * 0.2, ey - R * 0.16, X + R * 0.2, ey + R * 0.2], fill=(250, 250, 230), outline=ZLINE, width=int(ow * 0.6))
            d.ellipse([X - R * 0.09 + lk * 0.5, ey - R * 0.02, X + R * 0.09 + lk * 0.5, ey + R * 0.16], fill=glow)
            d.chord([X - R * 0.23, ey - R * 0.22, X + R * 0.23, ey + R * 0.22], 180, 360, fill=hc)  # droopy lid
            d.line([X - R * 0.23, ey, X + R * 0.23, ey], fill=ZLINE, width=int(ow * 0.6))
        my = cy + R * 0.45; mw = R * 0.42; zz = [(cx - mw + i * mw / 3, my + (R * 0.1 if i % 2 else 0)) for i in range(7)]
        d.polygon(zz + [(cx + mw, my + R * 0.22), (cx - mw, my + R * 0.22)], fill=(60, 20, 20)); d.line(zz, fill=ZLINE, width=int(ow * 0.6))
    else:
        big = expr in ("scared",)
        for sx in (-1, 1):
            X = cx + sx * ex; ry = R * (0.26 if big else 0.21)
            d.ellipse([X - R * 0.17, ey - ry, X + R * 0.17, ey + ry], fill=WHITE, outline=OUTLINE, width=int(ow * 0.55))
            pr = R * (0.07 if big else 0.09); d.ellipse([X - pr + lk, ey - pr + R * 0.02, X + pr + lk, ey + pr + R * 0.02], fill=OUTLINE)
            by = ey - ry - R * 0.12; tilt = {"worried": 0.14, "scared": 0.2, "strain": -0.12, "happy": 0.0}.get(expr, 0.0) * R
            yo, yi = by + tilt, by - tilt   # outer / inner brow end (worried: inner end raised)
            p1, p2 = ((X - R * 0.18, yo), (X + R * 0.18, yi)) if sx < 0 else ((X - R * 0.18, yi), (X + R * 0.18, yo))
            d.line([p1, p2], fill=OUTLINE, width=int(ow * 0.7))
        my = cy + R * 0.48
        if expr == "scared": d.ellipse([cx - R * 0.13, my - R * 0.15, cx + R * 0.13, my + R * 0.17], fill=(60, 20, 30), outline=OUTLINE, width=int(ow * 0.5))
        elif expr == "happy": d.arc([cx - R * 0.32, my - R * 0.3, cx + R * 0.32, my + R * 0.16], 15, 165, fill=OUTLINE, width=int(ow * 0.8))
        elif expr == "strain": d.line([cx - R * 0.25, my, cx + R * 0.25, my], fill=OUTLINE, width=int(ow * 0.8))
        else: d.arc([cx - R * 0.24, my - R * 0.02, cx + R * 0.24, my + R * 0.3], 200, 340, fill=OUTLINE, width=int(ow * 0.7))
        if expr in ("worried", "scared"):  # sweat drop
            sx2, sy2 = cx + R * 0.82, cy - R * 0.35; d.ellipse([sx2 - R * 0.08, sy2, sx2 + R * 0.08, sy2 + R * 0.2], fill=(140, 200, 255), outline=OUTLINE, width=int(ow * 0.4))
    small = lay.resize((max(1, lw // S2), max(1, lh // S2)), Image.LANCZOS)
    pen.im.paste(small, (int(bx0), int(by0)), small)


def pose_walk(ph, zombie=False):
    s = math.sin(ph * 2 * math.pi)
    legs = [(18 * s, 10 + 8 * max(0, -s)), (-18 * s, 10 + 8 * max(0, s))]
    if zombie: return {"lean": 8, "tilt": 2, "arms": [(-95, -8), (-100, 4)], "legs": legs}
    return {"lean": 3, "arms": [(-22 * s, 18), (22 * s, 18)], "legs": legs}

def pose_run(ph):
    s = math.sin(ph * 2 * math.pi)
    return {"lean": 16, "arms": [(-55 * s, 70), (55 * s, 70)], "legs": [(35 * s, 25 + 40 * max(0, -s)), (-35 * s, 25 + 40 * max(0, s))]}

STAND = {"arms": [(12, 6), (-12, -6)], "legs": [(8, 0), (-8, 0)]}
SCARED = {"lean": -6, "arms": [(150, 25), (-150, -25)], "legs": [(14, 0), (-14, 0)]}
SIT = {"drop": -0.32, "arms": [(25, -30), (-15, 30)], "legs": [(85, -85), (80, -80)]}
CLIMB = {"lean": 0, "arms": [(175, 10), (160, 20)], "legs": [(-30, 60), (20, 10)]}
HANG = {"arms": [(178, 0), (172, 0)], "legs": [(10, 15), (-15, 20)]}
def pose_dance(ph):
    s = math.sin(ph * 2 * math.pi)
    return {"lean": 10 * s, "arms": [(140 + 30 * s, 40), (-140 + 30 * s, -40)], "legs": [(15 + 10 * s, 0), (-15 + 10 * s, 0)]}
def pose_wave(ph):
    s = math.sin(ph * 2 * math.pi)
    return {"arms": [(165 + 15 * s, 20 * s), (-160 - 15 * s, -20 * s)], "legs": [(10, 0), (-10, 0)]}


# ---------------------------------------------------------------- scenes (drawn at 12 fps)
def sky(im, top=(10, 14, 34), bot=(34, 26, 52)):
    d = ImageDraw.Draw(im)
    for y in range(0, H, 16):
        k = y / H; d.rectangle([0, y, W, y + 16], fill=tuple(int(a + (b - a) * k) for a, b in zip(top, bot)))
    return d

def skyline(pen, y0, tick, lit=0.35, seed=4):
    r = random.Random(seed); x = -20
    while x < W:
        bw = r.randint(90, 180); bh = r.randint(260, 620)
        pen.d.rectangle([x, y0 - bh, x + bw, y0], fill=(16, 16, 24)); pen.line([(x, y0), (x, y0 - bh), (x + bw, y0 - bh), (x + bw, y0)], (70, 70, 90), 5)
        for wy in range(y0 - bh + 30, y0 - 30, 60):
            for wx in range(x + 18, x + bw - 30, 42):
                if r.random() < lit: pen.d.rectangle([wx, wy, wx + 18, wy + 24], fill=(255, 210, 110))
        x += bw + r.randint(4, 30)

def moon(pen, x, y, r=70):
    pen.d.ellipse([x - r * 1.8, y - r * 1.8, x + r * 1.8, y + r * 1.8], fill=(40, 40, 70)); pen.circle(x, y, r, (250, 245, 220), 8, fill=(240, 236, 210))

def zombie_line(pen, n, y, L, tick, x0, dx, turn=False, dance=False, seed=7):
    r = random.Random(seed)
    for i in range(n):
        x = x0 + i * dx + r.uniform(-30, 30); ph = tick / 10 + i * 0.37
        if dance: p = pose_dance(tick / 6 + (i % 2) * 0.5); stick(pen, x, y, L, p, ZOMB, face=1, w=9, eyes=((255, 60, 60), 0))
        elif turn: stick(pen, x, y, L, {"tilt": 3, "arms": [(-95, -8), (-100, 4)], "legs": [(8, 0), (-8, 0)]}, ZOMB, face=1, w=9, eyes=((255, 60, 60), 0))
        else: stick(pen, x + (tick * 2.2) % 40, y, L, pose_walk(ph, True), ZOMB, face=1 if i % 2 else -1, w=9)

def sc_title(im, pen, u, st, tick):
    sky(im); moon(pen, 820, 380, 80); skyline(pen, 1500, tick, 0.25)
    pen.d.rectangle([0, 1500, W, H], fill=(14, 12, 18)); pen.line([(0, 1500), (W, 1500)], (90, 90, 110), 6)
    zombie_line(pen, 5, 1700, 150, tick, 90, 210)

def sc_alert(im, pen, u, st, tick):
    d = sky(im, (18, 6, 8), (40, 10, 12))
    bz = 10 if (st.get("buzz", True) and u < 1.6 and int(tick) % 2 == 0) else 0; jx = pen.r.uniform(-bz, bz)
    x0, y0, x1, y1 = 260 + jx, 500, 820 + jx, 1250
    d.rounded_rectangle([x0 - 30, y0 - 30, x1 + 30, y1 + 30], 90, fill=(60, 10, 10))
    d.rounded_rectangle([x0, y0, x1, y1], 70, fill=(22, 22, 26), outline=(200, 200, 210), width=10)
    d.rounded_rectangle([x0 + 30, y0 + 60, x1 - 30, y1 - 60], 30, fill=(120, 16, 16) if st.get("red", True) else (16, 40, 90))
    cx = (x0 + x1) / 2
    pen.line([(cx - 90, 820), (cx, 660), (cx + 90, 820), (cx - 90, 820)], WHITE, 12); pen.line([(cx, 710), (cx, 770)], WHITE, 12); pen.d.ellipse([cx - 8, 785, cx + 8, 801], fill=WHITE)
    for i, ln in enumerate(st.get("screen", ["EMERGENCY ALERT"])):
        f = F(54 if i == 0 else 40); tw = d.textlength(ln, font=f); d.text((cx - tw / 2, 870 + i * 70), ln, font=f, fill=WHITE)
    if bz:
        for k in (1, 2):
            pen.line([(x0 - 40 * k, 700), (x0 - 60 * k, 760), (x0 - 40 * k, 820)], (255, 120, 120), 7)
            pen.line([(x1 + 40 * k, 700), (x1 + 60 * k, 760), (x1 + 40 * k, 820)], (255, 120, 120), 7)

def sc_window(im, pen, u, st, tick):
    d = sky(im, (12, 12, 20), (22, 20, 30)); x0, y0, x1, y1 = 140, 420, 940, 1420
    win = Image.new("RGB", (x1 - x0, y1 - y0)); wd = ImageDraw.Draw(win)
    for y in range(0, y1 - y0, 12):
        k = y / (y1 - y0); wd.rectangle([0, y, x1 - x0, y + 12], fill=(int(14 + 24 * k), int(20 + 16 * k), int(50 + 10 * k)))
    im.paste(win, (x0, y0)); moon(pen, 760, 560, 55)
    pen.d.rectangle([x0, 1240, x1, y1], fill=(30, 28, 36)); pen.line([(x0, 1240), (x1, 1240)], (110, 110, 130), 6)
    pen.d.rectangle([x0 + 60, 1130, x0 + 70, 1240], fill=(90, 90, 100)); pen.d.ellipse([x0 + 40, 1110, x0 + 90, 1140], fill=(255, 220, 120))
    zombie_line(pen, st.get("zombies", 4), 1335, 200, tick, x0 + 100, 200, turn=st.get("turn", False) and u > 0.8, dance=st.get("dance", False))
    pen.d.rectangle([0, 0, W, y0], fill=(18, 16, 24)); pen.d.rectangle([0, y1, W, H], fill=(18, 16, 24))
    pen.d.rectangle([0, y0, x0, y1], fill=(18, 16, 24)); pen.d.rectangle([x1, y0, W, y1], fill=(18, 16, 24))
    pen.rect(x0, y0, x1, y1, (150, 120, 90), 22); pen.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], (150, 120, 90), 16)
    pen.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], (150, 120, 90), 16)

def sc_room(im, pen, u, st, tick):
    d = sky(im, (26, 22, 32), (40, 32, 40)); off = st.get("lights_off") and u > 0.7
    d.rectangle([0, 1480, W, H], fill=(48, 36, 32)); pen.line([(0, 1480), (W, 1480)], (110, 90, 80), 6)
    pen.rect(140, 1260, 700, 1480, CHALK, 10, fill=(70, 50, 90)); pen.rect(140, 1180, 260, 1260, CHALK, 8, fill=(220, 220, 230))
    if not off:
        d.ellipse([720, 900, 1060, 1240], fill=(80, 64, 40)); pen.line([(890, 1480), (890, 1150)], CHALK, 8); pen.line([(840, 1150), (940, 1150), (910, 1080), (870, 1080), (840, 1150)], (255, 220, 120), 8)
    pose = SCARED if st.get("scared") else SIT
    jx = pen.r.uniform(-7, 7) if st.get("shake") else 0
    stick(pen, 360 + jx, 1480, 380, pose, CHALK, face=1, w=12, expr="scared" if (st.get("growl") or st.get("scared")) else "worried", look=1 if st.get("growl") else 0.6)
    if st.get("growl") and u > 0.3:
        for i in range(3):
            a = (tick + i * 4) % 12 / 12; pen.circle(560, 1090, 30 + a * 110, (255, 214, 10), 5)
    if off:
        dark = Image.new("RGBA", (W, H), (0, 0, 10, 175)); im.paste(dark, (0, 0), dark)

def sc_door(im, pen, u, st, tick):
    d = sky(im, (20, 18, 26), (30, 26, 34)); kn = st.get("knock") and (int(tick) % 8 < 2) and u > 0.2
    jx = pen.r.uniform(-9, 9) if kn or st.get("rattle") else 0
    d.rectangle([0, 1560, W, H], fill=(36, 30, 30))
    pen.rect(300 + jx, 430, 780 + jx, 1560, (170, 130, 90), 14, fill=(84, 56, 38)); pen.rect(360 + jx, 520, 720 + jx, 940, (140, 104, 70), 8); pen.rect(360 + jx, 1020, 720 + jx, 1460, (140, 104, 70), 8)
    pen.circle(700 + jx, 1010, 26, (230, 190, 90), 8, fill=(200, 160, 70)); pen.circle(540 + jx, 640, 20, (200, 200, 210), 6, fill=(10, 10, 14))
    if st.get("locked"): pen.rect(640 + jx, 1060, 760 + jx, 1180, (210, 210, 220), 10, fill=(60, 60, 70)); pen.line([(660 + jx, 1060), (660 + jx, 1010), (740 + jx, 1010), (740 + jx, 1060)], (210, 210, 220), 10)
    d.rectangle([300, 1548, 780, 1560], fill=(255, 220, 140))
    if st.get("feet"):
        for fx in (470, 590): d.ellipse([fx - 40, 1548, fx + 40, 1566], fill=(10, 10, 12))
    if kn:
        for i, (tx, ty) in enumerate(((230, 700), (850, 820), (200, 1000))):
            f = F(70); d.text((tx - 80, ty), "KNOCK", font=f, fill=YEL, stroke_width=6, stroke_fill=(0, 0, 0))

def sc_hallway(im, pen, u, st, tick):
    d = sky(im, (14, 14, 18), (24, 22, 28)); fl = (int(tick) % 7 in (0, 3)) and st.get("flicker", True)
    vx, vy = W / 2, 820
    for a, b in (((0, 0), (vx - 120, vy - 140)), ((W, 0), (vx + 120, vy - 140)), ((0, H), (vx - 120, vy + 220)), ((W, H), (vx + 120, vy + 220))):
        pen.line([a, b], (90, 90, 110), 8)
    pen.rect(vx - 120, vy - 140, vx + 120, vy + 220, (90, 90, 110), 8, fill=(8, 8, 12))
    if not fl:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g); gd.polygon([(vx - 60, 300), (vx + 60, 300), (vx + 360, 1500), (vx - 360, 1500)], fill=(255, 230, 160, 40)); im.paste(g, (0, 0), g)
        pen.line([(vx - 70, 300), (vx + 70, 300)], (255, 240, 190), 14)
    stick(pen, vx, 1700, 520, pose_walk(tick / 14), CHALK, face=1, w=13, expr="worried", look=-0.6)
    if st.get("zombie_far"): stick(pen, vx + 40, vy + 210, 110, pose_walk(tick / 10, True), ZOMB, face=-1, w=6, eyes=((255, 60, 60), 0))

def sc_stairs(im, pen, u, st, tick):
    d = sky(im, (16, 16, 22), (26, 24, 30))
    for k in range(6):
        y = 1900 - k * 300 + (tick * 18) % 300; x = 140 if k % 2 else 940
        pen.line([(x, y), (1080 - x, y - 300)], (120, 120, 140), 10); pen.line([(x, y + 20), (1080 - x, y - 280)], (60, 60, 80), 6)
    a, b = st.get("floors", [3, 12]); fl = int(a + (b - a) * min(1, u / max(0.1, st["_dur"] - 0.3)))
    f = F(300); txt = str(fl); tw = d.textlength(txt, font=f); d.text((W / 2 - tw / 2 - 260, 420), txt, font=f, fill=(255, 255, 255, 60), stroke_width=4, stroke_fill=(90, 90, 110))
    d.text((W / 2 - 260 - 20, 380), "FLOOR", font=F(60), fill=GREY)
    stick(pen, 640, 1300, 420, pose_run(tick / 5), CHALK, face=1, w=13, expr="scared" if st.get("below") else "strain", look=-1 if st.get("below") else 1)
    if st.get("below"):
        for i in range(2): stick(pen, 230 + i * 120, 1880, 260, pose_walk(tick / 8 + i * 0.4, True), ZOMB, face=1, w=8, eyes=((255, 60, 60), 0))

def sc_roof(im, pen, u, st, tick):
    sky(im, (8, 10, 28), (30, 24, 54)); moon(pen, 900, 300, 55); skyline(pen, 1500, tick, 0.05, seed=9)
    pen.d.rectangle([0, 1380, W, H], fill=(40, 40, 48)); pen.line([(0, 1380), (W, 1380)], (130, 130, 150), 10)
    pen.rect(760, 1060, 960, 1380, (150, 150, 170), 10, fill=(60, 64, 76)); pen.line([(780, 1380), (780, 1440)], (150, 150, 170), 8); pen.line([(940, 1380), (940, 1440)], (150, 150, 170), 8)
    hel = st.get("heli")
    if hel:
        hx = 260 + 360 * min(1, u / 1.5) if hel == "arrive" else 620; hy = 400
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        sx = hx + 160 * math.sin(tick / 6); gd.polygon([(hx - 20, hy + 60), (hx + 20, hy + 60), (sx + 220, 1400), (sx - 220, 1400)], fill=(255, 250, 200, 45)); im.paste(g, (0, 0), g)
        dd = pen.d; O = OUTLINE                                   # helicopter: tail, body, window, skids, rotor
        dd.polygon([(hx + 60, hy - 20), (hx + 280, hy - 40), (hx + 290, hy - 10), (hx + 60, hy + 25)], fill=(200, 60, 40), outline=O, width=7)
        dd.ellipse([hx + 262, hy - 80, hx + 312, hy - 30], outline=O, width=6, fill=(230, 230, 230))
        dd.ellipse([hx - 140, hy - 75, hx + 110, hy + 85], fill=(222, 70, 46), outline=O, width=9)
        dd.chord([hx - 125, hy - 60, hx + 10, hy + 50], 90, 270, fill=(150, 210, 240), outline=O, width=6)
        for sx in (-90, 40): dd.line([(hx + sx, hy + 75), (hx + sx, hy + 110)], fill=O, width=8)
        dd.line([(hx - 140, hy + 110), (hx + 90, hy + 110)], fill=O, width=10)
        dd.line([(hx - 15, hy - 75), (hx - 15, hy - 100)], fill=O, width=10); bl = 280 * math.cos(tick * 1.7)
        dd.line([(hx - 15 - bl, hy - 102), (hx - 15 + bl, hy - 102)], fill=(40, 40, 46), width=10)
        if st.get("rope"): pen.line([(hx - 10, hy + 70), (hx - 10, 1720 - 220 * min(1, u / 2) - 2.16 * 300)], (230, 200, 140), 6)
    pose = {"climb": CLIMB, "wave": pose_wave(tick / 5), "hang": HANG, "scared": SCARED}.get(st.get("you", "stand"), STAND)
    ex_ = {"climb": "strain", "wave": "happy", "hang": "scared", "scared": "scared"}.get(st.get("you"), "worried")
    if st.get("you") == "hang": stick(pen, 610, 1720 - 220 * min(1, u / 2), 300, pose, CHALK, face=1, w=12, expr=ex_, look=0)
    else: stick(pen, 380, 1380, 300, pose, CHALK, face=1, w=12, expr=ex_, look=1 if st.get("heli") else 0.4)
    if st.get("rattle"):
        jx = pen.r.uniform(-10, 10); pen.rect(60 + jx, 980, 260 + jx, 1380, (170, 130, 90), 12, fill=(84, 56, 38))
        if int(tick) % 4 < 2: pen.d.text((40, 900), "BANG", font=F(70), fill=YEL, stroke_width=6, stroke_fill=(0, 0, 0))

def sc_choice(im, pen, u, st, tick):
    sky(im, (12, 10, 24), (30, 16, 30))

SCENES = {"title": sc_title, "alert": sc_alert, "window": sc_window, "room": sc_room, "door": sc_door, "hallway": sc_hallway,
          "stairs": sc_stairs, "roof": sc_roof, "choice": sc_choice}


# ---------------------------------------------------------------- text overlays
_tl = {}
def text_line(parts, size, stroke=8):
    key = (json.dumps(parts), size, stroke)
    if key in _tl: return _tl[key]
    f = F(size); d0 = ImageDraw.Draw(Image.new("RGB", (1, 1))); tw = int(sum(d0.textlength(t, font=f) for t, _ in parts)) + stroke * 2 + 4
    im = Image.new("RGBA", (max(1, tw), int(size * 1.3) + stroke * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = stroke
    for t, c in parts:
        d.text((x, stroke), t, font=f, fill=c, stroke_width=stroke, stroke_fill=(0, 0, 0)); x += d0.textlength(t, font=f)
    _tl[key] = im; return im

def paste_c(base, L, cy, s=1.0):
    if L.width * s > W - 60: s = (W - 60) / L.width          # never run off the screen
    if s != 1.0: L = L.resize((max(1, int(L.width * s)), max(1, int(L.height * s))), Image.LANCZOS)
    base.paste(L, (int((W - L.width) / 2), int(cy - L.height / 2)), L)

def spring(age, dur=0.18):
    if age < 0: return 0
    k = min(1, age / dur); return (0.7 + 0.3 * k) + (0.15 * math.sin(k * math.pi) if k < 1 else 0)

_badge = []
def badge(im):
    if not _badge:
        ic = Image.open(ICON).convert("RGB").resize((76, 76), Image.LANCZOS)
        m = Image.new("L", ic.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 75, 75], 18, fill=255); ic = ic.convert("RGBA"); ic.putalpha(m)
        f = F(48); tw = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength("Framey", font=f))
        bw, bh = 12 + 76 + 16 + tw + 30, 100
        b = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
        d.rounded_rectangle([0, 0, bw - 1, bh - 1], bh // 2, fill=(0, 0, 0, 150)); b.paste(ic, (12, 12), ic); d.text((104, 18), "Framey", font=f, fill=WHITE)
        _badge.append(b)
    b = _badge[0]; im.paste(b, ((W - b.width) // 2, 64), b)

def words_of(say, key):
    ks = {k.lower() for k in re.findall(r"[\w']+", key or "")}
    return [(w, re.sub(r"[^\w']", "", w).lower() in ks) for w in say.split()]

def chunks(words):
    out, cur = [], []
    for i, (w, k) in enumerate(words):
        if cur and len(" ".join(x[1] for x in cur + [(i, w, k)])) > 15: out.append(cur); cur = []
        cur.append((i, w, k))
        if len(cur) >= 3 or w[-1] in ".,?!:": out.append(cur); cur = []
    if cur: out.append(cur)
    return out


# ---------------------------------------------------------------- sound
def tone(f0, f1, dur, amp=0.5, decay=5.0):
    t = np.arange(int(dur * SR)) / SR; f = np.linspace(f0, f1, len(t))
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * decay / max(dur, 1e-3))
def noise(dur, amp=0.5, smooth=1, env="decay", seed=1):
    n = np.random.default_rng(seed).uniform(-1, 1, int(dur * SR))
    if smooth > 1: n = np.convolve(n, np.ones(smooth) / smooth, "same") * math.sqrt(smooth)
    e = np.exp(-np.linspace(0, 7, len(n))) if env == "decay" else np.sin(np.linspace(0, np.pi, len(n)))
    return amp * n * e
def buzz(dur=1.4):
    t = np.arange(int(dur * SR)) / SR; on = (np.floor(t * 5) % 2 == 0)
    return 0.22 * np.sign(np.sin(2 * np.pi * 170 * t)) * on
def knock():
    o = np.zeros(int(1.0 * SR))
    for at in (0.0, 0.28, 0.56):
        s = tone(110, 70, 0.12, 0.9); nz = noise(0.05, 0.4, 4, seed=int(at * 10)); s[: len(nz)] += nz; i = int(at * SR); o[i:i + len(s)] += s
    return o
def heli(dur=2.5):
    t = np.arange(int(dur * SR)) / SR; return noise(dur, 0.5, 40, env="arch") * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 13 * t)))
SFX = {"buzz": buzz, "knock": knock, "growl": lambda: noise(1.3, 0.6, 90, env="arch", seed=3) + tone(70, 50, 1.3, 0.35, 1.5),
       "steps": lambda: np.concatenate([np.pad(tone(160, 110, 0.07, 0.5), (0, int(0.18 * SR))) for _ in range(6)]),
       "whoosh": lambda: noise(0.6, 0.45, 30, env="arch"), "heli": heli, "bang": lambda: knock() * 1.2,
       "sting": lambda: np.concatenate([tone(196, 196, 0.25, 0.4, 2), tone(185, 185, 0.6, 0.45, 2)]),
       "ding": lambda: np.concatenate([tone(880, 880, 0.15, 0.35), tone(1175, 1175, 0.4, 0.4)])}

def ambience(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    drone = 0.07 * np.sin(2 * np.pi * 55 * t) + 0.05 * np.sin(2 * np.pi * 82.4 * t + 1) + 0.04 * np.convolve(np.random.default_rng(5).uniform(-1, 1, n), np.ones(200) / 200, "same") * 14
    beat = np.zeros(n); hb = tone(60, 40, 0.16, 0.5, 4)
    for s in np.arange(0.0, dur, 0.95):
        for off in (0, 0.22):
            i = int((s + off) * SR); e = min(n, i + len(hb))
            if i < n: beat[i:e] += hb[: e - i] * (0.6 if off else 1)
    return drone + 0.5 * beat


def read_wav(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768; sr = w.getframerate()
    if sr != SR: a = np.interp(np.linspace(0, len(a), int(len(a) * SR / sr), endpoint=False), np.arange(len(a)), a)
    return a


# ---------------------------------------------------------------- one episode
def episode(name, preview=False):
    ep = EPS[name]; shots = []; t = 0.0
    for i, s in enumerate(ep["shots"]):
        s = dict(s); vp = f"{VOICE}/{name}_{i}.wav"
        if os.path.exists(vp): s["_voice"] = read_wav(vp); vd = len(s["_voice"]) / SR
        else: s["_voice"] = None; vd = 0.36 * len(s["say"].split()) + 0.3
        s["_vd"] = vd; s["_dur"] = max(1.4, vd + (0.55 if s["scene"] != "choice" else 1.3)); s["_t0"] = t; t += s["_dur"]
        s["_chance"] = s.get("chance", shots[-1]["_chance"] if shots else None); s["_chance0"] = shots[-1]["_chance"] if shots else s["_chance"]
        s["_words"] = words_of(s["say"], s.get("key")); s["_chunks"] = chunks(s["_words"])
        n = len(s["_words"]); ws = [len(w) + 2 for w, _ in s["_words"]]; tot = sum(ws); acc = 0; s["_wt"] = []
        for x in ws: s["_wt"].append(0.12 + (vd * 0.94) * acc / tot); acc += x
        shots.append(s)
    T_OUT = 3.2; dur = t + T_OUT
    rule_tag = {}; scene_cache = {}

    def scene_img(si, tick):
        key = (si, tick)
        if key not in scene_cache:
            if len(scene_cache) > 3: scene_cache.clear()
            s = shots[si]; im = Image.new("RGB", (W, H)); pen = Pen(ImageDraw.Draw(im, "RGBA"), seed=si * 1000 + (tick // 2 if DRAW_FPS > 12 else tick), j=JIT); pen.im = im
            SCENES[s["scene"]](im, pen, tick / DRAW_FPS - s["_t0"], s, tick * 12 / DRAW_FPS)
            if CAM > 1.0 and s["scene"] != "choice":
                cw, ch = int(W / CAM), int(H / CAM); x0 = (W - cw) // 2; y0 = int((H - ch) * 0.62)
                im = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
            scene_cache[key] = im
        return scene_cache[key].copy()

    def overlays(im, s, u, gt):
        badge(im)
        if s.get("clock"):
            hh, mm = map(int, s["clock"].split(":")); tm = (hh % 12) * 60 + mm + int(u // 2) + (12 * 60 if hh == 12 else 0)
            h2, m2 = divmod(tm % (24 * 60), 60); txt = f"{(h2 - 1) % 12 + 1}:{m2:02d} {'AM' if (h2 >= 12 or h2 < 6) else 'PM'}"
            L = text_line([(txt, WHITE)], 44, 5); im.paste(L, (40, 190), L)
        L = text_line([("PART " + str(ep["part"]), YEL)], 40, 5); im.paste(L, (W - L.width - 40, 190), L)
        if s.get("_chance") is not None and s["scene"] != "choice":
            c0 = s["_chance0"] if s["_chance0"] is not None else s["_chance"]; k = min(1, max(0, (u - 0.3) / 0.6)); c = round(c0 + (s["_chance"] - c0) * k)
            col = (70, 210, 120) if c >= 60 else (255, 214, 10) if c >= 30 else RED
            bar = Image.new("RGBA", (440, 78), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
            bd.rounded_rectangle([0, 0, 439, 77], 39, fill=(0, 0, 0, 210)); bd.rounded_rectangle([8, 8, 8 + max(24, int(424 * c / 100)), 69], 31, fill=col + (255,))
            bd.text((220, 39), f"SURVIVAL {c}%", font=F(42), fill=WHITE, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
            im.paste(bar, (40, 258), bar)
        if ep.get("hook") and (s["scene"] == "title" or s.get("title_overlay")) and u > 0.6:
            paste_c(im, text_line([(ep["hook"].upper(), YEL)], 56, 6), 1530, spring(u - 0.6))
        if s["scene"] == "title" or s.get("title_overlay"):
            paste_c(im, text_line([("STICKMAN", WHITE)], 120), 520, spring(u)); paste_c(im, text_line([("SURVIVAL", RED)], 132), 660, spring(u - 0.12))
            paste_c(im, text_line([(ep["title"].upper(), YEL)], 74), 820, spring(u - 0.3))
        if s.get("rule"):
            a = u - 0.15
            if a > 0:
                r, txt = s["rule"]; pill = text_line([("  " + r + "  ", WHITE)], 52, 0); bg = Image.new("RGBA", (pill.width, pill.height), RED + (255,)); bg.paste(pill, (0, 0), pill)
                paste_c(im, bg, 300, spring(a)); paste_c(im, text_line([(txt, WHITE)], 80), 395, spring(a - 0.1))
        if s["scene"] == "choice":
            q = s["choice"]
            for j, (lab, txt) in enumerate((("A", q[0]), ("B", q[1]))):
                a = u - 0.2 - 0.25 * j
                if a > 0:
                    card = Image.new("RGBA", (900, 200), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
                    cd.rounded_rectangle([0, 0, 899, 199], 40, fill=((255, 214, 10) if j == 0 else (254, 97, 0)) + (255,))
                    cd.text((50, 48), lab, font=F(96), fill=(17, 17, 17)); f = F(58 if len(txt) < 20 else 46); cd.text((170, 66 if len(txt) < 20 else 74), txt, font=f, fill=(17, 17, 17))
                    paste_c(im, card, 640 + j * 250, spring(a))
            if u > 0.8: paste_c(im, text_line([("COMMENT ", WHITE), ("A", YEL), (" OR ", WHITE), ("B", OR)], 70), 1180, spring(u - 0.8))
        # word-by-word caption
        if True:
            cur = -1
            for i, wt in enumerate(s["_wt"]):
                if u >= wt: cur = i
            if cur >= 0 and u < s["_vd"] + 0.5 and s["scene"] != "choice":
                ch = next(c for c in s["_chunks"] if any(x[0] == cur for x in c))
                parts = []
                for i, w, k in ch:
                    if i <= cur: parts += [(w.upper(), YEL if k else WHITE), (" ", WHITE)]
                L = text_line(parts[:-1] or [(" ", WHITE)], 92 if s["scene"] != "choice" else 64)
                paste_c(im, L, 1600 if s["scene"] == "choice" else 1380, spring(u - s["_wt"][cur], 0.12))

    def outro(im, u):
        im.paste(Image.new("RGB", (W, H), (12, 10, 18)), (0, 0)); badge(im)
        ic = Image.open(ICON).convert("RGB").resize((300, 300), Image.LANCZOS); m = Image.new("L", ic.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 299, 299], 70, fill=255)
        ic = ic.convert("RGBA"); ic.putalpha(m); s_ = spring(u); ic2 = ic.resize((int(300 * s_), int(300 * s_))); im.paste(ic2, (int((W - ic2.width) / 2), int(470 - ic2.height / 2)), ic2)
        paste_c(im, text_line([("Every frame drawn by hand", GREY)], 50, 5), 720, spring(u - 0.15))
        paste_c(im, text_line([("Want to make videos like this?", WHITE)], 60, 6), 900, spring(u - 0.35))
        paste_c(im, text_line([("Use ", WHITE), ("Framey", OR)], 120), 1020, spring(u - 0.5))
        paste_c(im, text_line([("the stop-motion app  ·  COMING SOON", GREY)], 44, 5), 1160, spring(u - 0.7))
        paste_c(im, text_line([(ep.get("next", "FOLLOW FOR PART " + str(ep["part"] + 1)), YEL)], 64), 1320, spring(u - 0.9))

    def frame(gt):
        if gt >= t: im = Image.new("RGB", (W, H)); outro(im, gt - t); return im
        si = max(i for i, s in enumerate(shots) if s["_t0"] <= gt); s = shots[si]; u = gt - s["_t0"]
        im = scene_img(si, int(gt * DRAW_FPS)); overlays(im, s, u, gt)
        if u < 0.08 and si > 0: im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), 0.35 * (1 - u / 0.08))  # quick flash cut
        return im

    if preview:
        os.makedirs(D + "/preview", exist_ok=True)
        ts = [s["_t0"] + s["_vd"] * 0.8 for s in shots] + [t + 2.5]
        ims = [frame(x).resize((216, 384)) for x in ts]; cols = min(5, len(ims)); rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (216 * cols, 384 * rows))
        for i, x in enumerate(ims): sheet.paste(x, ((i % cols) * 216, (i // cols) * 384))
        sheet.save(f"{D}/preview/stick-{name}.jpg", quality=80); print("preview", name, round(dur, 1), "s"); return

    d = f"{D}/r/stick-{name}"; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    for i in range(int(dur * FPS)): frame(i / FPS).save(f"{d}/{i:04d}.jpg", quality=96, subsampling=0)
    v = f"{D}/r/stick-{name}_v.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{d}/%04d.jpg", "-threads", "1", "-c:v", "libx264", "-crf", "16", "-tune", "animation",
                    "-preset", "fast", "-x264-params", "rc-lookahead=8:sliced-threads=0", "-profile:v", "high", "-maxrate", "12M", "-bufsize", "24M", "-g", "60", "-pix_fmt", "yuv420p", v], check=True)
    mix = ambience(dur)
    def put(at, snd, gain=1.0):
        i0 = int(at * SR); e = min(len(mix), i0 + len(snd))
        if 0 <= i0 < len(mix): mix[i0:e] += snd[: e - i0] * gain
    for s in shots:
        if s["_voice"] is not None: put(s["_t0"] + 0.1, s["_voice"], 1.6)
        for kind in s.get("sfx", []): put(s["_t0"] + 0.05, SFX[kind]())
    put(t - 0.05, SFX["ding"]()); put(t + 0.2, SFX["sting"]())
    fo = int(0.8 * SR); mix[-fo:] *= np.linspace(1, 0, fo); peak = max(1.0, np.abs(mix).max()); mix = mix / peak * 0.95
    wv = f"{D}/r/stick-{name}.wav"
    with wave.open(wv, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes())
    os.makedirs(OUT, exist_ok=True); out = f"{OUT}/framey-stick-{name}.mp4"; tmp = out[:-4] + ".tmp.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", v, "-i", wv, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out); shutil.rmtree(d, ignore_errors=True); print("stick", name, round(dur, 1), out)


if __name__ == "__main__":
    args = sys.argv[1:]; pv = "--preview" in args
    for nm in [x for x in args if not x.startswith("--")]:
        if not pv and os.path.exists(f"{V}/vout/framey-stick-{nm}.mp4"): print("skip", nm); continue
        episode(nm, preview=pv)
