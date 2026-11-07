# SPOT THE MISTAKE: a smooth looping animation with ONE wrong frame, shown twice, then revealed.
# Usage: python3 spot.py <variant> [--preview]   (RESUME=1: only write missing JPEG frames + wav into $WORK/spotjpg_<variant>, then stop)   (variants in VARIANTS below)
import os, sys, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

V = os.environ.get("FRAMEY_DIR", "/mnt/files/v")
OUT = os.environ.get("OUTDIR", V + "/vout"); FF = os.environ.get("FFMPEG", "ffmpeg")
W, H, FPS = 1080, 1920, 30
FB = V + "/Inter.ttf"; ICON = V + "/icon.png"
BG1, BG2 = (14, 16, 34), (34, 20, 52)
YEL, ORA, RED, WHITE = (255, 214, 10), (255, 122, 26), (238, 52, 64), (255, 255, 255)
PAL = [(255, 92, 92), (255, 170, 40), (255, 222, 60), (70, 210, 120), (70, 160, 255), (170, 110, 255)]

_fc = {}
def font(sz, wt=850):
    k = (sz, wt)
    if k not in _fc:
        f = ImageFont.truetype(FB, sz)
        try:
            ax = f.get_variation_axes(); f.set_variation_by_axes([32, wt] if len(ax) == 2 else [wt])
        except Exception: pass
        _fc[k] = f
    return _fc[k]

def bg():
    g = np.linspace(0, 1, H)[:, None, None]
    a = (np.array(BG1) * (1 - g) + np.array(BG2) * g).astype(np.uint8)
    return Image.fromarray(np.repeat(a, W, 1))
BASE = None

_icon = None
def badge(d, im):
    global _icon
    if _icon is None: _icon = Image.open(ICON).convert("RGB").resize((64, 64))
    f = font(40, 800); tw = d.textlength("Framey", font=f); bw = 64 + 18 + tw + 44
    x0 = (W - bw) / 2; y0 = 60
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + 88], 44, fill=(0, 0, 0))
    m = Image.new("L", (64, 64), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 63, 63], 16, fill=255)
    im.paste(_icon, (int(x0 + 14), y0 + 12), m)
    d.text((x0 + 14 + 64 + 18, y0 + 44), "Framey", font=f, fill=WHITE, anchor="lm")

def ctext(d, y, s, sz, col=WHITE, wt=900, stroke=8):
    f = font(sz, wt)
    while d.textlength(s, font=f) > W - 100 and sz > 30: sz -= 4; f = font(sz, wt)
    d.text((W / 2, y), s, font=f, fill=col, anchor="mm", stroke_width=stroke, stroke_fill=(0, 0, 0))

def balls(d, t, wrong):
    n = 5; gy = 1260; sp = W / (n + 1)
    d.line([80, gy + 62, W - 80, gy + 62], fill=(255, 255, 255, 60), width=6)
    for i in range(n):
        ph = (t * 1.6 + i * 0.13) % 1.0
        h = abs(math.sin(math.pi * ph)); y = gy - h * 560
        sq = max(0, 1 - h * 6) * 0.28
        rx, ry = 62 * (1 + sq), 62 * (1 - sq)
        x = sp * (i + 1); sh = 50 * (0.5 + 0.5 * (1 - h))
        d.ellipse([x - sh, gy + 52, x + sh, gy + 70], fill=(0, 0, 0))
        c = PAL[i]
        if i == 2: p3 = (x, y)
        if wrong and i == 2:
            d.rounded_rectangle([x - 62, y - 62, x + 62, y + 62], 14, fill=c, outline=(0, 0, 0), width=6)
        else:
            d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=c, outline=(0, 0, 0), width=6)
            d.ellipse([x - rx * 0.45, y - ry * 0.6, x - rx * 0.05, y - ry * 0.25], fill=(255, 255, 255))
    return p3

def gears(d, t, wrong):
    def gear(cx, cy, r, teeth, ang, col):
        pts = []
        for k in range(teeth * 2):
            a = ang + k * math.pi / teeth; rr = r if k % 2 == 0 else r * 0.82
            for s in (-0.38, 0.38):
                aa = a + s * math.pi / teeth; pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
        d.polygon(pts, fill=col, outline=(0, 0, 0), width=6)
        d.ellipse([cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3], fill=(20, 20, 30), outline=(0, 0, 0), width=6)
    a = t * 1.4
    gear(360, 900, 230, 12, a, PAL[1])
    gear(720, 1180, 170, 9, -a * 12 / 9 + 0.2, PAL[4])
    gear(420, 1390, 130, 7, -a * 12 / 7, PAL[0] if wrong else PAL[3])
    return (420, 1390)

def walker(d, t, wrong):
    gy = 1300; x = 160 + (t * 260) % 800; L = 150; ph = t * 2 * math.pi * 1.3
    d.line([0, gy, W, gy], fill=(255, 255, 255), width=6)
    hip = (x, gy - 2 * L + 10 * abs(math.sin(ph)))
    def leg(off):
        s = math.sin(ph + off); k = (hip[0] + s * 70, hip[1] + L)
        f = (hip[0] + s * 120, gy); d.line([hip, k, f], fill=WHITE, width=18, joint="curve")
    def arm(off):
        sh = (hip[0], hip[1] - 1.1 * L); s = math.sin(ph + off)
        e = (sh[0] + s * 60, sh[1] + 0.6 * L); h_ = (sh[0] + s * 90, sh[1] + 1.1 * L)
        d.line([sh, e, h_], fill=WHITE, width=16, joint="curve")
    leg(0); leg(math.pi); arm(math.pi); arm(0)
    neck = (hip[0], hip[1] - 1.25 * L)
    d.line([hip, neck], fill=WHITE, width=18)
    hx, hy = neck[0], neck[1] - 62
    if wrong:
        d.rounded_rectangle([hx - 58, hy - 58, hx + 58, hy + 58], 10, fill=ORA, outline=(0, 0, 0), width=6)
    else:
        d.ellipse([hx - 58, hy - 58, hx + 58, hy + 58], fill=WHITE, outline=(0, 0, 0), width=6)
    return (hx, hy)

VARIANTS = {
    "balls": dict(scene=balls, hook="1 FRAME IS WRONG", sub="Can you spot it?", reveal="Ball #3 turned into a square!", wrong_at=3.9,
                  caption="1 frame in this animation is WRONG 👀 Did you spot it the first time? Be honest 👇 Every frame here is drawn one by one, just like in Framey, the stop-motion app for your phone. Coming soon! Follow @frameyapp for more. #stopmotion #animation #spotthedifference #framey"),
    "gears": dict(scene=gears, hook="1 FRAME IS WRONG", sub="Watch the gears...", reveal="The green gear turned RED!", wrong_at=3.8,
                  caption="One frame breaks the gears ⚙️ Did you catch it? Comment the second you saw it 👇 Made frame by frame, the way you animate in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #animation #satisfying #framey"),
    "walker": dict(scene=walker, hook="1 FRAME IS WRONG", sub="Keep your eyes on him...", reveal="His head turned into a box!", wrong_at=3.5,
                   caption="Stickman walks... but 1 frame is WRONG 🧍 Did you see it? Comment the second 👇 Animated frame by frame like you can in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #stickman #animation #framey"),
}


def pendulum(d, t, wrong):
    n = 9; top = 560; d.line([120, top, W - 120, top], fill=(200, 200, 220), width=10)
    p_out = None
    for i in range(n):
        x0 = 180 + i * (W - 360) / (n - 1); L = 700 - i * 40
        ang = 0.28 * math.sin(2 * math.pi * t * (0.5 + i * 0.02))
        bx, by = x0 + L * math.sin(ang), top + L * math.cos(ang)
        d.line([x0, top, bx, by], fill=(230, 230, 240), width=5)
        c = (255, 255, 255) if (wrong and i == 6) else PAL[i % len(PAL)]
        if i == 6: p_out = (bx, by)
        d.ellipse([bx - 44, by - 44, bx + 44, by + 44], fill=c, outline=(0, 0, 0), width=6)
        d.ellipse([bx - 22, by - 30, bx - 4, by - 12], fill=(255, 255, 255))
    return p_out

def orbit(d, t, wrong):
    cx, cy = W / 2, 1000
    for r in (230, 360, 480): d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(80, 80, 120), width=4)
    d.ellipse([cx - 110, cy - 110, cx + 110, cy + 110], fill=(255, 196, 40), outline=(0, 0, 0), width=8)
    for k in range(14):
        a = k * 2 * math.pi / 14 + t * 0.3; d.line([cx + 125 * math.cos(a), cy + 125 * math.sin(a), cx + 150 * math.cos(a), cy + 150 * math.sin(a)], fill=(255, 220, 90), width=8)
    out = None
    for r, sp, sz, col in ((230, 1.6, 34, PAL[4]), (360, 1.0, 50, PAL[0]), (480, 0.65, 42, PAL[3])):
        a = t * sp; px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        d.ellipse([px - sz, py - sz, px + sz, py + sz], fill=col, outline=(0, 0, 0), width=6)
        if r == 360:
            out = (px, py)
            if not wrong:
                ma = t * 4.2; mx, my = px + 100 * math.cos(ma), py + 100 * math.sin(ma)
                d.ellipse([mx - 26, my - 26, mx + 26, my + 26], fill=(220, 220, 230), outline=(0, 0, 0), width=4)
    return out

def clock(d, t, wrong):
    cx, cy, R = W / 2, 1000, 380
    d.ellipse([cx - R - 24, cy - R - 24, cx + R + 24, cy + R + 24], fill=(255, 122, 26), outline=(0, 0, 0), width=10)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(250, 246, 236), outline=(0, 0, 0), width=8)
    for k in range(12):
        a = k * math.pi / 6; l = 50 if k % 3 == 0 else 26
        d.line([cx + (R - 20) * math.sin(a), cy - (R - 20) * math.cos(a), cx + (R - 20 - l) * math.sin(a), cy - (R - 20 - l) * math.cos(a)], fill=(30, 30, 40), width=12 if k % 3 == 0 else 6)
    m = t * 2 * math.pi / 3.0
    h = m / 12
    if wrong: m += math.pi
    d.line([cx, cy, cx + 210 * math.sin(h), cy - 210 * math.cos(h)], fill=(30, 30, 40), width=22)
    d.line([cx, cy, cx + 320 * math.sin(m), cy - 320 * math.cos(m)], fill=(238, 52, 64), width=14)
    d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(30, 30, 40))
    return (cx + 230 * math.sin(m), cy - 230 * math.cos(m))

VARIANTS.update({
    "pendulum": dict(scene=pendulum, hook="1 FRAME IS WRONG", sub="Watch the pendulums...", reveal="Ball #7 turned WHITE!", wrong_at=4.1,
                     caption="So satisfying... but 1 frame is WRONG 👀 Did you catch it? Comment the second you saw it 👇 Every frame drawn one by one, like in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #satisfying #animation #framey"),
    "orbit": dict(scene=orbit, hook="1 FRAME IS WRONG", sub="Keep your eyes on the planets...", reveal="The moon disappeared!", wrong_at=3.6,
                  caption="Planets spinning around the sun... but 1 frame is WRONG 🪐 Did you spot it? Comment the second 👇 Made frame by frame, like you can in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #space #animation #framey"),
    "clock": dict(scene=clock, hook="1 FRAME IS WRONG", sub="Watch the clock...", reveal="The red hand jumped!", wrong_at=4.4,
                  caption="Tick tock... 1 frame is WRONG ⏰ Did you see it the first time? Be honest 👇 Every frame drawn one by one, like in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #animation #spotthedifference #framey"),
})


def ferris(d, t, wrong):
    cx, cy, R = W / 2, 980, 360
    d.polygon([(cx, cy), (cx - 260, 1460), (cx - 200, 1460)], fill=(120, 120, 150), outline=(0, 0, 0))
    d.polygon([(cx, cy), (cx + 260, 1460), (cx + 200, 1460)], fill=(120, 120, 150), outline=(0, 0, 0))
    d.line([80, 1462, W - 80, 1462], fill=(200, 200, 220), width=8)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(230, 230, 245), width=12)
    d.ellipse([cx - R * 0.55, cy - R * 0.55, cx + R * 0.55, cy + R * 0.55], outline=(170, 170, 200), width=6)
    a0 = t * 0.9; out = None
    for k in range(8):
        a = a0 + k * math.pi / 4; px, py = cx + R * math.cos(a), cy + R * math.sin(a)
        d.line([cx, cy, px, py], fill=(200, 200, 220), width=6)
    for k in range(8):
        a = a0 + k * math.pi / 4; px, py = cx + R * math.cos(a), cy + R * math.sin(a)
        d.line([px, py, px, py + 40], fill=(30, 30, 40), width=6)
        c = PAL[k % len(PAL)]; by = py + 40
        if k == 4: out = (px, by + 40)
        if wrong and k == 4:
            d.polygon([(px, by + 95), (px - 70, by - 5), (px + 70, by - 5)], fill=c, outline=(0, 0, 0), width=6)
        else:
            d.rounded_rectangle([px - 60, by, px + 60, by + 80], 22, fill=c, outline=(0, 0, 0), width=6)
            d.rectangle([px - 38, by + 14, px + 38, by + 40], fill=(220, 240, 255))
    d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], fill=(255, 196, 40), outline=(0, 0, 0), width=6)
    return out

def balloons(d, t, wrong):
    out = None
    for i in range(6):
        x = 150 + i * 156 + 30 * math.sin(t * 1.7 + i)
        y = 1500 - ((t * 190 + i * 230) % 1100)
        c = PAL[i]
        d.line([x, y + 75, x + 10 * math.sin(t * 3 + i), y + 260], fill=(230, 230, 240), width=4)
        if i == 3: out = (x, y)
        if wrong and i == 3:
            pts = [(x + (78 if k % 2 == 0 else 34) * math.sin(k * math.pi / 5), y - (78 if k % 2 == 0 else 34) * math.cos(k * math.pi / 5)) for k in range(10)]
            d.polygon(pts, fill=c, outline=(0, 0, 0), width=6)
        else:
            d.ellipse([x - 62, y - 78, x + 62, y + 78], fill=c, outline=(0, 0, 0), width=6)
            d.ellipse([x - 36, y - 56, x - 14, y - 22], fill=(255, 255, 255, 200))
            d.polygon([(x, y + 76), (x - 14, y + 94), (x + 14, y + 94)], fill=c, outline=(0, 0, 0))
    return out

def fish(d, t, wrong):
    d.rectangle([0, 560, W, 1520], fill=(30, 90, 160, 110))
    for k in range(5):
        bx = 120 + k * 210; by = 1480 - ((t * 140 + k * 190) % 900)
        d.ellipse([bx - 14, by - 14, bx + 14, by + 14], outline=(200, 230, 255), width=4)
    out = None
    for i in range(4):
        y = 720 + i * 220; sp = 230 + i * 30
        x = -150 + ((t * sp + (0, 260, 1084, 780)[i]) % (W + 300)); c = PAL[(i * 2 + 1) % len(PAL)]
        wig = 18 * math.sin(t * 9 + i)
        flip = wrong and i == 2
        s = -1 if flip else 1
        if i == 2: out = (x, y)
        col = (238, 52, 64) if flip else c
        d.polygon([(x - s * 95, y), (x - s * 165, y - 60 + wig), (x - s * 165, y + 60 + wig)], fill=col, outline=(0, 0, 0), width=6)
        d.ellipse([x - 110, y - 62, x + 110, y + 62], fill=col, outline=(0, 0, 0), width=6)
        d.ellipse([x + s * 50 - 16, y - 30, x + s * 50 + 16, y + 2], fill=WHITE, outline=(0, 0, 0), width=4)
        d.ellipse([x + s * 56 - 7, y - 20, x + s * 56 + 7, y - 6], fill=(0, 0, 0))
    return out

def traffic(d, t, wrong):
    cx = W / 2
    d.rectangle([cx - 22, 1300, cx + 22, 1600], fill=(70, 70, 90))
    d.rounded_rectangle([cx - 170, 560, cx + 170, 1320], 60, fill=(40, 40, 52), outline=(0, 0, 0), width=10)
    ph = (t / 1.5) % 4; st = 0 if ph < 1.5 else (1 if ph < 2 else (2 if ph < 3.5 else 1))
    cols = [(238, 52, 64), (255, 196, 40), (70, 210, 120)]
    on = {st}
    if wrong: on = {0, 2}
    for k in range(3):
        y = 700 + k * 240; c = cols[k] if k in on else tuple(v // 5 for v in cols[k])
        d.ellipse([cx - 95, y - 95, cx + 95, y + 95], fill=c, outline=(0, 0, 0), width=8)
    d.line([0, 1520, W, 1520], fill=(200, 200, 220), width=6)
    x = -120 + (t * 300) % (W + 240)
    d.rounded_rectangle([x - 110, 1410, x + 110, 1490], 24, fill=PAL[4], outline=(0, 0, 0), width=6)
    for wx in (x - 60, x + 60): d.ellipse([wx - 28, 1466, wx + 28, 1522], fill=(20, 20, 26), outline=(0, 0, 0), width=4)
    return (cx, 700)

VARIANTS.update({
    "ferris": dict(scene=ferris, hook="1 FRAME IS WRONG", sub="Watch the Ferris wheel...", reveal="A cabin turned into a TRIANGLE!", wrong_at=3.7,
                   caption="Round and round... but 1 frame is WRONG 🎡 Did you spot it the first time? Comment the second you saw it 👇 Every frame drawn one by one, like in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #animation #spotthedifference #framey"),
    "balloons": dict(scene=balloons, hook="1 FRAME IS WRONG", sub="Follow the balloons...", reveal="The green balloon became a STAR!", wrong_at=4.2,
                     caption="6 balloons floating up... 1 frame is WRONG 🎈 Did you catch it? Be honest 👇 Animated frame by frame, the way you animate in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #satisfying #animation #framey"),
    "fish": dict(scene=fish, hook="1 FRAME IS WRONG", sub="Watch the fish swim...", reveal="One fish turned RED and swam backwards!", wrong_at=3.4,
                 caption="Just fish swimming... or is it? 🐟 1 frame is WRONG. Comment the second you saw it 👇 Made frame by frame, like you can in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #animation #fish #framey"),
    "traffic": dict(scene=traffic, hook="1 FRAME IS WRONG", sub="Watch the traffic light...", reveal="RED and GREEN were on at once!", wrong_at=4.0,
                    caption="Red, green, yellow... but 1 frame is WRONG 🚦 Did you see it the first time? Be honest 👇 Every frame drawn one by one, like in Framey, the stop-motion app. Coming soon! Follow @frameyapp for more. #stopmotion #animation #spotthedifference #framey"),
})

def windmills(d, t, wrong):
    gy = 1440; out = None
    d.ellipse([-200, gy - 90, W + 200, gy + 400], fill=(40, 120, 70), outline=(0, 0, 0), width=6)
    d.ellipse([800, 420, 940, 560], fill=(250, 240, 200)); d.ellipse([835, 405, 975, 545], fill=(24, 18, 40))   # moon
    for k in range(26):   # twinkling stars
        sx = (k * 383) % (W - 80) + 40; sy = 400 + ((k * 7) % 13) * 34 + (k % 3) * 9; r = 3 + 3 * (0.5 + 0.5 * math.sin(t * 3 + k))
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 250, 220))
    for i, (x, top, R, sp) in enumerate(((230, 1010, 170, 1.2), (W / 2, 820, 230, 0.9), (850, 1060, 150, 1.4))):
        d.polygon([(x - 34, top), (x + 34, top), (x + 62, gy - 20), (x - 62, gy - 20)], fill=(235, 228, 214), outline=(0, 0, 0), width=6)
        d.rectangle([x - 20, gy - 110, x + 20, gy - 20], fill=(120, 80, 50), outline=(0, 0, 0), width=4)
        a0 = t * sp * (1 if i != 1 else -1)
        col = (238, 52, 64) if (wrong and i == 1) else (PAL[2] if i == 1 else PAL[4])
        for b in range(4):
            a = a0 + b * math.pi / 2; ca, sa = math.cos(a), math.sin(a)
            p = lambda r, w: (x + r * ca - w * sa, top + r * sa + w * ca)
            d.polygon([p(18, -10), p(R, -30), p(R, 30), p(18, 10)], fill=col, outline=(0, 0, 0), width=5)
        d.ellipse([x - 22, top - 22, x + 22, top + 22], fill=(40, 40, 50), outline=(0, 0, 0), width=4)
        if i == 1: out = (x, top)
    return out

VARIANTS.update({
    "windmills": dict(scene=windmills, hook="1 FRAME IS WRONG", sub="Watch the windmills spin...", reveal="The big windmill turned RED!", wrong_at=3.6,
                      caption="3 windmills spinning... but 1 frame is WRONG \U0001F32C\uFE0F Did you spot it the first time? Comment the second you saw it \U0001F447 This was drawn with code, one frame at a time, the same frame-by-frame idea behind Framey, the stop-motion app for your phone. Coming soon! Follow for more. #stopmotion #animation #spotthedifference #framey"),
})

PLAY = 6.0; NW = 3

def make_frames(v):
    segs = [("hook", 2.0), ("play1", PLAY), ("again", 0.7), ("play2", PLAY), ("reveal", 3.2), ("outro", 3.4)]
    t0 = 0
    for name, dur in segs:
        n = int(dur * FPS)
        for k in range(n):
            yield name, k, n, t0
        t0 += dur

def render(name, preview=False):
    global BASE
    v = VARIANTS[name]; sc = v["scene"]; wf0 = int(v["wrong_at"] * FPS)
    BASE = bg(); os.makedirs(OUT, exist_ok=True)
    out = f"{OUT}/framey-spot-{name}.mp4"
    frames = list(make_frames(v)); total = len(frames)
    if preview: frames = [frames[i] for i in (10, 60 + wf0, 60 + wf0 + 20, total - 160, total - 50)]
    p = None
    if not preview:
        make_audio(name, v, total)
        JD = os.environ.get("WORK", "/home/user") + f"/spotjpg_{name}"; os.makedirs(JD, exist_ok=True)
        RESUME = os.environ.get("RESUME")
        if not RESUME:
            for f_ in os.listdir(JD): os.remove(os.path.join(JD, f_))
        p = None; enc = [FF, "-y", "-v", "error", "-framerate", str(FPS), "-i", JD + "/%04d.jpg",
                              "-i", f"{OUT}/_spot_{name}.wav", "-c:v", "libx264", "-threads", "1", "-preset", "faster", "-crf", "21", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    shots = []; fi = 0
    for seg, k, n, t0 in frames:
        if not preview and os.environ.get("RESUME") and os.path.exists(f"{JD}/{fi:04d}.jpg"): fi += 1; continue
        im = BASE.copy(); d = ImageDraw.Draw(im, "RGBA")
        if seg in ("play1", "play2", "hook"):
            t = k / FPS if seg != "hook" else 0.0
            wrong = seg != "hook" and wf0 <= k < wf0 + NW
            sc(d, t, wrong)
            if seg == "hook":
                d.rectangle([0, 0, W, H], fill=(0, 0, 0, 120))
                pop = min(1, k / 6); ctext(d, 760, v["hook"], int(120 * (0.7 + 0.3 * pop)), YEL)
                ctext(d, 900, v["sub"], 72)
            else:
                ctext(d, 330, "WATCH CLOSELY" if seg == "play1" else "ONE MORE TIME", 70, YEL)
                if seg == "play2": ctext(d, 1560, "Comment the second you saw it!", 56)
                sec = (k / FPS)
                ctext(d, 1700, f"{sec:04.1f}s", 60, WHITE, 700, 6)
        elif seg == "again":
            sc(d, PLAY, False); d.rectangle([0, 0, W, H], fill=(0, 0, 0, 170))
            ctext(d, 900, "DID YOU SEE IT?", 110, YEL)
        elif seg == "reveal":
            pos = sc(d, wf0 / FPS, True)
            r = 150 + 10 * math.sin(k / 3)
            d.ellipse([pos[0] - r, pos[1] - r, pos[0] + r, pos[1] + r], outline=RED, width=14)
            ctext(d, 330, f"HERE! AT {wf0 / FPS:.1f}s", 96, RED)
            ctext(d, 1560, v["reveal"], 64)
            ctext(d, 1660, f"It lasted only {NW} frames", 50, YEL)
        else:
            d.rectangle([0, 0, W, H], fill=(8, 8, 16, 235))
            ic = Image.open(ICON).convert("RGB").resize((300, 300)); m = Image.new("L", (300, 300), 0)
            ImageDraw.Draw(m).rounded_rectangle([0, 0, 299, 299], 70, fill=255); im.paste(ic, (390, 480), m)
            ctext(d, 900, "Every frame matters.", 56)
            ctext(d, 1010, "Want to make videos like this?", 60)
            f = font(150, 900); s1, s2 = "Use ", "Framey"; w1 = d.textlength(s1, font=f); w2 = d.textlength(s2, font=f)
            x = (W - w1 - w2) / 2; d.text((x, 1160), s1, font=f, fill=WHITE, anchor="lm"); d.text((x + w1, 1160), s2, font=f, fill=ORA, anchor="lm")
            ctext(d, 1290, "the stop-motion app  ·  COMING SOON", 46, WHITE, 700, 0)
            ctext(d, 1420, "FOLLOW FOR MORE", 70, YEL, 900, 0)
        badge(d, im)
        if preview: shots.append(im.resize((270, 480)))
        else: im.save(f"{JD}/{fi:04d}.jpg", quality=92); fi += 1
    if preview:
        sheet = Image.new("RGB", (270 * len(shots), 480))
        for i, s in enumerate(shots): sheet.paste(s, (270 * i, 0))
        sheet.save(f"{OUT}/spot_{name}_preview.jpg"); print("preview"); return
    if os.environ.get("RESUME"): print("FRAMES DONE", fi); return
    vv = f"{JD}_v.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", JD + "/%04d.jpg", "-threads", "1", "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p", vv], check=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", vv, "-i", f"{OUT}/_spot_{name}.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(vv); os.remove(f"{OUT}/_spot_{name}.wav"); print("spot", name, total / FPS, out)

def make_audio(name, v, total):
    sr = 24000; n = int(total / FPS * sr) + sr; a = np.zeros(n, np.float32)
    def tone(t, f, dur=0.12, vol=0.25):
        i = int(t * sr); m = int(dur * sr); tt = np.arange(m) / sr
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 28) * vol
        a[i:i + m] += s[: max(0, min(m, n - i))]
    def noise(t, dur, vol):
        i = int(t * sr); m = int(dur * sr); env = np.sin(np.linspace(0, np.pi, m)) * vol
        a[i:i + m] += (np.random.randn(m) * env)[: max(0, min(m, n - i))]
    notes = [523, 587, 659, 784, 880]
    for start in (2.0, 2.0 + PLAY + 0.7):
        for b in range(int(PLAY * 4)):
            tone(start + b * 0.25, notes[b % 5] if b % 2 == 0 else 392, 0.1, 0.12)
        tone(start + v["wrong_at"], 1400, 0.05, 0.04)
    tone(0.05, 300, 0.4, 0.3); tone(0.25, 600, 0.3, 0.25)
    noise(2.0 + PLAY, 0.5, 0.15); noise(2.0 + 2 * PLAY + 0.7, 0.5, 0.2)
    r0 = 2.0 + 2 * PLAY + 0.7; tone(r0 + 0.05, 880, 0.5, 0.35); tone(r0 + 0.2, 1175, 0.6, 0.3)
    o0 = r0 + 3.2; tone(o0 + 0.05, 659, 0.4, 0.25); tone(o0 + 0.2, 988, 0.5, 0.25)
    a = np.clip(a, -1, 1)
    with wave.open(f"{OUT}/_spot_{name}.wav", "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((a * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    render(sys.argv[1], "--preview" in sys.argv)
