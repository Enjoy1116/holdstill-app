# "I Survived 100 Days in a Zombie Apocalypse" — Stickman short for Framey. 1080x1920, 60 fps.
# Usage: python3 film.py preview t1 t2 ...   |   python3 film.py render [start end]
import math, random, sys, subprocess, json
import numpy as np
import skia
from rig import *
from world import *

FPS = 60
NIGHT = (C(10, 14, 38), C(46, 30, 74))

# narration lines: (start, end, text)  — times from the word-level transcript
LINES = [
 (0.0, 7.5, "Day 99. I'm stuck on a roof. I have zero food. And the only way down... is through them."),
 (8.4, 11.5, "To understand how I got here, we have to go back to day 1."),
 (12.3, 14.6, "I woke up to 47 missed calls."),
 (15.1, 20.2, "Outside, everyone was running. Everyone except the ones who were... walking."),
 (20.8, 24.7, "So I did the smart thing. I pushed everything I owned against the door."),
 (25.4, 28.3, "By day 7, I was down to 3 cans of beans."),
 (28.6, 29.8, "And I hate beans."),
 (30.6, 34.8, "On day 12, something scratched at my door. I almost didn't open it."),
 (35.3, 39.2, "It was a dog. I named him Biscuit. Best decision I ever made."),
 (39.8, 43.8, "Day 20. We needed food, so we snuck into the supermarket."),
 (44.2, 46.9, "Rule number one: don't make a sound."),
 (47.5, 48.9, "Biscuit knocked over a can."),
 (49.3, 51.6, "Every head in that store turned at once."),
 (51.8, 55.0, "We ran. I have never run that fast in my life."),
 (55.7, 59.3, "After that, I stopped going out. I turned the roof into a farm."),
 (59.6, 63.3, "Tomatoes, rainwater, and a lot of very boring days."),
 (63.9, 68.2, "Then, on day 64, I saw something that made my blood go cold."),
 (68.7, 71.5, "One of them opened a door. With the handle."),
 (71.9, 72.8, "They were learning."),
 (73.5, 77.0, "On day 80, a storm wiped out the whole farm in one night."),
 (77.3, 82.0, "Which brings us back to day 99. No food. And they're coming up the stairs."),
 (82.5, 87.5, "But zombies follow sound. And I had one thing left that was very, very loud."),
 (87.8, 91.1, "My phone. Full volume. Biscuit's favorite song."),
 (91.5, 93.3, "I threw it as far as I could."),
 (93.4, 95.3, "And every single one of them followed it."),
 (95.9, 98.6, "Day 100. We walked out the front door."),
 (98.8, 102.6, "And for the first time in 100 days... the street was quiet."),
 (103.3, 103.9, "Too quiet."),
 (104.5, 106.6, "Want part 2? Comment Biscuit."),
]
HOT = {"zombies", "biscuit", "biscuit's", "run", "ran.", "beans.", "learning.", "quiet.", "100", "99.", "99", "47", "handle.", "storm", "loud.", "sound."}

def build_words():
    out = []
    for (a, b, txt) in LINES:
        ws = txt.split(); wt = [len(w) + 2 for w in ws]; tot = sum(wt); acc = 0
        for w, x in zip(ws, wt):
            out.append((a + (b - a) * acc / tot, w)); acc += x
    return out
WORDS = build_words()

def chunks():
    """Group words into caption chunks of up to 3 words, breaking at punctuation and line ends."""
    res = []
    for (a, b, txt) in LINES:
        ws = [w for w in WORDS if a - 1e-6 <= w[0] < b + 1e-6]
        cur = []
        for t0, w in ws:
            cur.append((t0, w))
            if len(cur) == 3 or w[-1] in ".,?:" or len(" ".join(x[1] for x in cur)) > 15:
                res.append(cur); cur = []
        if cur: res.append(cur)
    for i, ch in enumerate(res):
        nxt = res[i + 1][0][0] if i + 1 < len(res) else ch[-1][0] + 1.2
        ch_end = min(nxt, ch[-1][0] + 1.4)
        res[i] = (ch[0][0], ch_end, ch)
    return res
CHUNKS = chunks()

# ---------------------------------------------------------------- helpers
def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, px=0, py=0, rot=0):
    c.translate(W / 2 + px, H / 2 + py); c.rotate(rot); c.scale(zoom, zoom); c.translate(-cx, -cy)

def shake(t, amt, f=31.0):
    return (math.sin(t * f) * math.sin(t * f * 0.37 + 1) * amt, math.cos(t * f * 0.83) * math.sin(t * f * 0.21 + 2) * amt)

def blink_at(t, seed=0):
    ph = (t + seed * 1.7) % 3.3
    return ph < 0.09

def horde(c, t, rows, y_top, y_bot, x0, x1, s0, s1, seed=11, reach=True, dir_=None, speed=0.0, tint=None):
    rnd = random.Random(seed)
    items = []
    for r_ in range(rows):
        k = r_ / max(1, rows - 1)
        gy = lerp(y_top, y_bot, k); s = lerp(s0, s1, k)
        n = int((x1 - x0) / (s * 0.42)) + 2
        for i in range(n):
            x = x0 + (i + rnd.uniform(-0.3, 0.3)) * (x1 - x0) / n + (r_ % 2) * s * 0.2
            items.append((gy, x, s, rnd.random() * 10, rnd.choice([-1, 1]), k))
    items.sort()
    for gy, x, s, ph, fc, k in items:
        if dir_ is not None:
            fc = dir_; x = x + speed * t * (0.8 + 0.4 * (ph % 1))
            p = zwalk(t * 4 + ph)
        elif reach:
            sw = math.sin(t * 2.2 + ph)
            p = pose(lean=-10 + 4 * sw, head=-28, uaL=-150 + 18 * sw, laL=-10, uaR=-160 - 14 * sw, laR=10,
                     ulL=-6, ulR=6, bob=0.004 * math.sin(t * 5 + ph))
        else:
            p = zwalk(t * 2 + ph, 0.6)
        st = ZOMB
        if k < 0.6:
            d = 0.45 + 0.55 * k
            st = dict(ZOMB, body=C(118 * d, 150 * d, 104 * d), head=C(146 * d, 184 * d, 120 * d))
        stick(c, x, gy, s, p, st, face=fc, expr="z", look=0.3)
    # fog over the far rows
    c.drawRect(skia.Rect.MakeLTRB(-400, y_top - s0 * 1.2, W + 400, y_top + (y_bot - y_top) * 0.5),
               lin(c, 0, y_top - s0 * 1.2, 0, y_top + (y_bot - y_top) * 0.5, [C(40, 30, 70, 0), C(40, 30, 70, 110), C(40, 30, 70, 0)]))

def building_facade(c, l, r, top, bot, t, lit=0.15, seed=4, col=C(52, 50, 72)):
    rect(c, l, top, r, bot, fill(col))
    rect(c, l - 20, top - 24, r + 20, top + 6, fill(C(72, 70, 96)))
    rnd = random.Random(seed)
    for j in range(int((bot - top) // 150)):
        for i in range(4):
            wx = l + 40 + i * (r - l - 80) / 4; wy = top + 70 + j * 150
            on = rnd.random() < lit
            col2 = C(255, 210, 120) if on else C(24, 24, 40)
            outlined_rect(c, wx, wy, wx + (r - l - 80) / 4 - 40, wy + 90, col2, 6, 4)
            if not on and rnd.random() < 0.3:
                c.drawLine(wx + 10, wy + 10, wx + 50, wy + 70, stroke(C(70, 70, 96), 4))

def roof_scene(c, t, hero_pose=None, expr="worry", hero_x=540, dog_mode="sit", horde_on=True, night=True, look=0.6, skycols=None, extra=None):
    sky(c, *(skycols or NIGHT))
    stars(c, 7, 90, 900, t)
    moon(c, 840, 330, 70)
    skyline(c, 21, 1250, 250, 560, C(30, 26, 58), C(120, 110, 170), 0.12, t=t)
    skyline(c, 22, 1380, 200, 450, C(22, 20, 42), C(255, 200, 120), 0.08, t=t, flicker=1)
    building_facade(c, 170, 910, 800, H + 50, t)
    # rooftop props
    outlined_rect(c, 200, 690, 300, 800, C(90, 90, 116), 7, 6)            # vent
    c.drawLine(745, 800, 745, 600, stroke(OUT, 14)); outlined_rect(c, 690, 540, 870, 640, C(110, 86, 70), 7, 30)  # water tank
    for x in (705, 855): c.drawLine(x, 640, x - 12 * (1 if x < 800 else -1), 800, stroke(OUT, 10))
    if horde_on:
        horde(c, t, 5, 1560, 1980, -120, W + 120, 120, 250)
    if extra: extra(c, t)
    hp = hero_pose if hero_pose is not None else idle(t)
    stick(c, hero_x, 800, 300, hp, HERO, face=1, expr=expr, look=look, blink=blink_at(t), scarf_t=t, wind=0.6)
    if dog_mode:
        dog(c, hero_x + 150, 800, 150, t, face=1, mode=dog_mode, wag=0.6)

# ---------------------------------------------------------------- shots
def s_hook(c, t, T):
    z = lerp(1.6, 1.0, ease((t - 0.8) / 3.0)) + 0.05 * ease((t - 6.4) / 1.2)
    cy = lerp(700, 960, ease((t - 0.8) / 3.0)) + 260 * ease((t - 6.4) / 1.2)
    sx, sy = shake(t, 3)
    c.save(); cam(c, z, W / 2, cy, sx, sy)
    look = 0.6 if t < 5.5 else 0.2
    roof_scene(c, t, expr="worry" if t < 6.3 else "shock", look=look)
    c.restore()
    if t < 3.2:
        k = back_out(clamp(t / 0.45)); a = clamp((3.2 - t) / 0.4)
        c.save(); c.translate(W / 2, 330); c.scale(k, k)
        c.saveLayerAlpha(None, int(255 * a))
        text_c(c, "I SURVIVED", 0, -10, font("Lucky", 120), C(255, 255, 255), OUT, 22)
        text_c(c, "100 DAYS", 0, 120, font("Lucky", 170), C(255, 214, 10), OUT, 26)
        text_c(c, "IN A ZOMBIE APOCALYPSE", 0, 200, font("Lucky", 64), C(254, 97, 0), OUT, 16)
        c.restore(); c.restore()

def s_rewind(c, t, T):
    tt = 7.5 - t * 2.2
    sx, sy = shake(t, 9, 45)
    c.save(); cam(c, 1.0 + 0.04 * math.sin(t * 12), W / 2, 960, sx, sy)
    roof_scene(c, tt, expr="shock", look=0.2)
    c.restore()
    grade(c, C(150, 160, 210), skia.BlendMode.kMultiply)
    rnd = random.Random(int(t * 24))
    for i in range(7):
        y = rnd.uniform(0, H); h = rnd.uniform(6, 30)
        rect(c, 0, y, W, y + h, fill(C(255, 255, 255, int(rnd.uniform(30, 90)))))
    k = 0.6 + 0.4 * abs(math.sin(t * 6))
    c.save(); c.translate(W / 2, 640)
    tri = skia.Path()
    for dx in (-70, 30):
        tri.moveTo(dx + 60, -60); tri.lineTo(dx - 20, 0); tri.lineTo(dx + 60, 60); tri.close()
    c.drawPath(tri, fill(C(255, 255, 255, int(230 * k))))
    c.restore()
    text_c(c, "REWIND", W / 2, 790, font("Anton", 70), C(255, 255, 255, int(230 * k)), OUT, 10)

def s_bedroom(c, t, T):
    sx, sy = shake(t, 2.5 * clamp((t - 0.3) * 3), 40)
    c.save(); cam(c, lerp(1.08, 1.0, ease_out(t / 2.5)), W / 2, 1200, sx, sy)
    rect(c, -300, 0, W + 300, H, lin(c, 0, 0, 0, H, [C(196, 168, 140), C(150, 120, 100)]))
    def outside(c2, tt):
        sky(c2, C(250, 140, 70), C(120, 60, 60), 600, 1250)
        skyline(c2, 5, 1250, 120, 380, C(60, 40, 50), x0=600, x1=1100)
        smoke(c2, 820, 1100, tt + 3, 0.6, 1); fire_glow(c2, 760, 1200, 160, tt)
    window_frame(c, 640, 700, 380, 470, outside, t)
    rect(c, -400, 1500, W + 400, H + 700, fill(C(120, 86, 66)))
    c.drawLine(-300, 1500, W + 300, 1500, stroke(OUT, 10))
    outlined_rect(c, 160, 1160, 240, 1500, C(150, 96, 58), 8, 10)
    outlined_rect(c, 160, 1400, 820, 1470, C(150, 96, 58), 8, 10)
    outlined_rect(c, 210, 1320, 810, 1405, C(240, 240, 250), 7, 26)
    up = ease_out(clamp((t - 0.35) / 0.3))
    p = mix(pose(lean=-40, head=-10, ulL=86, ulR=88, llL=0, llR=0, uaL=10, laL=10, uaR=20, laR=10),
            pose(lean=6, head=4, ulL=86, ulR=88, llL=0, llR=0, uaL=50, laL=-100, uaR=60, laR=-110), up)
    stick(c, 380, 1350, 340, p, HERO, face=1, expr="sleep" if up < 0.3 else "shock", look=1, scarf_t=t)
    outlined_rect(c, 410, 1300, 810, 1400, C(90, 130, 200), 7, 30)
    if t < 0.4:
        text_c(c, "z z z", 420, 1120, font("Lucky", 60), C(255, 255, 255, 200))
    c.restore()
    k = back_out(clamp((t - 0.25) / 0.35))
    if k > 0:
        c.save(); c.translate(780, 900); c.scale(k * 0.75, k * 0.75)
        phone(c, 0, 0, 1.0, t, "calls", buzz=1.0)
        for i in range(3):
            a = (t * 2 + i / 3) % 1
            c.drawArc(skia.Rect.MakeLTRB(-230 - a * 120, -330 - a * 120, 230 + a * 120, 330 + a * 120), -40, 80, False, stroke(C(255, 255, 255, int(200 * (1 - a))), 8))
        c.restore()

def s_street(c, t, T):
    z = 1.0 + 0.35 * ease((t - 3.9) / 1.6)
    cx = lerp(W / 2, 760, ease((t - 3.9) / 1.6))
    c.save(); cam(c, z, cx, lerp(960, 1080, ease((t - 3.9) / 1.6)), *shake(t, 2))
    sky(c, C(240, 130, 70), C(110, 60, 70), 0, 1200)
    skyline(c, 31, 1100, 300, 700, C(80, 54, 64), C(255, 200, 140), 0.06, t=t)
    smoke(c, 300, 1000, t, 1.3, 2); smoke(c, 860, 900, t + 2, 1.0, 3)
    fire_glow(c, 300, 1050, 220, t)
    rect(c, -400, 1300, W + 400, H + 700, fill(C(70, 64, 76)))
    rect(c, -300, 1290, W + 300, 1320, fill(C(120, 110, 120)))
    for i in range(-2, 8):
        x = (i * 260 - t * 40) % 1560 - 300
        rect(c, x, 1600, x + 140, 1620, fill(C(220, 210, 120)))
    # car wreck
    outlined_rect(c, 60, 1440, 420, 1560, C(80, 120, 190), 8, 30); outlined_rect(c, 140, 1370, 340, 1450, C(80, 120, 190), 8, 24)
    for x in (130, 350): c.drawCircle(x, 1560, 42, fill(OUT)); c.drawCircle(x, 1560, 22, fill(C(140, 140, 150)))
    smoke(c, 360, 1400, t + 1, 0.5, 9, (60, 60, 70))
    # runners
    rnd = random.Random(4)
    for i in range(7):
        sp = rnd.uniform(650, 900); st = CIVS[i % len(CIVS)]; gy = rnd.choice([1520, 1600, 1700, 1780])
        x = (W + 300 - (t * sp + i * 420) % (W + 700))
        stick(c, x, gy, rnd.uniform(240, 300), run(t * 13 + i), st, face=-1, expr="shock", look=0.4)
    # walkers
    if t > 2.3:
        for i, (gy, s, x0) in enumerate(((1560, 250, 1180), (1700, 300, 1320), (1820, 340, 1150))):
            x = x0 - (t - 2.3) * 70
            stick(c, x, gy, s, zwalk(t * 3.4 + i * 2), ZOMB, face=-1, expr="z")
    c.restore()

def s_barricade(c, t, T):
    c.save(); cam(c, 1.0, W / 2, 960, *shake(t, 6 * max(0, 1 - ((t - 0.7) % 0.85) * 5) if t > 0.6 else 0))
    rect(c, -400, 0, W + 400, H, lin(c, 0, 0, 0, H, [C(150, 140, 120), C(110, 100, 90)]))
    rect(c, -400, 1500, W + 400, H + 700, fill(C(100, 74, 58))); c.drawLine(0, 1500, W, 1500, stroke(OUT, 10))
    door(c, 90, 760, 300, 740)
    items = [(0.55, "couch"), (1.35, "fridge"), (2.05, "tv"), (2.65, "chair"), (3.15, "lamp"), (3.6, "plant")]
    for i, (ta, kind) in enumerate(items):
        k = ease_out(clamp((t - ta + 0.5) / 0.5))
        if k <= 0: continue
        drop = 1 - ease_out(clamp((t - ta) / 0.18)) if kind in ("tv", "lamp", "plant", "chair") else 0
        if kind == "couch":
            x = lerp(900, 80, k); outlined_rect(c, x, 1310, x + 420, 1500, C(200, 70, 70), 8, 26); outlined_rect(c, x + 20, 1240, x + 400, 1330, C(220, 90, 90), 8, 24)
        elif kind == "fridge":
            x = lerp(900, 180, k); outlined_rect(c, x, 760, x + 200, 1240, C(235, 240, 245), 8, 18); c.drawLine(x + 170, 820, x + 170, 980, stroke(OUT, 8))
        elif kind == "tv":
            y = 640 - drop * 500; outlined_rect(c, 110, y, 380, y + 120, C(40, 40, 50), 8, 10); rect(c, 125, y + 14, 365, y + 106, fill(C(60, 80, 120)))
        elif kind == "chair":
            y = 1240 - drop * 600; outlined_rect(c, 420, y - 160, 450, y, C(150, 96, 58), 6, 4); outlined_rect(c, 410, y - 30, 540, y, C(150, 96, 58), 6, 4)
        elif kind == "lamp":
            y = 520 - drop * 500; c.drawLine(300, y, 300, y + 120, stroke(OUT, 10))
            tri = skia.Path(); tri.moveTo(250, y + 20); tri.lineTo(350, y + 20); tri.lineTo(320, y - 50); tri.lineTo(280, y - 50); tri.close()
            c.drawPath(tri, fill(C(250, 210, 90))); c.drawPath(tri, stroke(OUT, 7))
        elif kind == "plant":
            y = 760 - drop * 500; plant(c, 200, y, 0.4, t, False, 0.2)
    hx = lerp(900, 640, ease((t % 0.85) / 0.6)) if t < 3.8 else 640
    stick(c, hx, 1500, 330, push(t) if t < 3.8 else pose(lean=-6, uaL=-150, laL=-20, uaR=40, laR=-110), HERO, face=-1,
          expr="angry" if t < 3.8 else "happy", look=0.5, scarf_t=t, wind=0.3)
    c.restore()

def s_beans(c, t, T):
    z = 1.0 + 0.55 * ease_out(clamp((t - 3.35) / 0.35))
    c.save(); cam(c, z, lerp(W / 2, 450, ease_out(clamp((t - 3.35) / 0.35))), lerp(960, 1000, ease_out(clamp((t - 3.35) / 0.35))), *shake(t, 4 if t > 3.35 else 0))
    rect(c, 0, 0, W, H, fill(C(46, 38, 50)))
    fire_glow(c, 560, 1040, 700, t)
    rect(c, -400, 1500, W + 400, H + 700, fill(C(60, 44, 40)))
    outlined_rect(c, 540, 1180, 1000, 1220, C(150, 96, 58), 8, 6)
    for x in (570, 970): c.drawLine(x, 1220, x, 1500, stroke(OUT, 14))
    c.drawLine(780, 1180, 780, 1130, stroke(C(240, 230, 200), 22)); c.drawCircle(780, 1110, 12, glow(C(255, 200, 80), 10))
    n = 3 if t < 1.5 else 2
    for i in range(n): can(c, 640 + i * 90 + (60 if i == 2 else 0), 1180, 0.9)
    k = t * 2.4
    eat = pose(lean=6, ulL=86, llL=86, ulR=88, llR=88, uaL=40, laL=-100, uaR=30 + 15 * math.sin(k), laR=-120 - 20 * math.sin(k), head=8)
    hipy = 1500 - foot_drop(eat, 330)
    outlined_rect(c, 330, hipy + 8, 470, hipy + 36, C(150, 96, 58), 6, 4); c.drawLine(350, hipy + 36, 350, 1500, stroke(OUT, 12)); c.drawLine(450, hipy + 36, 450, 1500, stroke(OUT, 12))
    stick(c, 400, 1500, 330, eat, HERO, face=1, expr="sad" if t < 3.3 else "disgust", look=0.8, scarf_t=t)
    can(c, 520, 1160 + 30 * math.sin(k), 0.7, rot=-20)
    if t > 3.4:
        a = clamp((t - 3.4) / 0.2)
        text_c(c, "BLEGH!", 420, 1000, font("Lucky", 110), C(160, 220, 80, int(255 * a)), OUT, 18)
    c.restore()

def s_biscuit(c, t, T):
    open_k = ease(clamp((t - 4.8) / 0.6))
    zoom = 1.0 + 0.1 * ease(t / 4.8) - 0.1 * open_k
    c.save(); cam(c, zoom, W / 2, 1000, *shake(t, 2 if t < 4.8 else 0))
    rect(c, 0, 0, W, H, lin(c, 0, 0, 0, H, [C(70, 64, 80), C(46, 40, 54)]))
    rect(c, -400, 1500, W + 400, H + 700, fill(C(70, 54, 46))); c.drawLine(0, 1500, W, 1500, stroke(OUT, 10))
    light = C(255, 236, 180)
    door(c, 360, 760, 330, 740, open_k, light=light)
    if open_k > 0.05:
        c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), rad(525, 1300, 700, [C(255, 230, 160, int(120 * open_k)), C(255, 230, 160, 0)]))
    if t < 4.9:
        for i in range(3):
            a = (t * 1.6 + i / 3) % 1
            sx = 690 + 10; sy = 1380 - i * 30
            c.drawLine(sx + 10, sy, sx + 50 + a * 30, sy - 20, stroke(C(255, 255, 255, int(200 * (1 - a))), 6))
        text_c(c, "scratch scratch", 760, 1300, font("Lucky", 46), C(255, 255, 255, 170 if (t % 0.8) < 0.5 else 60))
    if open_k > 0.3:
        dog(c, 520, 1500, 210, t, face=-1, mode="sit" if t < 6.3 else "stand", wag=1.6)
        if t > 6.2:
            for i in range(4):
                a = ((t - 6.2) * 0.9 + i * 0.25) % 1
                heart(c, 470 + math.sin(i * 2 + t * 2) * 80, 1150 - a * 380, 36, int(255 * (1 - a)))
    hp = mix(pose(lean=-10, uaR=-150, laR=-10, uaL=50, laL=-110, ulL=-14, llL=14, ulR=10), pose(lean=10, uaL=60, laL=-30, uaR=70, laR=-20, ulR=30, llR=40, ulL=-20, llL=30), ease(clamp((t - 6.4) / 0.5)))
    if t < 4.8: hp["bob"] = 0.006 * math.sin(t * 30)
    stick(c, 830, 1500, 330, hp, HERO, face=-1, expr="worry" if t < 4.8 else ("shock" if t < 6.0 else "happy"), look=0.6, blink=blink_at(t), scarf_t=t)
    if t < 6.3:   # frying pan in the raised hand
        J = joints(hp, 330); hx_, hy_ = J["handR"]
        hipy = 1500 - foot_drop(hp, 330)
        px, py = 830 - hx_, hipy + hy_
        c.drawLine(px, py, px - 30, py - 70, stroke(OUT, 14)); c.drawCircle(px - 50, py - 120, 60, fill(OUT)); c.drawCircle(px - 50, py - 120, 50, fill(C(60, 60, 70)))
    c.restore()
    if t > 6.4:
        k = back_out(clamp((t - 6.4) / 0.4))
        c.save(); c.translate(W / 2, 1010); c.scale(k, k)
        rrect(c, -230, -80, 230, 40, 30, fill(C(254, 97, 0))); c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-230, -80, 230, 40), 30, 30), stroke(OUT, 10))
        text_c(c, "BISCUIT", 0, 12, font("Lucky", 96), C(255, 255, 255), OUT, 12)
        c.restore()

def market_bg(c, t, cam_x, tremble=0.0):
    rect(c, -2000, 0, 6000, H, lin(c, 0, 0, 0, H, [C(60, 74, 80), C(36, 44, 52)]))
    for i in range(-2, 14):
        x = i * 420 - cam_x * 0.5
        rect(c, x, 300, x + 200, 330, fill(C(220, 240, 240, 90)))
    for i in range(-2, 14):
        shelf(c, i * 560 - cam_x * 0.8, 820, 480, 660, seed=i, t=t, tremble=tremble)
    rect(c, -2000, 1500, 6000, H + 700, fill(C(150, 160, 160))); c.drawLine(-2000, 1500, 6000, 1500, stroke(OUT, 10))
    for i in range(-2, 30): rect(c, i * 200 - cam_x % 200, 1500, i * 200 - cam_x % 200 + 6, H, fill(C(120, 130, 130)))

def s_market(c, t, T):
    hx = 120 + t * 95
    cam_x = hx - 420
    c.save(); cam(c, 1.0, W / 2, 960, 0, 0)
    c.save(); c.translate(0, 0); market_bg(c, t, cam_x); c.restore()
    for i, zx in enumerate((900, 1350, 1800)):
        x = zx - cam_x
        stick(c, x, 1500, 320, zwalk(t * 0.6 + i, 0.15), ZOMB, face=1, expr="z")
    stick(c, hx - cam_x, 1500, 300, sneak(t * 3.0), HERO, face=1, expr="worry", look=0.5, blink=blink_at(t), scarf_t=t)
    dog(c, hx - cam_x - 170, 1500, 140, t, face=1, mode="walk", ph=t * 5, wag=0.3, expr="neutral")
    c.restore()
    if t > 4.5:
        k = back_out(clamp((t - 4.5) / 0.35))
        c.save(); c.translate(W / 2, 960); c.scale(k, k)
        pill = font("Anton", 64)
        rrect(c, -200, -70, 200, 20, 20, fill(C(220, 40, 40))); c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-200, -70, 200, 20), 20, 20), stroke(OUT, 8))
        text_c(c, "RULE #1", 0, -2, pill, C(255, 255, 255))
        text_c(c, "DON'T MAKE A SOUND", 0, 100, font("Lucky", 62), C(255, 255, 255), OUT, 14)
        c.restore()

def s_can(c, t, T):
    z = 1.9
    c.save(); cam(c, z, 600, 1150, *shake(t, 14 if 1.15 < t < 1.6 else 0, 50))
    market_bg(c, t, 360, tremble=4 if t < 0.5 else 0)
    dog(c, 470, 1500, 150, t, face=1, mode="stand", wag=0.2, expr="neutral")
    # falling can (slow motion)
    k = clamp((t - 0.15) / 1.0)
    fx = 640 + 120 * k; fy = 1150 + 350 * (k ** 2.2); rot = 220 * k
    if t < 1.15: can(c, fx, fy, 0.8, rot)
    else:
        can(c, 790, 1500, 0.8, 90 + 30 * math.sin((t - 1.15) * 20) * max(0, 1 - (t - 1.15) * 2))
        a = clamp((t - 1.15) / 0.5)
        for i in range(3):
            r = 40 + a * 300 + i * 50
            c.drawCircle(790, 1480, r, stroke(C(255, 255, 255, int(220 * (1 - a))), 8))
    c.restore()
    if t > 1.15:
        k2 = back_out(clamp((t - 1.15) / 0.25))
        c.save(); c.translate(W / 2, 700); c.rotate(-8); c.scale(k2, k2)
        text_c(c, "CLANG!", 0, 0, font("Lucky", 190), C(255, 214, 10), OUT, 24)
        c.restore()
    if t < 1.1:
        c.save(); c.translate(W / 2, 600)
        text_c(c, "!", 0, 0, font("Lucky", 160), C(255, 255, 255, int(255 * clamp(t * 4))), OUT, 20)
        c.restore()

def s_heads(c, t, T):
    c.save(); cam(c, 1.0 + 0.06 * t, W / 2, 960, *shake(t, 3))
    rect(c, 0, 0, W, H, lin(c, 0, 0, 0, H, [C(40, 20, 30), C(20, 10, 16)]))
    for i in range(4):
        x = 150 + i * 260; turn = ease_out(clamp((t - 0.15 - i * 0.22) / 0.25))
        face = 1 if turn > 0.5 else -1
        p = pose(lean=4, head=lerp(-30, 10, turn), uaL=10, uaR=10)
        stick(c, x, 2300 - (i % 2) * 120, 1300, p, ZOMB, face=face, expr="z", look=lerp(-0.6, 0.0, turn))
    c.restore()
    if t > 0.9:
        a = 0.35 * (0.5 + 0.5 * math.sin(t * 14))
        p = fill(C(255, 0, 0, int(255 * a))); p.setBlendMode(skia.BlendMode.kScreen); c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), p)

def s_chase(c, t, T):
    hx = t * 900
    c.save(); cam(c, 1.0, W / 2, 960, *shake(t, 9, 40))
    market_bg(c, t, hx - 620)
    for i in range(6):
        zx = 400 - i * 105 + math.sin(t * 3 + i) * 25 - max(0, 0.8 - t) * 400
        stick(c, zx, 1500 + (i % 2) * 30, 330 + (i % 3) * 20, run(t * 11 + i, 0.75), ZOMB, face=1, expr="z")
    stick(c, 660, 1500, 330, run(t * 15), HERO, face=1, expr="scared", look=-0.6, scarf_t=t, wind=1.0)
    dog(c, 860, 1500, 150, t, face=1, mode="run", ph=t * 22, wag=0.2)
    c.restore()
    speed_lines(c, t, 1.0)

def day_sky(c, k):
    """k 0..1: one full day (dawn -> noon -> dusk -> night -> dawn)."""
    cols = [(255, 170, 120), (120, 190, 255), (255, 140, 90), (20, 24, 60), (255, 170, 120)]
    i = min(3, int(k * 4)); f = k * 4 - i
    a = cols[i]; b = cols[i + 1]
    top = C(*(lerp(a[j], b[j], f) * 0.8 for j in range(3))); bot = C(*(lerp(a[j], b[j], f) for j in range(3)))
    sky(c, top, bot, 0, 1500)
    ang = k * 2 * math.pi
    sx, sy = W / 2 - math.cos(ang) * 520, 1100 - math.sin(ang) * 800
    c.drawCircle(sx, sy, 90, rad(sx, sy, 180, [C(255, 230, 120, 180), C(255, 230, 120, 0)])); c.drawCircle(sx, sy, 60, fill(C(255, 236, 140)))
    mx, my = W / 2 + math.cos(ang) * 520, 1100 + math.sin(ang) * 800
    moon(c, mx, my, 50)

def farm(c, t, grow, storm=0.0, sky_k=0.3, hero=True, hero_pose=None, expr="neutral", plants_alive=1.0):
    if storm > 0:
        sky(c, C(16, 18, 30), C(40, 44, 60), 0, 1500)
    else:
        day_sky(c, sky_k)
    skyline(c, 41, 1250, 250, 560, C(60, 70, 100) if storm == 0 else C(24, 26, 40), C(255, 220, 140), 0.05)
    rect(c, -400, 1350, W + 400, H + 700, fill(C(90, 90, 110) if storm == 0 else C(44, 44, 56)))
    c.drawLine(-300, 1350, W + 300, 1350, stroke(OUT, 12))
    for i, x in enumerate((180, 420, 660)):
        if plants_alive <= i / 3:
            outlined_rect(c, x - 90 + storm * 40, 1280, x + 90 + storm * 40, 1350, C(130, 84, 50), 7, 6)
            continue
        plant(c, x, 1350, grow, t, True, sway=1.0 + storm * 6)
    barrel(c, 900, 1350, clamp(0.2 + grow * 0.6), rot=storm * -70)
    if hero:
        stick(c, 760, 1350, 300, hero_pose or idle(t), HERO, face=-1, expr=expr, look=0.4, blink=blink_at(t), scarf_t=t, wind=0.3 + storm)

def s_farm(c, t, T):
    grow = ease(clamp(t / 7.0))
    k = (t - 4.0) / 4.2
    sky_k = 0.3 if k < 0 else (0.3 + k * 6) % 1.0
    c.save(); cam(c, 1.05 - 0.05 * ease(t / 8), W / 2, 1000)
    if t < 4.0:
        hp = pose(lean=10, uaR=70, laR=10, uaL=-10, head=8)
        farm(c, t, grow, sky_k=sky_k, hero_pose=hp, expr="happy")
        # watering can arc of water
        for i in range(10):
            a = (t * 3 + i / 10) % 1
            c.drawCircle(560 - a * 120, 1060 + a * a * 230, 7, fill(C(120, 190, 255, int(220 * (1 - a)))))
    else:
        hp = pose(lean=-4, ulL=86, llL=86, ulR=88, llR=88, uaL=60, laL=-140, uaR=20, laR=40, head=-10, bob=-0.13)
        farm(c, t, grow, sky_k=sky_k, hero_pose=hp, expr="sad")
        dog(c, 560, 1350, 120, t, face=1, mode="sit", wag=0.1, expr="neutral")
    c.restore()

def hallway(c, t, flick):
    rect(c, 0, 0, W, H, lin(c, 0, 0, 0, H, [C(50, 48, 60), C(28, 26, 34)]))
    rect(c, -400, 1500, W + 400, H + 700, fill(C(40, 34, 36))); c.drawLine(0, 1500, W, 1500, stroke(OUT, 10))
    for x in (0, 360, 720, 1080): c.drawLine(x, 300, x, 1500, stroke(C(36, 34, 44), 6))
    c.drawLine(540, 0, 540, 220, stroke(OUT, 6)); c.drawCircle(540, 240, 28, fill(C(255, 240, 180, int(255 * flick))))
    c.drawCircle(540, 240, 500, rad(540, 240, 700, [C(255, 230, 160, int(90 * flick)), C(255, 230, 160, 0)]))

def s_learning(c, t, T):
    flick = 0.25 + 0.75 * (1 if (math.sin(t * 9) + math.sin(t * 23)) > -0.6 else 0.2)
    handle_k = ease(clamp((t - 5.3) / 0.6)); open_k = ease(clamp((t - 6.3) / 1.0)) * 0.55
    if t < 4.8:
        zoom, cx, cy = 1.3 + 0.04 * t, 600, 1150
    elif t < 8.0:
        k = ease_out(clamp((t - 4.8) / 0.5)); zoom, cx, cy = lerp(1.5, 2.3, k), lerp(600, 360, k), lerp(1150, 1130, k)
    else:
        k = ease_out(clamp((t - 8.0) / 0.35)); zoom, cx, cy = lerp(2.3, 3.0, k), lerp(360, 280, k), lerp(1130, 940, k)
    c.save(); cam(c, zoom, cx, cy, *shake(t, 1.5))
    hallway(c, t, flick)
    door(c, 150, 760, 300, 740, open_k, col=C(110, 80, 60), knob=False)
    if open_k > 0.02:
        stick(c, 300, 1500, 360, zwalk(0.3, 0.1), ZOMB, face=1, expr="z", alpha=int(255 * clamp(open_k * 3)))
    # lever handle
    dw = 300 * (1 - 0.82 * ease(open_k / 0.55 * 0.55))
    hx, hy = 150 + dw * 0.86, 1130
    c.save(); c.translate(hx, hy); c.rotate(32 * handle_k)
    c.drawCircle(0, 0, 18, fill(OUT)); rrect(c, -80, -12, 6, 12, 10, fill(OUT)); rrect(c, -74, -7, 2, 7, 7, fill(C(200, 200, 210)))
    if t > 5.0:
        a = clamp((t - 5.0) / 0.3)
        c.saveLayerAlpha(None, int(255 * a))
        for i in range(4): rrect(c, -70 + i * 16, -26, -58 + i * 16, 14, 6, fill(ZOMB["body"]))
        rrect(c, -78, -30, -4, -6, 10, fill(ZOMB["head"])); c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-78, -30, -4, -6), 10, 10), stroke(OUT, 4))
        c.restore()
    c.restore()
    # hero peeking around the corner
    stick(c, 900, 1500, 330, pose(lean=-14, head=-10, uaL=60, laL=-100, uaR=40, laR=-90), HERO, face=-1, expr="shock" if t > 1.0 else "worry", look=0.4, scarf_t=t)
    rect(c, 960, 300, 1200, 1500, fill(C(36, 34, 44))); c.drawLine(960, 300, 960, 1500, stroke(OUT, 8))
    c.restore()
    if t < 4.6:
        hb = (t % 0.9)
        a = max(0, 1 - hb * 4)
        vignette(c, 0.5 + 0.3 * a)
    grade(c, C(170, 190, 230), skia.BlendMode.kMultiply)

def s_storm(c, t, T):
    flash = max(lightning_val(t, 0.5), lightning_val(t, 2.1), lightning_val(t, 3.3))
    c.save(); cam(c, 1.0, W / 2, 1000, *shake(t, 5 + 10 * flash))
    alive = 1.0 - ease(clamp((t - 1.0) / 2.0))
    farm(c, t, 1.0 * alive + 0.0001, storm=0.4 + 0.6 * ease(clamp(t / 1.5)), hero_pose=pose(lean=-20, uaL=-120, laL=-30, uaR=-110, laR=-40, ulL=-24, llL=20, ulR=10, llR=30), expr="shock", plants_alive=alive)
    rnd = random.Random(int(t * 20))
    for i in range(8):     # leaves and tomatoes flying
        a = ((t * 0.7 + i / 8) % 1)
        x = W + 100 - a * (W + 400); y = 1100 - math.sin(a * 6 + i) * 200 - i * 40
        if i % 3 == 0: c.drawCircle(x, y, 16, fill(C(230, 50, 40)))
        else: c.drawOval(skia.Rect.MakeLTRB(x - 26, y - 12, x + 26, y + 12), fill(C(60, 160, 70)))
    lightning(c, 0.5, t, 1); lightning(c, 2.1, t, 2); lightning(c, 3.3, t, 3)
    c.restore()
    rain(c, t, 260, ang=-0.35)
    if flash > 0:
        p = fill(C(220, 230, 255, int(150 * flash))); p.setBlendMode(skia.BlendMode.kScreen); c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), p)

def lightning_val(t, t0):
    k = t - t0
    return 0 if (k < 0 or k > 0.35) else (1 - k / 0.35)

def s_stairs(c, t, T):
    c.save(); cam(c, 1.0, W / 2, 960, *shake(t, 3))
    rect(c, -200, -300, W + 200, H + 600, lin(c, 0, 0, 0, H, [C(40, 36, 46), C(24, 20, 30)]))
    red = 0.5 + 0.5 * math.sin(t * 5)
    c.drawCircle(820, 500, 700, rad(820, 500, 900, [C(255, 40, 40, int(80 * red)), C(255, 40, 40, 0)]))
    n = 13; dx, dy = 66, 78; x0, y0 = -40, 1900
    for i in range(n):
        x = x0 + i * dx; y = y0 - i * dy
        outlined_rect(c, x, y, x + dx + 8, y0 + 200, C(90, 86, 100), 6, 2)
    top_y = y0 - (n - 1) * dy
    rect(c, x0 + n * dx, top_y, W + 200, y0 + 200, fill(C(90, 86, 100)))
    c.drawLine(x0 + n * dx, top_y, W + 200, top_y, stroke(OUT, 8))
    door(c, 900, top_y - 520, 170, 520, 0, col=C(120, 90, 70))
    for j in range(5):
        pos = clamp(1.5 + j * 2.2 + t * 0.55, 0, n - 1.5)
        i = (n - 1.5) - (j * 2.2) + t * 0.55 - 1.5
        i = max(0.0, min(n - 2.2, i))
        gx = x0 + i * dx + dx * 0.5; gy = y0 - int(i) * dy - (i - int(i)) * dy
        stick(c, gx, gy, 300, zwalk(t * 3 + j), ZOMB, face=1, expr="z")
    stick(c, 920, top_y, 320, brace(t), HERO, face=-1, expr="scared", look=-0.5, scarf_t=t)
    dog(c, 1040, top_y, 120, t, face=-1, mode="stand", wag=0.0, expr="neutral")
    c.restore()

def s_idea(c, t, T):
    z = 1.0 + 0.15 * ease(clamp((t - 1.8) / 1.2))
    c.save(); cam(c, z, W / 2, lerp(960, 900, ease(clamp((t - 1.8) / 1.2))))
    hp = idle(t) if t < 1.8 else (pose(uaR=-150, laR=-30, uaL=-10, head=-6) if t < 5.3 else hold_phone(t))
    roof_scene(c, t, hero_pose=hp, expr="worry" if t < 1.8 else ("determined" if t < 5.3 else "happy"), look=0.3, dog_mode="sit")
    c.restore()
    if 1.8 < t < 5.3:
        k = back_out(clamp((t - 1.8) / 0.3))
        c.save(); c.translate(540, 470); c.scale(k, k)
        c.drawCircle(0, 0, 110, glow(C(255, 230, 100, 140), 40))
        c.drawCircle(0, 0, 70, fill(OUT)); c.drawCircle(0, 0, 62, fill(C(255, 230, 100)))
        rect(c, -30, 50, 30, 100, fill(OUT)); rect(c, -24, 54, 24, 94, fill(C(180, 180, 190)))
        for i in range(8):
            a = math.radians(i * 45); c.drawLine(math.cos(a) * 90, math.sin(a) * 90, math.cos(a) * 130, math.sin(a) * 130, stroke(C(255, 230, 100), 10))
        c.restore()
    if t > 5.3:
        k = back_out(clamp((t - 5.3) / 0.35))
        vol = ease(clamp((t - 6.4) / 0.8))
        c.save(); c.translate(540, 760); c.scale(1.5 * k, 1.5 * k); phone(c, 0, 0, 1.0, t, "music", buzz=0.25 * vol, vol=vol); c.restore()
        if vol > 0.2:
            music_notes(c, [(300 + ((t * 0.6 + i * 0.3) % 1) * 60, 900 - ((t * 0.6 + i * 0.3) % 1) * 500, 1 - ((t * 0.6 + i * 0.3) % 1)) for i in range(3)] +
                           [(780 - ((t * 0.5 + i * 0.3) % 1) * 60, 900 - ((t * 0.5 + i * 0.3) % 1) * 500, 1 - ((t * 0.5 + i * 0.3) % 1)) for i in range(3)], t)

def s_throw(c, t, T):
    tilt = ease(clamp((t - 1.9) / 1.0))
    c.save(); cam(c, lerp(1.0, 0.9, tilt), W / 2, lerp(960, 1350, tilt))
    k = clamp(t / 0.9)
    def extra(c2, tt):
        if t > 0.5:
            q = clamp((t - 0.5) / 1.6)
            px = lerp(560, 1150, q); py = 640 - math.sin(q * math.pi) * 420 + q * q * 900
            c2.save(); c2.translate(px, py); c2.rotate(q * 900); phone(c2, 0, 0, 0.35, tt, "music"); c2.restore()
            music_notes(c2, [(px - 60 - i * 70, py + 40 + i * 30, 0.9 - i * 0.25) for i in range(3)], tt)
    sky(c, *NIGHT); stars(c, 7, 90, 900, t); moon(c, 840, 330, 70)
    skyline(c, 21, 1250, 250, 560, C(30, 26, 58), C(120, 110, 170), 0.12, t=t)
    skyline(c, 22, 1380, 200, 450, C(22, 20, 42), C(255, 200, 120), 0.08, t=t, flicker=1)
    building_facade(c, 170, 910, 800, H + 600, t)
    hstart = 2.0
    if t < hstart: horde(c, t, 5, 1560, 1980, -120, W + 120, 120, 250)
    else: horde(c, t - hstart, 5, 1560, 1980, -120, W + 120, 120, 250, dir_=1, speed=260)
    extra(c, t)
    stick(c, 540, 800, 300, throw(k), HERO, face=1, expr="determined", look=0.5, scarf_t=t, wind=0.8)
    dog(c, 380, 800, 150, t, face=1, mode="sit", wag=1.0)
    c.restore()

def s_day100(c, t, T):
    open_k = ease(clamp((t - 0.3) / 0.7))
    walk_k = clamp((t - 1.0) / 6.0)
    z = 1.0 + 0.06 * ease(t / 7)
    c.save(); cam(c, z, lerp(W / 2, 620, ease(walk_k)), 1000)
    sky(c, C(255, 170, 140), C(255, 226, 170), -300, 1300)
    c.drawCircle(860, 760, 260, rad(860, 760, 420, [C(255, 240, 180, 200), C(255, 240, 180, 0)])); c.drawCircle(860, 760, 110, fill(C(255, 244, 200)))
    skyline(c, 51, 1150, 260, 600, C(150, 110, 130), C(255, 230, 190), 0.04, x0=-400, x1=1700)
    rect(c, -400, 1300, 1700, H + 400, fill(C(120, 110, 120)))
    rect(c, -400, 1290, 1700, 1320, fill(C(170, 160, 160)))
    building_facade(c, -360, 330, 300, 1300, t, lit=0.0, col=C(110, 96, 120))
    door(c, 80, 940, 220, 360, open_k, col=C(120, 90, 70), light=C(30, 26, 34))
    for i, x in enumerate((700, 980, 1240)):         # debris and papers
        outlined_rect(c, x, 1460 + i * 30, x + 90, 1490 + i * 30, C(200, 190, 170), 4, 4)
    pa = (t * 0.35) % 1
    c.save(); c.translate(-100 + pa * 1500, 1400 - math.sin(pa * 9) * 80); c.rotate(pa * 700)
    rect(c, -30, -20, 30, 20, fill(C(240, 236, 220))); c.restore()
    hx = 190 + ease(walk_k) * 620
    stick(c, hx, 1560, 320, walk(t * 6.5) if walk_k < 1 else idle(t), HERO, face=1, expr="worry", look=0.6, blink=blink_at(t), scarf_t=t, wind=0.4)
    dog(c, hx - 170, 1560, 140, t, face=1, mode="walk" if walk_k < 1 else "stand", ph=t * 7, wag=0.4, expr="neutral")
    c.restore()

def s_quiet(c, t, T):
    z = 1.0 + 0.25 * ease(t / 1.3)
    c.save(); cam(c, z, 700, 1250)
    sky(c, C(110, 90, 110), C(150, 120, 130), -300, 1300)
    skyline(c, 51, 1150, 260, 600, C(80, 60, 80), None, 0, x0=-400, x1=1700)
    rect(c, -400, 1300, 1700, H + 400, fill(C(80, 74, 84)))
    rect(c, 340, 700, 560, 1560, fill(C(14, 12, 20)))       # dark alley
    for i in range(5):
        a = clamp((t - 0.25 - i * 0.12) / 0.15)
        if a <= 0: continue
        ex, ey = 380 + (i * 47) % 150, 900 + (i * 131) % 520
        for dx in (-14, 14):
            c.drawCircle(ex + dx, ey, 16, glow(C(255, 60, 40, int(160 * a)), 8)); c.drawCircle(ex + dx, ey, 7, fill(C(255, 120, 90, int(255 * a))))
    stick(c, 810, 1560, 320, idle(t), HERO, face=-1, expr="worry", look=-0.6, scarf_t=t)
    dog(c, 980, 1560, 140, t, face=-1, mode="stand", wag=0.0, expr="neutral")
    c.restore()
    vignette(c, 0.8)

def s_cta(c, t, T):
    rect(c, 0, 0, W, H, lin(c, 0, 0, 0, H, [C(30, 22, 60), C(12, 10, 24)]))
    for i in range(14):
        a = (t * 0.3 + i / 14) % 1
        c.drawCircle((i * 157) % W, H - a * H, 6, fill(C(255, 214, 10, int(120 * (1 - a)))))
    k = back_out(clamp(t / 0.35))
    c.save(); c.translate(W / 2, 560); c.scale(k, k)
    text_c(c, "WANT PART 2?", 0, 0, font("Lucky", 128), C(255, 255, 255), OUT, 22)
    c.restore()
    k2 = back_out(clamp((t - 0.9) / 0.35))
    c.save(); c.translate(W / 2, 800); c.scale(k2, k2)
    rrect(c, -420, -110, 420, 60, 40, fill(C(255, 255, 255))); c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-420, -110, 420, 60), 40, 40), stroke(OUT, 10))
    tail = skia.Path(); tail.moveTo(-260, 55); tail.lineTo(-300, 130); tail.lineTo(-190, 55); tail.close(); c.drawPath(tail, fill(C(255, 255, 255)))
    text_c(c, "COMMENT \"BISCUIT\"", 0, 0, font("Lucky", 76), C(254, 97, 0))
    c.restore()
    dog(c, W / 2 - 60, 1560, 380, t, face=1, mode="stand", wag=1.8)
    if (t % 0.6) < 0.25 and t > 1.2:
        text_c(c, "WOOF!", 800, 1080, font("Lucky", 90), C(255, 214, 10), OUT, 14)

ICON = None
def s_end(c, t, T):
    global ICON
    if ICON is None:
        ICON = skia.Image.open("icon-512.png")
    rect(c, 0, 0, W, H, fill(C(17, 17, 17)))
    c.drawCircle(W / 2, 1500, 900, rad(W / 2, 1500, 900, [C(120, 50, 10, 200), C(17, 17, 17, 0)]))
    k = back_out(clamp(t / 0.4))
    c.save(); c.translate(W / 2, 760); c.scale(k, k)
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-190, -190, 190, 190), 80, 80)
    c.save(); c.clipRRect(rr, True); c.drawImageRect(ICON, skia.Rect.MakeLTRB(-190, -190, 190, 190), skia.SamplingOptions(skia.FilterMode.kLinear)); c.restore()
    c.restore()
    a = int(255 * clamp((t - 0.2) / 0.3))
    text_c(c, "FRAMEY", W / 2, 1110, font("Lucky", 150), C(255, 255, 255, a))
    text_c(c, "THE STOP-MOTION APP", W / 2, 1200, font("Anton", 60), C(200, 200, 210, a))
    k3 = back_out(clamp((t - 0.6) / 0.3))
    c.save(); c.translate(W / 2, 1330); c.scale(k3, k3)
    rrect(c, -250, -60, 250, 50, 55, fill(C(254, 97, 0)))
    text_c(c, "COMING SOON", 0, 20, font("Anton", 64), C(17, 17, 17))
    c.restore()

# (start, end, fn, day, transition)
SHOTS = [
 (0.0, 8.2, s_hook, 99, None), (8.2, 12.1, s_rewind, "rw", "flash"), (12.1, 14.9, s_bedroom, 1, "flash"),
 (14.9, 20.6, s_street, 1, "punch"), (20.6, 25.2, s_barricade, 1, "punch"), (25.2, 30.3, s_beans, 7, "punch"),
 (30.3, 39.6, s_biscuit, 12, "punch"), (39.6, 47.3, s_market, 20, "punch"), (47.3, 49.2, s_can, 20, "punch"),
 (49.2, 51.7, s_heads, 20, "flash"), (51.7, 55.5, s_chase, 20, "punch"), (55.5, 63.7, s_farm, "farm", "punch"),
 (63.7, 73.3, s_learning, 64, "punch"), (73.3, 77.2, s_storm, 80, "flash"), (77.2, 82.3, s_stairs, 99, "punch"),
 (82.3, 91.4, s_idea, 99, "punch"), (91.4, 95.7, s_throw, 99, "punch"), (95.7, 103.1, s_day100, 100, "flash"),
 (103.1, 104.4, s_quiet, 100, None), (104.4, 107.3, s_cta, None, "flash"), (107.3, 109.8, s_end, None, "punch"),
]
DURATION = SHOTS[-1][1]
GROUND = {s_bedroom: (1500, 1.35), s_street: (1700, 1.3), s_barricade: (1500, 1.4), s_beans: (1500, 1.45), s_biscuit: (1500, 1.4),
          s_market: (1500, 1.45), s_chase: (1500, 1.45), s_farm: (1350, 1.35), s_storm: (1350, 1.35), s_day100: (1560, 1.35), s_quiet: (1560, 1.3)}

def day_at(t):
    for a, b, fn, d, tr in SHOTS:
        if a <= t < b:
            if d == "rw": return 99 - 98 * ease(clamp((t - a) / (b - a - 0.3))), True
            if d == "farm": return 35 + 28 * ease(clamp((t - a - 3.8) / 4.2)), True
            return d, False
    return None, False

def draw_counter(c, t):
    d, rolling = day_at(t)
    if d is None or t < 3.1: return
    di = int(round(d))
    prev, _ = day_at(t - 0.25)
    pop = 1.0
    if prev is not None and int(round(prev)) != di and not rolling:
        pop = 1 + 0.25 * (1 - clamp((t % 10) and 1))
    c.save(); c.translate(W / 2, 250)
    rrect(c, -190, -66, 190, 66, 40, fill(C(0, 0, 0, 170)))
    rrect(c, -190, -66, 190, 66, 40, stroke(C(255, 255, 255, 60), 4))
    f1 = font("Anton", 46); f2 = font("Anton", 96)
    c.drawString("DAY", -150, 22, f1, fill(C(254, 97, 0)))
    s = f"{di}"; tw = f2.measureText(s)
    c.drawString(s, 70 - tw / 2 + 20, 34, f2, fill(C(255, 255, 255)))
    # progress to 100
    rrect(c, -150, 82, 150, 94, 6, fill(C(255, 255, 255, 60)))
    rrect(c, -150, 82, -150 + 300 * clamp(di / 100), 94, 6, fill(C(254, 97, 0)))
    c.restore()

def draw_caption(c, t):
    for (a, b, ch) in CHUNKS:
        if a <= t < b:
            f = font("Lucky", 92)
            words = [w for _, w in ch]
            widths = [f.measureText(w + " ") for w in words]
            total = sum(widths) - f.measureText(" ")
            k = back_out(clamp((t - a) / 0.16), 2.2)
            c.save(); c.translate(W / 2, 1530); c.scale(0.7 + 0.3 * k, 0.7 + 0.3 * k)
            x = -total / 2
            for (t0, w), ww in zip(ch, widths):
                hot = t >= t0
                col = C(255, 214, 10) if (hot and (w.lower().strip(".,?!:'\"") in HOT or w.lower() in HOT)) else C(255, 255, 255)
                if not hot: col = C(255, 255, 255, 150)
                c.drawString(w.upper(), x, 0, f, stroke(OUT, 18))
                c.drawString(w.upper(), x, 0, f, fill(col))
                x += ww
            c.restore()
            return

GRAIN = None
def grain(c, t):
    global GRAIN
    if GRAIN is None:
        rnd = np.random.default_rng(3)
        n = (rnd.normal(0, 1, (480, 270)) * 40 + 128).clip(0, 255).astype(np.uint8)
        arr = np.dstack([n, n, n, np.full_like(n, 22)])
        GRAIN = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
    ox = (int(t * 60) * 37) % 200; oy = (int(t * 60) * 53) % 300
    p = skia.Paint(); p.setBlendMode(skia.BlendMode.kOverlay)
    c.drawImageRect(GRAIN, skia.Rect.MakeLTRB(-ox, -oy, W - ox + 400, H - oy + 600), skia.SamplingOptions(), p)

def frame(c, t):
    c.clear(C(0, 0, 0))
    for a, b, fn, d, tr in SHOTS:
        if a <= t < b:
            lt = t - a
            c.save()
            if tr in ("punch", "flash") and lt < 0.3:
                z = 1 + 0.07 * (1 - ease_out(lt / 0.3))
                c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
            g = GROUND.get(fn)
            if g:
                gy, gz = g
                c.translate(W / 2, 1330); c.scale(gz, gz); c.translate(-W / 2, -gy)
            fn(c, lt, b - a)
            c.restore()
            if tr == "flash" and lt < 0.2:
                c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), fill(C(255, 255, 255, int(200 * (1 - lt / 0.2)))))
            if fn not in (s_cta, s_end, s_quiet, s_learning):
                vignette(c, 0.45)
            break
    draw_counter(c, t)
    draw_caption(c, t)
    grain(c, t)

def main():
    mode = sys.argv[1]
    surf = skia.Surface(W, H); c = surf.getCanvas()
    if mode == "preview":
        for ts in sys.argv[2:]:
            t = float(ts); frame(c, t)
            surf.makeImageSnapshot().save(f"prev_{t:06.2f}.jpg", skia.kJPEG, 80)
        return
    t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    t1 = float(sys.argv[3]) if len(sys.argv) > 3 else DURATION
    out = sys.argv[4] if len(sys.argv) > 4 else "video.mp4"
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-tune", "animation", "-pix_fmt", "yuv420p",
                           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        frame(c, n / FPS)
        arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        ff.stdin.write(arr.tobytes())
        if n % 600 == 0: print("frame", n, flush=True)
    ff.stdin.close(); ff.wait()
    print("done", out)

if __name__ == "__main__":
    main()
