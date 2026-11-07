# "THE UNKNOWN NUMBER" — Part 1. Stickman zombie series for Framey. 1080x1920, 60 fps.
# Usage: python3 unk1.py preview t1 t2 ...   |   python3 unk1.py render start end out.mp4
import math, random, sys, subprocess, json
sys.path.insert(0, "/home/claude/stick100")
import numpy as np
import skia
import rig
from rig import *
from world import *

FPS = 60
D = json.load(open("events.json"))
EV = {e["id"]: e for e in D["events"]}
TOTAL = D["total"]
def T(k): return EV[k]["t"]
def E(k): return EV[k]["end"]
def frac(k, f): return T(k) + (E(k) - T(k)) * f

# ---------------------------------------------------------------- fonts
_IF = {}
def inter(w, size):
    if w not in _IF: _IF[w] = skia.Typeface.MakeFromFile(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf")
    return skia.Font(_IF[w], size)

def wrap(txt, f, maxw):
    lines, cur = [], ""
    for w in txt.split():
        tryl = (cur + " " + w).strip()
        if f.measureText(tryl) <= maxw or not cur: cur = tryl
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

# ---------------------------------------------------------------- characters
SUIT = dict(body=C(232, 236, 240), out=OUT, head=C(232, 236, 240), eye=C(60, 230, 220), kind="suit")
HALE = dict(CIVS[3], kind="civ")
HALE_Z = dict(body=C(150, 140, 90), out=C(24, 26, 20), head=C(176, 186, 140), eye=C(255, 236, 120), kind="zombie")
CASHIER = dict(CIVS[2])
CASHIER_INF = dict(CIVS[2], kind="infected", eye=C(255, 226, 60))
TEAL = C(40, 210, 196)

_orig_face = rig.draw_face
def _face(c, x, y, r, st, expr, face, look, blink):
    if st["kind"] == "suit":
        c.drawCircle(x, y, r * 1.02, fill(C(232, 236, 240)))
        vp = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x - 0.62 * r + 0.25 * r * look * face, y - 0.42 * r, x + 0.78 * r + 0.25 * r * look * face, y + 0.3 * r), r * 0.3, r * 0.3)
        g = fill(C(40, 230, 220, 150)); g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.3))
        c.drawRRect(vp, g)
        c.drawRRect(vp, fill(C(10, 26, 34)))
        c.drawRRect(vp, stroke(OUT, r * 0.09))
        c.drawLine(x - 0.4 * r + 0.25 * r * look * face, y - 0.22 * r, x + 0.5 * r + 0.25 * r * look * face, y - 0.22 * r, stroke(C(60, 240, 230), r * 0.08))
        return
    if st["kind"] == "infected":
        _orig_face(c, x, y, r, dict(st, kind="civ", eye=C(20, 20, 28)), expr, face, look, blink)
        g = fill(C(255, 220, 60, 150)); g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.22))
        ex0 = x + 0.18 * look * r * face
        for ex in (-0.3, 0.3):
            c.drawCircle(ex0 + ex * r, y - 0.12 * r, r * 0.2, g)
            c.drawOval(skia.Rect.MakeLTRB(ex0 + ex * r - 0.13 * r, y - 0.27 * r, ex0 + ex * r + 0.13 * r, y + 0.03 * r), fill(C(255, 226, 60)))
            c.drawCircle(ex0 + ex * r, y - 0.12 * r, r * 0.04, fill(C(30, 20, 0)))
        return
    _orig_face(c, x, y, r, st, expr, face, look, blink)
rig.draw_face = _face

def wpt(x, gy, s, p, face, key):
    J = joints(p, s); hy = gy - foot_drop(p, s) - p["bob"] * s
    return x + face * J[key][0], hy + J[key][1]

def small_phone(c, x, y, s=1.0, lit=1.0, buzz=0.0, t=0.0):
    c.save(); c.translate(x + math.sin(t * 80) * 4 * buzz, y); c.scale(s, s)
    if lit > 0:
        c.drawCircle(0, 0, 220, rad(0, 0, 220, [C(150, 200, 255, int(110 * lit)), C(150, 200, 255, 0)]))
    outlined_rect(c, -22, -40, 22, 40, C(30, 30, 38), 6, 8)
    rrect(c, -16, -33, 16, 33, 5, fill(C(int(lerp(20, 190, lit)), int(lerp(24, 220, lit)), int(lerp(40, 255, lit)))))
    c.restore()

def face_light(c, x, y, r=320, a=110, col=(140, 190, 255)):
    p = fill(C(0, 0, 0)); p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), r, [C(*col, a), C(*col, 0)], None))
    p.setBlendMode(skia.BlendMode.kScreen); c.drawCircle(x, y, r, p)

def dark(c, k, col=(8, 10, 26)):
    if k > 0: rect(c, -600, -600, W + 600, H + 600, fill(C(*col, int(255 * clamp(k)))))

# ---------------------------------------------------------------- helpers
def cam(c, zoom=1.0, cx=W / 2, cy=H / 2, px=0, py=0, rot=0):
    c.translate(W / 2 + px, H / 2 + py); c.rotate(rot); c.scale(zoom, zoom); c.translate(-cx, -cy)

def shake(t, amt, f=31.0):
    return (math.sin(t * f) * math.sin(t * f * 0.37 + 1) * amt, math.cos(t * f * 0.83) * math.sin(t * f * 0.21 + 2) * amt)

def blink_at(t, seed=0): return ((t + seed * 1.7) % 3.3) < 0.09

def night_city(c, t, lit=1.0, base=1250, seed=21, fires=False, red_dot=None):
    sky(c, C(6, 8, 28), C(30, 22, 60))
    stars(c, 7, 70, base - 300, t)
    moon(c, 860, base - 430, 50)
    skyline(c, seed, base, 220, 520, C(26, 22, 50), C(120, 110, 170) if lit > 0.5 else None, 0.12 * lit, t=t)
    skyline(c, seed + 1, base + 120, 160, 420, C(16, 14, 34), C(255, 200, 120) if lit > 0.5 else None, 0.09 * lit, t=t, flicker=1)
    if fires:
        for fx, fy, k in ((260, base - 40, 1.0), (760, base, 0.8), (520, base + 60, 0.7)):
            fire_glow(c, fx, fy, 260 * k, t); smoke(c, fx, fy - 40, t + fx, 0.9 * k, int(fx))
    if red_dot is not None and (t % 1.0) < 0.5:
        x, y = red_dot if isinstance(red_dot, tuple) else (900, 520)
        c.drawCircle(x, y, 26, glow(C(255, 40, 40, 160), 10)); c.drawCircle(x, y, 7, fill(C(255, 70, 70)))

def apt(c, t, lamp=1.0, curtains=0.0, city_lit=1.0, fires=False, red_dot=None, flash=0.0):
    rect(c, -600, -600, W + 600, H + 600, lin(c, 0, 0, 0, H, [C(78, 70, 92), C(52, 44, 62)]))
    # window
    def outside(c2, tt):
        night_city(c2, tt, city_lit, 1060, fires=fires, red_dot=red_dot)
        if flash > 0: rect(c2, 0, 0, W, H, fill(C(220, 230, 255, int(230 * flash))))
    window_frame(c, 560, 520, 420, 520, outside, t)
    cw = 210 * clamp(curtains)
    for side in (0, 1):
        l = 548 if side == 0 else 992 - cw - 10
        r = l + cw + 12
        rect(c, l, 500, r, 1080, fill(C(110, 36, 44)))
        for k in range(1, 4):
            xx = l + (r - l) * k / 4
            c.drawLine(xx, 510, xx, 1076, stroke(C(80, 24, 32), 6))
    c.drawLine(520, 500, 1010, 500, stroke(OUT, 14))
    # floor + baseboard
    rect(c, -600, 1500, W + 600, H + 700, fill(C(64, 48, 42)))
    c.drawLine(-600, 1500, W + 600, 1500, stroke(OUT, 10))
    for i in range(-3, 10): c.drawLine(i * 160, 1500, i * 160 - 200, H + 300, stroke(C(52, 38, 34), 5))
    # lamp
    c.drawLine(150, 1080, 150, 1495, stroke(OUT, 12)); outlined_rect(c, 100, 1478, 200, 1500, C(60, 60, 70), 6, 6)
    sh = skia.Path(); sh.moveTo(90, 1090); sh.lineTo(210, 1090); sh.lineTo(180, 990); sh.lineTo(120, 990); sh.close()
    c.drawPath(sh, fill(C(int(lerp(120, 250, lamp)), int(lerp(100, 210, lamp)), int(lerp(70, 120, lamp))))); c.drawPath(sh, stroke(OUT, 7))
    if lamp > 0:
        p = fill(C(0, 0, 0)); p.setShader(skia.GradientShader.MakeRadial(skia.Point(150, 1100), 700, [C(255, 200, 120, int(90 * lamp)), C(255, 200, 120, 0)], None))
        c.drawCircle(150, 1100, 700, p)
    # couch
    outlined_rect(c, 140, 1330, 520, 1500, C(70, 90, 130), 8, 24); outlined_rect(c, 160, 1250, 500, 1345, C(84, 104, 146), 8, 22)

def bedroom(c, t, red_dot=None, lit=1.0):
    rect(c, -600, -600, W + 600, H + 600, lin(c, 0, 0, 0, H, [C(40, 44, 82), C(24, 24, 50)]))
    window_frame(c, 560, 560, 420, 500, lambda c2, tt: night_city(c2, tt, lit, 1100, red_dot=red_dot), t)
    # poster + shelf
    outlined_rect(c, 120, 640, 360, 940, C(254, 97, 0), 7, 6); text_c(c, "SKATE", 240, 820, font("Lucky", 64), C(255, 255, 255))
    rect(c, -600, 1500, W + 600, H + 700, fill(C(46, 36, 40)))
    c.drawLine(-600, 1500, W + 600, 1500, stroke(OUT, 10))
    outlined_rect(c, 60, 1400, 760, 1470, C(110, 76, 56), 8, 10)          # bed frame
    outlined_rect(c, 80, 1310, 750, 1405, C(70, 110, 190), 7, 26)         # blanket
    outlined_rect(c, 70, 1250, 260, 1325, C(236, 236, 246), 7, 26)        # pillow
    c.drawLine(80, 1470, 80, 1500, stroke(OUT, 14)); c.drawLine(740, 1470, 740, 1500, stroke(OUT, 14))

SIT_PHONE = pose(lean=8, head=16, ulL=84, llL=84, ulR=88, llR=88, uaL=34, laL=-104, uaR=50, laR=-112)

def hero_reading(c, x, gy, s, t, expr="worry", look=0.6, lit=1.0, buzz=0.0, p=None, face=1):
    p = p or SIT_PHONE
    stick(c, x, gy, s, p, HERO, face=face, expr=expr, look=look, blink=blink_at(t), scarf_t=t)
    hx, hy = wpt(x, gy, s, p, face, "handR")
    small_phone(c, hx + 6 * face, hy - 10, s / 420, lit, buzz, t)
    fx, fy = wpt(x, gy, s, p, face, "hd")
    face_light(c, fx, fy, s * 0.6, int(90 * lit))

# ---------------------------------------------------------------- overlays: chat phone + banners
SESSIONS = [
 (T("U1") - 0.4, E("U2") + 0.7), (T("U3") - 0.45, E("U4") + 0.6), (T("U6") - 0.3, E("U6") + 0.7), (T("U8") - 0.3, E("U8") + 0.6),
 (T("U9") - 0.3, E("U9") + 0.6), (E("N18") - 0.2, E("U12") + 0.15), (T("U13") - 0.45, E("U13") + 0.4),
]
BANNERS = ["U5", "U7", "U10", "U14"]
MSGS = []   # (time, side, text)
for e in D["events"]:
    if e["kind"] == "U":
        for bt, s_ in e["bubbles"]: MSGS.append((bt, "L", s_, e["id"]))
    elif e["kind"] == "H":
        MSGS.append((e["end"] - 0.2, "R", e["text"], e["id"]))
MSGS.sort()
BF = None
def bubble_layout(text):
    f = inter("SemiBold", 42); lines = wrap(text, f, 500)
    w = max(f.measureText(l) for l in lines) + 56; h = len(lines) * 54 + 34
    return lines, w, h

def session_k(t):
    for a, b in SESSIONS:
        if a - 0.01 <= t <= b:
            return ease_out(clamp((t - a) / 0.38)) * (1 - ease(clamp((t - (b - 0.35)) / 0.35))), a
    return 0.0, None

def draw_chat(c, t):
    k, a = session_k(t)
    if k <= 0: return
    rect(c, 0, 0, W, H, fill(C(0, 0, 0, int(150 * k))))
    c.save(); c.translate(0, (1 - k) * 1400)
    L, R, TOP, BOT = 120, 960, 370, 1450
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(L - 6, TOP - 6, R + 6, BOT + 6), 96, 96), glow(C(0, 0, 0, 160), 30))
    rrect(c, L, TOP, R, BOT, 92, fill(C(22, 22, 26)))
    rrect(c, L + 18, TOP + 18, R - 18, BOT - 18, 76, fill(C(6, 6, 9)))
    rrect(c, 470, TOP + 34, 610, TOP + 72, 19, fill(C(0, 0, 0)))                      # island
    clk = {0: "7:25", 1: "7:31", 2: "8:14", 3: "2:40", 4: "9:12", 5: "1:13", 6: "5:47"}.get([i for i, (sa, sb) in enumerate(SESSIONS) if sa == a][0], "")
    c.drawString(clk, L + 80, TOP + 66, inter("SemiBold", 30), fill(C(240, 240, 245)))
    rrect(c, R - 140, TOP + 42, R - 88, TOP + 66, 7, stroke(C(240, 240, 245), 3))
    bl = {0: 1.0, 1: 0.95, 2: 0.9, 3: 0.6, 4: 0.45, 5: 0.2, 6: 0.04}.get([i for i, (sa, sb) in enumerate(SESSIONS) if sa == a][0], 1)
    rrect(c, R - 136, TOP + 46, R - 136 + 44 * bl, TOP + 62, 4, fill(C(255, 60, 60) if bl < 0.1 else C(240, 240, 245)))
    # header
    hy = TOP + 150
    c.drawCircle(540, hy, 50, fill(C(90, 90, 100)))
    text_c(c, "?", 540, hy + 24, inter("Bold", 64), C(230, 230, 236))
    text_c(c, "Unknown Number", 540, hy + 98, inter("SemiBold", 34), C(240, 240, 245))
    text_c(c, "No Caller ID", 540, hy + 136, inter("Medium", 24), C(140, 140, 150))
    c.drawLine(L + 18, hy + 160, R - 18, hy + 160, stroke(C(40, 40, 46), 3))
    top_area, bot_area = hy + 180, BOT - 140
    # messages visible
    vis = [m for m in MSGS if m[0] <= t]
    typing_u = None
    nxt = [m for m in MSGS if m[0] > t and m[1] == "L" and m[0] - t < 0.75 and m[0] - 0.75 >= a]
    if nxt: typing_u = nxt[0]
    items = []
    for (bt, side, txt, eid) in vis:
        lines, w, h = bubble_layout(txt)
        pop = back_out(clamp((t - bt) / 0.28), 2.0) if bt > a else 1.0
        items.append((side, lines, w, h, pop, clamp((t - bt) / 0.28) if bt > a else 1.0))
    heights = [it[3] * it[5] + 14 for it in items]
    if typing_u: heights.append(90)
    total = sum(heights)
    off = max(0, total - (bot_area - top_area))
    c.save(); c.clipRect(skia.Rect.MakeLTRB(L + 18, top_area - 10, R - 18, bot_area + 10))
    y = top_area - off
    f = inter("SemiBold", 42)
    for (side, lines, w, h, pop, grow), hh in zip(items, heights):
        if y + hh > top_area - 200:
            x0 = L + 50 if side == "L" else R - 50 - w
            col = C(52, 52, 60) if side == "L" else C(254, 97, 0)
            c.save()
            ax = x0 if side == "L" else x0 + w
            c.translate(ax, y + h); c.scale(pop, pop); c.translate(-ax, -(y + h))
            rrect(c, x0, y, x0 + w, y + h, 32, fill(col))
            for i, ln in enumerate(lines):
                c.drawString(ln, x0 + 28, y + 56 + i * 54, f, fill(C(255, 255, 255)))
            c.restore()
        y += hh
    if typing_u:
        rrect(c, L + 50, y, L + 190, y + 76, 34, fill(C(52, 52, 60)))
        for i in range(3):
            b = 0.5 + 0.5 * math.sin(t * 12 - i * 0.9)
            c.drawCircle(L + 85 + i * 35, y + 38 - 6 * b, 10, fill(C(170, 170, 180, int(140 + 100 * b))))
    c.restore()
    # input bar with hero typing
    rrect(c, L + 40, BOT - 120, R - 40, BOT - 50, 35, stroke(C(70, 70, 80), 4))
    cur = ""
    for e in D["events"]:
        if e["kind"] == "H" and e["t"] <= t < e["end"] - 0.2:
            n = int(len(e["text"]) * clamp((t - e["t"] - 0.15) / (e["end"] - e["t"] - 0.55)))
            cur = e["text"][:n]
    ft = inter("Medium", 36)
    if cur:
        c.drawString(cur, L + 76, BOT - 72, ft, fill(C(240, 240, 245)))
        if (t * 2) % 1 < 0.5: rect(c, L + 80 + ft.measureText(cur), BOT - 104, L + 84 + ft.measureText(cur), BOT - 64, fill(C(254, 97, 0)))
    else:
        c.drawString("Text Message", L + 76, BOT - 72, ft, fill(C(110, 110, 120)))
    c.drawCircle(R - 86, BOT - 85, 26, fill(C(254, 97, 0) if cur else C(70, 70, 80)))
    c.restore()

def draw_banners(c, t):
    for k in BANNERS:
        e = EV[k]; a = e["t"] - 0.1; b = e["end"] + 1.3
        if not (a <= t <= b): continue
        kin = ease_out(clamp((t - a) / 0.3)) * (1 - ease(clamp((t - (b - 0.3)) / 0.3)))
        txt = " ".join(s_ for _, s_ in e["bubbles"] if _ <= t + 0.05) or e["bubbles"][0][1]
        f = inter("SemiBold", 40); lines = wrap(txt, f, 760)
        h = 120 + len(lines) * 50
        y0 = lerp(-h - 40, 380, kin)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(50, y0, W - 50, y0 + h), 44, 44), glow(C(0, 0, 0, 150), 24))
        rrect(c, 50, y0, W - 50, y0 + h, 44, fill(C(34, 34, 40, 240)))
        c.drawCircle(130, y0 + 66, 40, fill(C(90, 90, 100))); text_c(c, "?", 130, y0 + 86, inter("Bold", 52), C(230, 230, 236))
        c.drawString("Unknown Number", 195, y0 + 62, inter("Bold", 34), fill(C(255, 255, 255)))
        c.drawString("now", W - 150, y0 + 62, inter("Medium", 28), fill(C(150, 150, 160)))
        for i, ln in enumerate(lines): c.drawString(ln, 195, y0 + 112 + i * 50, f, fill(C(235, 235, 240)))
        if k in ("U7", "U10", "U14"):           # giant word slam in the middle
            for j, (bt, s_) in enumerate(e["bubbles"]):
                if t < bt: continue
                q = back_out(clamp((t - bt) / 0.22), 2.6); fade = 1 - clamp((t - (b - 0.5)) / 0.5)
                c.save(); c.translate(W / 2 + shake(t, 6)[0], 980 + j * 190); c.scale(q, q)
                fnt = font("Lucky", 210 if len(s_) < 7 else 150)
                for dx, col in ((-7, C(0, 255, 255, int(110 * fade))), (7, C(255, 0, 60, int(140 * fade)))):
                    text_c(c, s_.upper(), dx, 0, fnt, col)
                text_c(c, s_.upper(), 0, 0, fnt, C(255, 255, 255, int(255 * fade)), C(140, 0, 20, int(255 * fade)), 24)
                c.restore()

# ---------------------------------------------------------------- captions (narrator)
HOT = {"7:25", "november", "texted", "again.", "alone.", "text,", "unknown", "yellow.", "11:58,", "11:59,", "screaming.", "knocked.", "lock...", "buzzed.", "scratching.", "drone.",
       "bridge.", "30.", "died.", "flashlight.", "forever.", "white", "suits,", "collecting", "window.", "nobody", "alive.", "1%.",
       "ran.", "empty.", "suit.", "number", "2."}
CHUNKS = []
for e in D["events"]:
    if e["kind"] != "N": continue
    ws = e["text"].split(); wt = [len(w) + 2 + (6 if w[-1] in ".,?" else 0) + (8 if w.endswith("...") else 0) for w in ws]
    tot = sum(wt); acc = 0; words = []
    for w, x in zip(ws, wt):
        words.append((e["t"] + (e["end"] - e["t"]) * acc / tot, w)); acc += x
    cur = []
    for tw in words:
        cur.append(tw)
        if len(cur) == 3 or tw[1][-1] in ".,?" or len(" ".join(x[1] for x in cur)) > 14:
            CHUNKS.append(cur); cur = []
    if cur: CHUNKS.append(cur)
CH = []
for i, ch in enumerate(CHUNKS):
    nxt = CHUNKS[i + 1][0][0] if i + 1 < len(CHUNKS) else ch[-1][0] + 1.2
    CH.append((ch[0][0], min(nxt, ch[-1][0] + 1.3), ch))

def draw_caption(c, t):
    for (a, b, ch) in CH:
        if a <= t < b:
            f = font("Lucky", 88)
            widths = [f.measureText(w.upper() + " ") for _, w in ch]
            total = sum(widths) - f.measureText(" ")
            k = back_out(clamp((t - a) / 0.16), 2.2)
            c.save(); c.translate(W / 2, 1600); c.scale(0.7 + 0.3 * k, 0.7 + 0.3 * k)
            x = -total / 2
            for (t0, w), ww in zip(ch, widths):
                hot = t >= t0
                col = C(255, 214, 10) if (hot and w.lower() in HOT) else C(255, 255, 255)
                if not hot: col = C(255, 255, 255, 140)
                c.drawString(w.upper(), x, 0, f, stroke(OUT, 18)); c.drawString(w.upper(), x, 0, f, fill(col))
                x += ww
            c.restore(); return

# ---------------------------------------------------------------- scenes
def s_pov(c, t, T_):
    """First-person: my hands, my phone, a video playing — then the text drops in."""
    nt = 0.12
    z = 1.06 + 0.035 * t + 0.1 * ease(clamp((t - 5.5) / 2.5))
    py = 40 * ease(clamp(t / 3))
    sx, sy = shake(t, 5 if nt < t < nt + 0.7 else 1.2, 45)
    rect(c, 0, 0, W, H, lin(c, 0, 0, 0, H, [C(18, 20, 40), C(34, 36, 70)]))
    c.drawCircle(W / 2, 960, 900, rad(W / 2, 960, 900, [C(120, 160, 255, 50), C(120, 160, 255, 0)]))
    c.save(); cam(c, z, W / 2, 940 - py, sx, sy)
    rect(c, -400, 1500, W + 400, H + 600, fill(C(52, 74, 140)))                    # blanket
    for i in range(6): c.drawLine(-200 + i * 260, 1500, 40 + i * 260, H + 400, stroke(C(44, 62, 120), 14))
    sc = skia.Path(); sc.moveTo(380, H + 200); sc.cubicTo(420, 1760, 520, 1700, 560, 1600)   # my scarf
    c.drawPath(sc, stroke(OUT, 96)); c.drawPath(sc, stroke(C(254, 97, 0), 70))
    L, R, TOP, BOT = 250, 830, 400, 1460
    c.save(); c.rotate(-2)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(L, TOP, R, BOT), 80, 80), glow(C(140, 190, 255, 120), 50))
    rrect(c, L, TOP, R, BOT, 80, fill(C(22, 22, 26))); rrect(c, L + 16, TOP + 16, R - 16, BOT - 16, 66, fill(C(0, 0, 0)))
    c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(L + 16, TOP + 16, R - 16, BOT - 16), 66, 66), True)
    # the video I'm watching: a stickman skater
    rect(c, L, TOP, R, BOT, lin(c, 0, TOP, 0, BOT, [C(120, 190, 250), C(250, 210, 160)]))
    ramp = skia.Path(); ramp.moveTo(L, 1180); ramp.quadTo(L + 60, 1330, L + 200, 1330); ramp.lineTo(R - 200, 1330); ramp.quadTo(R - 60, 1330, R, 1180); ramp.lineTo(R, BOT); ramp.lineTo(L, BOT); ramp.close()
    c.drawPath(ramp, fill(C(170, 150, 130))); c.drawPath(ramp, stroke(OUT, 8))
    ph = (t * 0.55) % 1.0; sxk = L + 120 + (R - L - 240) * (0.5 - 0.5 * math.cos(ph * 2 * math.pi))
    air = max(0, math.sin(ph * 2 * math.pi * 2)) * 60
    gy = 1330 - air
    stick(c, sxk, gy - 24, 300, pose(lean=8, uaL=-60, laL=-20, uaR=70, laR=10, ulL=-20, llL=30, ulR=26, llR=30), CIVS[0], face=1 if math.sin(ph * 2 * math.pi) > 0 else -1, expr="happy", look=0.3)
    outlined_rect(c, sxk - 80, gy - 22, sxk + 80, gy - 6, C(230, 60, 60), 5, 8)
    for wx in (-50, 50): c.drawCircle(sxk + wx, gy - 2, 10, fill(OUT))
    for i, yy in enumerate((930, 1040, 1150)):
        c.drawCircle(R - 80, yy, 34, fill(C(0, 0, 0, 90)))
    heart(c, R - 80, 935, 46, 240)
    c.drawString("@sk8_stix", L + 50, BOT - 120, inter("Bold", 32), fill(C(255, 255, 255)))
    c.drawString("day 47 of learning a kickflip", L + 50, BOT - 78, inter("Medium", 26), fill(C(255, 255, 255)))
    rect(c, L, BOT - 40, R, BOT - 34, fill(C(255, 255, 255, 80))); rect(c, L, BOT - 40, L + (R - L) * ((t / 7) % 1), BOT - 34, fill(C(255, 255, 255)))
    # status bar
    c.drawString("7:25", L + 70, TOP + 70, inter("SemiBold", 34), fill(C(255, 255, 255)))
    rrect(c, R - 130, TOP + 44, R - 76, TOP + 70, 7, stroke(C(255, 255, 255), 3)); rrect(c, R - 126, TOP + 48, R - 92, TOP + 66, 4, fill(C(255, 255, 255)))
    # the text arrives
    if t > nt:
        k = ease_out(clamp((t - nt) / 0.35)); y0 = lerp(TOP - 200, TOP + 100, k)
        rrect(c, L + 30, y0, R - 30, y0 + 170, 36, fill(C(30, 30, 36, 245)))
        c.drawCircle(L + 90, y0 + 62, 32, fill(C(90, 90, 100))); text_c(c, "?", L + 90, y0 + 78, inter("Bold", 40), C(230, 230, 236))
        c.drawString("Unknown Number", L + 140, y0 + 58, inter("Bold", 30), fill(C(255, 255, 255)))
        c.drawString("now", R - 110, y0 + 58, inter("Medium", 24), fill(C(150, 150, 160)))
        c.drawString("At midnight, the world ends.", L + 140, y0 + 102, inter("SemiBold", 30), fill(C(235, 235, 240)))
        c.drawString("Do exactly what I say, and...", L + 140, y0 + 140, inter("Medium", 28), fill(C(170, 170, 180)))
    c.restore()
    c.restore()
    # my hands
    for side in (-1, 1):
        hx = 540 + side * 300; hy = 1240
        arm = skia.Path(); arm.moveTo(540 + side * 520, H + 100); arm.lineTo(540 + side * 420, 1560); arm.lineTo(hx, hy)
        c.drawPath(arm, stroke(OUT, 80)); c.drawPath(arm, stroke(C(250, 248, 242), 52))
        c.drawCircle(hx, hy, 58, fill(OUT)); c.drawCircle(hx, hy, 45, fill(C(250, 248, 242)))
    c.restore()
    # time stamp
    if t < 4.5:
        a = clamp(t / 0.3) * (1 - clamp((t - 4.0) / 0.4))
        k = back_out(clamp(t / 0.35), 2.0)
        c.save(); c.translate(W / 2, 250); c.scale(k, k)
        text_c(c, "NOV 6  •  7:25 AM", 0, 0, font("Anton", 92), C(255, 255, 255, int(255 * a)), C(0, 0, 0, int(200 * a)), 14)
        c.restore()

def s_hook(c, t, T_):
    g = GT
    z = 1.45 + 0.3 * ease(clamp((g - T("N3") + 0.3) / 2.6))
    cx, cy = 560, 1150
    c.save(); cam(c, z, cx, cy, *shake(g, 2.5 if T("U2") < g < T("U2") + 0.6 else 0))
    bedroom(c, g, red_dot=(890, 760) if g > T("N3") + 0.5 else None)
    shock = T("U2") + 0.5 < g
    look = 0.6
    p = SIT_PHONE
    if g > T("N3") - 0.2:   # looks down at the scarf, then at the window
        q = ease(clamp((g - T("N3") + 0.2) / 0.5)); q2 = ease(clamp((g - frac("N3", 0.62)) / 0.4))
        p = mix(SIT_PHONE, pose(lean=6, head=lerp(30, -8, q2), ulL=84, llL=84, ulR=88, llR=88, uaL=34, laL=-104, uaR=30, laR=-80), q)
        look = lerp(0.6, 1.0, q2)
    hero_reading(c, 400, 1400, 470, g, "shock" if shock else "worry", look)
    dark(c, 0.25)
    c.restore()

def s_title(c, t, T_):
    rect(c, 0, 0, W, H, fill(C(4, 4, 8)))
    rnd = random.Random(int(t * 30))
    jit = rnd.uniform(-8, 8) if rnd.random() < 0.35 else 0
    k = back_out(clamp(t / 0.3), 1.6)
    c.save(); c.translate(W / 2 + jit, 860); c.scale(k, k)
    for dx, col in ((-6, C(0, 255, 255, 120)), (6, C(255, 0, 60, 150))):
        text_c(c, "THE UNKNOWN", dx, 0, font("Lucky", 128), col); text_c(c, "NUMBER", dx, 150, font("Lucky", 190), col)
    text_c(c, "THE UNKNOWN", 0, 0, font("Lucky", 128), C(255, 255, 255), OUT, 20)
    text_c(c, "NUMBER", 0, 150, font("Lucky", 190), C(254, 97, 0), OUT, 24)
    c.restore()
    k2 = clamp((t - 0.45) / 0.3)
    rrect(c, W / 2 - 150, 1110, W / 2 + 150, 1200, 45, fill(C(255, 255, 255, int(255 * k2))))
    text_c(c, "PART 1", W / 2, 1178, font("Anton", 70), C(17, 17, 17, int(255 * k2)))
    for i in range(5):
        y = rnd.uniform(0, H); rect(c, 0, y, W, y + rnd.uniform(2, 10), fill(C(255, 255, 255, int(rnd.uniform(10, 50)))))

def s_day0(c, t, T_):
    c.save(); cam(c, 1.45 + 0.03 * t / 6, 520, 1150)
    bedroom(c, t + 20)
    hero_reading(c, 400, 1400, 470, t, "worry" if t < 3 else "angry" if t < 8.2 else "worry", 0.6)
    dark(c, 0.25)
    c.restore()

def jump_face(c, k, st, t, mouth=1.0):
    """Full-screen face slam. k = 0..1 time since the snap (scale settles fast)."""
    rect(c, -50, -50, W + 50, H + 50, fill(C(40, 0, 6)))
    c.drawCircle(W / 2, 900, 1100, rad(W / 2, 900, 1100, [C(160, 10, 20, 200), C(20, 0, 4, 0)]))
    sc = lerp(1.45, 1.0, ease_out(clamp(k / 0.12)))
    sx, sy = shake(t, 22 * (1 - clamp(k / 0.8)) + 4, 60)
    c.save(); c.translate(W / 2 + sx, 930 + sy); c.scale(sc, sc)
    R = 560
    c.drawCircle(0, 0, R + 26, fill(OUT)); c.drawCircle(0, 0, R, fill(st["head"]))
    if st["kind"] == "suit":
        vp = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-420, -230, 460, 150), 160, 160)
        g = fill(C(40, 230, 220, 200)); g.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 60)); c.drawRRect(vp, g)
        c.drawRRect(vp, fill(C(8, 22, 30))); c.drawRRect(vp, stroke(OUT, 40))
        c.drawLine(-300, -120, 340, -120, stroke(C(60, 240, 230), 36))
    else:
        eye = st["eye"] if st["kind"] == "zombie" else C(255, 226, 60)
        c.drawCircle(0, 0, R, fill(C(150, 170, 140) if st["kind"] == "zombie" else C(196, 190, 170)))
        c.drawCircle(0, 60, R, rad(0, 60, R, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(20, 30, 20, 150)], [0, 0.55, 1.0]))
        rnd = random.Random(5)
        for i in range(6):   # veins / cracks
            p = skia.Path(); x0, y0 = rnd.uniform(-400, 400), rnd.uniform(-380, 380); p.moveTo(x0, y0)
            for j in range(4): x0 += rnd.uniform(-70, 70); y0 += rnd.uniform(-60, 60); p.lineTo(x0, y0)
            c.drawPath(p, stroke(C(90, 40, 60, 160), 9))
        for ex in (-190, 190):
            c.drawOval(skia.Rect.MakeLTRB(ex - 150, -250, ex + 150, 10), fill(C(16, 10, 12)))          # sunken sockets
            gl = fill(C(255, 220, 80, 200)); gl.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40))
            c.drawCircle(ex, -120, 95, gl); c.drawCircle(ex, -120, 58, fill(eye)); c.drawCircle(ex, -120, 16, fill(C(40, 10, 0)))
            inner = 1 if ex < 0 else -1      # angry brows: inner ends low
            c.drawLine(ex - 150 * inner, -320, ex + 140 * inner, -240, stroke(OUT, 40))
        m = skia.Path(); m.addOval(skia.Rect.MakeLTRB(-240 * mouth, 70, 240 * mouth, 70 + 360 * mouth)); c.drawPath(m, fill(C(24, 0, 6)))
        for i in range(8):
            tx = -200 + i * 57
            tri = skia.Path(); tri.moveTo(tx - 24, 96); tri.lineTo(tx + 24, 96); tri.lineTo(tx, 170); tri.close(); c.drawPath(tri, fill(C(230, 222, 190)))
            tri = skia.Path(); tri.moveTo(tx - 22, 420); tri.lineTo(tx + 22, 420); tri.lineTo(tx, 360); tri.close(); c.drawPath(tri, fill(C(230, 222, 190)))
    c.restore()
    if k < 0.1: rect(c, 0, 0, W, H, fill(C(255, 255, 255, int(255 * (1 - k / 0.1)))))

def store_bg(c, t):
    rect(c, -600, -600, W + 600, H + 600, lin(c, 0, 0, 0, H, [C(196, 206, 196), C(160, 170, 160)]))
    for i, x in enumerate((90, 520, 900)):
        fl = 1.0 if not (i == 1 and (t * 7) % 3.1 < 0.4) else 0.25
        rect(c, x - 140, 120, x + 140, 150, fill(C(240, 255, 240, int(255 * fl))))
        c.drawCircle(x, 135, 260, rad(x, 135, 260, [C(230, 255, 230, int(70 * fl)), C(230, 255, 230, 0)]))
    rect(c, -600, 1500, W + 600, H + 700, fill(C(150, 150, 140)))
    for i in range(-4, 14): c.drawLine(i * 120, 1500, i * 120 - 160, H + 300, stroke(C(130, 130, 122), 4))
    c.drawLine(-600, 1500, W + 600, 1500, stroke(OUT, 10))
    # nearly empty shelves
    for sx in (-60, 330):
        outlined_rect(c, sx, 760, sx + 350, 1500, C(176, 182, 194), 8, 4)
        rnd = random.Random(sx)
        for r_ in range(4):
            y = 860 + r_ * 160; c.drawLine(sx + 6, y, sx + 344, y, stroke(OUT, 9))
            for j in range(rnd.choice([0, 0, 1, 2])):
                px = sx + 30 + rnd.uniform(0, 260); col = rnd.choice([(230, 80, 70), (80, 150, 230), (250, 190, 60)])
                outlined_rect(c, px, y - rnd.uniform(60, 90), px + 46, y - 4, C(*col), 5, 4)
    outlined_rect(c, 40, 560, 560, 680, C(220, 60, 50), 8, 10); text_c(c, "SALE", 300, 650, font("Anton", 90), C(255, 255, 255))

def s_store(c, t, T_):
    g0 = T("N4"); cough_t = frac("N4", 0.42) - g0; eyes_t = frac("N4", 0.8) - g0; u5 = T("U5") - g0
    zin = ease(clamp((t - eyes_t + 0.4) / 0.9)) * (1 - ease(clamp((t - u5 - 0.2) / 0.6)))
    c.save(); cam(c, lerp(1.3, 2.6, zin), lerp(560, 790, zin), lerp(1130, 1010, zin), *shake(t, 3 if t > u5 else 0))
    store_bg(c, t)
    # cashier behind counter
    cough = (t > cough_t) and ((t - cough_t) % 1.1 < 0.45) and t < eyes_t + 0.5
    reach = ease(clamp((t - u5 - 0.6) / 0.8))
    cp = pose(lean=22 if cough else 4 + 14 * reach, head=18 if cough else -4, uaL=40 if cough else -10, laL=-120 if cough else -8,
              uaR=lerp(12, 80, reach), laR=lerp(8, 4, reach))
    st = CASHIER_INF if t > eyes_t else CASHIER
    stick(c, 800, 1500, 500, cp, st, face=-1, expr="sad" if t < eyes_t else "neutral", look=0.4, blink=blink_at(t, 2) and t < eyes_t)
    outlined_rect(c, 640, 1230, 1100, 1500, C(120, 90, 70), 8, 6)
    outlined_rect(c, 900, 1130, 1040, 1232, C(60, 60, 70), 7, 8)       # register
    rect(c, 920, 1146, 1020, 1190, fill(C(80, 220, 120)))
    if cough:
        k = (t - cough_t) % 1.1
        for i in range(3):
            c.drawCircle(700 - k * 160 - i * 30, 1010 + i * 12, 14 + k * 30, fill(C(200, 220, 160, int(140 * (1 - k / 0.45)))))
    # hero with basket: walks in, stops, backs away on U5
    if t < u5:
        hx = lerp(-140, 390, ease_out(clamp(t / 4.0))); hp = walk(t * 8) if t < 4 else idle(t)
        if t >= 4: hp = mix(idle(t), scared(t), ease(clamp((t - eyes_t) / 0.4)))
    else:
        hx = 390 - 220 * ease(clamp((t - u5 - 0.8) / 2.5)); hp = walk(-(t) * 8, 0.8) if 0.8 < t - u5 < 3.3 else scared(t)
    stick(c, hx, 1500, 470, hp, HERO, face=1, expr="shock" if t > eyes_t else "neutral", look=0.7, scarf_t=t, blink=blink_at(t))
    bx, by = wpt(hx, 1500, 470, hp, 1, "handL")
    outlined_rect(c, bx - 60, by, bx + 60, by + 80, C(40, 120, 220), 6, 8)
    for i in range(3): outlined_rect(c, bx - 48 + i * 34, by - 50, bx - 22 + i * 34, by + 10, C(160, 210, 255), 4, 6)
    c.restore()
    snap = T("JS1") + 0.6
    if snap <= GT < T("U5") - 0.1: jump_face(c, GT - snap, CASHIER_INF, GT, 1.0)

def s_lock(c, t, T_):
    c.save(); cam(c, 1.2, 520, 1080)
    rect(c, -600, -600, W + 600, H + 600, lin(c, 0, 0, 0, H, [C(62, 56, 78), C(40, 34, 52)]))
    rect(c, -600, 1500, W + 600, H + 700, fill(C(56, 42, 38))); c.drawLine(-600, 1500, W + 600, 1500, stroke(OUT, 10))
    door(c, 120, 720, 330, 780)
    outlined_rect(c, 382, 1100, 418, 1160, C(190, 190, 200), 5, 8)
    turn = ease(clamp((t - 0.9) / 0.4))
    c.save(); c.translate(400, 1130); c.rotate(90 * turn); rrect(c, -8, -24, 8, 24, 6, fill(C(80, 80, 90))); c.restore()
    # wall clock
    outlined_rect(c, 640, 760, 960, 900, C(10, 10, 14), 8, 16)
    clock = "11:58"
    f = font("Anton", 110); text_c(c, clock, 800, 870, f, C(255, 50, 50))
    c.drawCircle(800, 830, 140, rad(800, 830, 160, [C(255, 40, 40, 50), C(255, 40, 40, 0)]))
    p = pose(lean=10, head=4, uaR=-70 + 30 * (1 - turn), laR=-40, uaL=10, laL=-20)
    stick(c, 540, 1500, 470, p, HERO, face=-1, expr="worry", look=0.5, scarf_t=t, blink=blink_at(t))
    dark(c, 0.2)
    c.restore()

def s_alert(c, t, T_):
    sx, sy = shake(t, 10 * (1 - clamp(t / 2.5)) + 3, 50)
    rect(c, 0, 0, W, H, fill(C(10, 6, 8)))
    flash = 0.5 + 0.5 * math.sin(t * 14)
    c.drawCircle(W / 2, 900, 900, rad(W / 2, 900, 900, [C(255, 20, 30, int(120 * flash)), C(255, 20, 30, 0)]))
    c.save(); c.translate(W / 2 + sx, 930 + sy); c.rotate(math.sin(t * 40) * 1.2); s = 1.0 + 0.03 * ease(t / 4)
    c.scale(s, s)
    rrect(c, -400, -620, 400, 620, 90, fill(C(22, 22, 26))); rrect(c, -380, -600, 380, 600, 76, fill(C(0, 0, 0)))
    text_c(c, "11:59", 0, -360, inter("Bold", 150), C(240, 240, 245))
    text_c(c, "Wednesday", 0, -470, inter("Medium", 40), C(200, 200, 210))
    rrect(c, -340, -230, 340, 250, 40, fill(C(int(lerp(150, 210, flash)), 20, 30)))
    tri = skia.Path(); tri.moveTo(-270, -120); tri.lineTo(-210, -200); tri.lineTo(-150, -120); tri.close()
    c.drawPath(tri, fill(C(255, 214, 10))); text_c(c, "!", -210, -128, inter("Black", 60), C(20, 20, 20))
    c.drawString("EMERGENCY ALERT", -120, -140, inter("Black", 44), fill(C(255, 255, 255)))
    for i, ln in enumerate(["Extreme Alert: SHELTER", "IN PLACE. Stay indoors.", "Lock all doors.", "Do NOT go outside."]):
        c.drawString(ln, -300, -50 + i * 66, inter("SemiBold", 48), fill(C(255, 255, 255)))
    c.restore()
    for i in range(3):
        a = (t * 1.6 + i / 3) % 1
        c.drawArc(skia.Rect.MakeLTRB(W / 2 - 430 - a * 260, 300 - a * 260, W / 2 + 430 + a * 260, 1560 + a * 260), -30, 60, False, stroke(C(255, 80, 80, int(200 * (1 - a))), 10))
        c.drawArc(skia.Rect.MakeLTRB(W / 2 - 430 - a * 260, 300 - a * 260, W / 2 + 430 + a * 260, 1560 + a * 260), 150, 60, False, stroke(C(255, 80, 80, int(200 * (1 - a))), 10))

def s_chaos(c, t, T_):
    c.save(); cam(c, 1.0 + 0.08 * t, W / 2, 1000, *shake(t, 6))
    night_city(c, t, 1.0, 1150, seed=33, fires=True)
    rect(c, -600, 1300, W + 600, H + 700, fill(C(40, 36, 50)))
    rnd = random.Random(9)
    for i in range(8):
        sp = rnd.uniform(500, 800); gy = rnd.choice([1420, 1500, 1580]); x = (t * sp + i * 300) % (W + 600) - 300
        stick(c, x, gy, rnd.uniform(200, 260), run(t * 13 + i), CIVS[i % 5], face=1, expr="scared", look=0.3)
    for i in range(6):
        x = -120 + i * 140 + t * 90; gy = 1460 + (i % 3) * 70
        stick(c, x, gy, 250, run(t * 11 + i * 1.3, 0.8), ZOMB, face=1, expr="z")
    c.restore()
    # window frame overlay (we're looking out)
    p = stroke(OUT, 60); c.drawRect(skia.Rect.MakeLTRB(-10, -10, W + 10, H + 10), p)
    c.drawLine(W / 2, 0, W / 2, H, stroke(C(40, 36, 46), 34)); c.drawLine(0, 960, W, 960, stroke(C(40, 36, 46), 34))
    grade(c, C(255, 190, 170))

def s_rule1(c, t, T_):
    c.save(); cam(c, 1.4, 520, 1170)
    apt(c, t, lamp=1.0, curtains=0.6, fires=True)
    p = pose(lean=-6, head=14, ulL=70, llL=90, ulR=60, llR=100, uaL=40, laL=-100, uaR=55, laR=-112)
    hero_reading(c, 380, 1500, 460, t, "worry", 0.6, p=p)
    dark(c, 0.15)
    c.restore()

def s_knock(c, t, T_):
    kn = [0.15, 0.45, 0.75, 1.5, 1.75, 2.0]
    hit = max([max(0, 1 - (t - k) * 8) for k in kn if t >= k] + [0])
    c.save(); cam(c, 1.2 + 0.05 * t, 450, 1080, hit * 8, 0)
    rect(c, -600, -600, W + 600, H + 600, lin(c, 0, 0, 0, H, [C(62, 56, 78), C(40, 34, 52)]))
    rect(c, -600, 1500, W + 600, H + 700, fill(C(56, 42, 38))); c.drawLine(-600, 1500, W + 600, 1500, stroke(OUT, 10))
    c.save(); c.translate(hit * 6, 0); door(c, 120, 720, 330, 780); c.restore()
    c.drawCircle(285, 940, 12, fill(OUT)); c.drawCircle(285, 940, 6, fill(C(255, 240, 200)))   # peephole
    if hit > 0.3: text_c(c, "KNOCK", 300 + random.Random(int(t * 10)).uniform(-30, 30), 700, font("Lucky", 110), C(255, 255, 255), OUT, 16)
    hx = lerp(860, 520, ease(clamp((t - 0.4) / 1.6)))
    hp = sneak(t * 6) if 0.4 < t < 2.0 else scared(t)
    stick(c, hx, 1500, 450, hp, HERO, face=-1, expr="scared", look=0.4, scarf_t=t, blink=blink_at(t))
    dark(c, 0.25)
    c.restore()

def peephole(c, t, draw, zoom=1.0):
    rect(c, 0, 0, W, H, fill(C(4, 4, 6)))
    cx, cy, R = W / 2, 900, 470
    path = skia.Path(); path.addCircle(cx, cy, R)
    c.save(); c.clipPath(path, skia.ClipOp.kIntersect, True)
    c.save(); c.translate(cx, cy); c.scale(zoom, zoom); c.translate(-cx, -cy); draw(c, t); c.restore()
    c.drawCircle(cx, cy, R, rad(cx, cy, R, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, 230)], [0, 0.6, 1.0]))
    c.drawCircle(cx - 160, cy - 200, 160, rad(cx - 160, cy - 200, 160, [C(255, 255, 255, 40), C(255, 255, 255, 0)]))
    c.restore()
    c.drawCircle(cx, cy, R + 6, stroke(C(30, 30, 34), 18))

def hallway(c, t, flick=True, horde_k=0.0):
    fl = 0.35 if (flick and (t * 5.3) % 2.7 < 0.25) else 1.0
    rect(c, -600, -600, W + 600, H + 600, fill(C(int(108 * fl), int(112 * fl), int(86 * fl))))
    # vanishing hallway
    vp = (540, 820)
    rect(c, 360, 660, 720, 1000, fill(C(int(30 * fl), int(30 * fl), int(26 * fl))))
    for (x0, y0) in ((-200, -200), (W + 200, -200), (-200, H + 200), (W + 200, H + 200)):
        c.drawLine(x0, y0, 360 if x0 < 0 else 720, 660 if y0 < 0 else 1000, stroke(C(60, 60, 50), 8))
    rect(c, -600, 1000, W + 600, H + 700, fill(C(int(70 * fl), int(60 * fl), int(52 * fl))))
    c.drawCircle(540, 560, 60, glow(C(255, 250, 210, int(200 * fl)), 30))
    if horde_k > 0:
        for i in range(4):
            x = 430 + i * 60; s = 150 + 30 * horde_k
            stick(c, x, 1000, s, zwalk(t * 3 + i), dict(ZOMB, body=C(30, 34, 30), head=C(36, 40, 36)), face=1 if i % 2 else -1, expr="z", alpha=int(255 * horde_k))

def s_peep(c, t, T_):
    def draw(c2, tt):
        hallway(c2, tt, True, ease(clamp(tt / 3.0)) * 0.9)
        bang = math.sin(tt * 9)
        p = pose(lean=12, head=-14 + 20 * ease(clamp((tt - 1.2) / 0.3)) * (1 - ease(clamp((tt - 1.9) / 0.3))),
                 uaL=-120 + 20 * bang, laL=-30, uaR=-110 - 20 * bang, laR=-20)
        lookback = (1.2 < tt < 1.9)
        stick(c2, 560, 1960, 1050, p, HALE, face=-1 if lookback else 1, expr="scared", look=-0.6 if lookback else 0.4, blink=blink_at(tt))
    peephole(c, t, draw, 1.0 + 0.04 * t)

def s_hand(c, t, T_):
    buzz_t = E("N9") - T("N9") - 0.5
    sx, sy = shake(t, 4 if buzz_t < t < buzz_t + 0.6 else 0, 60)
    c.save(); cam(c, 1.0 + 0.03 * t, W / 2, 960, sx, sy)
    rect(c, -600, -600, W + 600, H + 600, lin(c, 0, 0, W, H, [C(140, 92, 56), C(110, 70, 42)]))
    for i in range(-2, 12): c.drawLine(i * 120, -200, i * 120 + 40, H + 200, stroke(C(120, 78, 46), 6))
    outlined_rect(c, 400, 640, 680, 1240, C(186, 186, 196), 9, 40)
    c.drawCircle(540, 820, 70, fill(C(150, 150, 160))); c.drawCircle(540, 820, 70, stroke(OUT, 8))
    ang = 26 * ease(clamp((t - 0.4) / max(0.5, buzz_t - 0.4))) + (math.sin(t * 40) * 2 if t > buzz_t else 0)
    ang = min(ang, 26)
    c.save(); c.translate(540, 1040); c.rotate(ang)
    outlined_rect(c, -36, -110, 36, 110, C(170, 170, 180), 8, 30)
    c.restore()
    # arm + hand (stick style)
    hx, hy = 540 + 60 * math.sin(math.radians(ang)), 1040 - 30
    arm = skia.Path(); arm.moveTo(1180, 1800); arm.lineTo(870, 1350); arm.lineTo(hx + 30, hy + 40)
    c.drawPath(arm, stroke(OUT, 92)); c.drawPath(arm, stroke(C(250, 248, 242), 58))
    c.drawCircle(hx + 30, hy + 30, 64, fill(OUT)); c.drawCircle(hx + 30, hy + 30, 50, fill(C(250, 248, 242)))
    sc = skia.Path(); sc.moveTo(1180, 1900); sc.lineTo(1000, 1640); c.drawPath(sc, stroke(OUT, 120)); c.drawPath(sc, stroke(C(254, 97, 0), 90))
    dark(c, 0.3 + 0.15 * clamp((t - buzz_t) / 1))
    c.restore()

def s_peep2(c, t, T_):
    g = GT; stop = E("N10") - 0.6; gone = T("JS2") + 0.5; snap = T("JS2") + 1.35
    def draw(c2, tt):
        hallway(c2, tt * (1 if g < gone else 2.3), True, 0.9 if g < stop else 0.0)
        if g < stop:
            bang = math.sin(tt * 9)
            p = pose(lean=12, head=-14, uaL=-120 + 20 * bang, laL=-30, uaR=-110 - 20 * bang, laR=-20)
            stick(c2, 560, 1960, 1050, p, HALE, face=1, expr="scared", look=0.4)
        elif g < gone:
            q = ease(clamp((g - stop) / (gone - stop)))
            stick(c2, 560 + 20 * q, lerp(1960, 1020, q), lerp(1050, 260, q), walk(tt * 4, 0.6) if q > 0.15 else pose(head=30, uaL=-10, uaR=10),
                  HALE, face=-1, expr="sleep", look=0.0, alpha=int(255 * (1 - 0.7 * q)))
        elif g >= snap + 1.0:
            s_ = math.sin(tt * 18)
            p = pose(lean=18, head=-20, uaL=-150 + 25 * s_, laL=-40, uaR=-140 - 25 * s_, laR=-30)
            stick(c2, 560, 1960, 1120, p, HALE_Z, face=1, expr="z", look=0.2)
    if snap <= g < snap + 1.0:
        jump_face(c, g - snap, HALE_Z, g, 1.0)
        path = skia.Path(); path.addCircle(W / 2, 900, 470)
        c.save(); c.clipPath(path, skia.ClipOp.kDifference, True); rect(c, 0, 0, W, H, fill(C(4, 4, 6, 200))); c.restore()
        return
    sx, sy = shake(t, 6 if g > snap else 0, 45)
    c.save(); c.translate(sx, sy); peephole(c, t, draw, 1.0 + 0.04 * t + (0.06 * ease(clamp((g - gone) / 0.85)) if g > gone else 0)); c.restore()
    if g > snap + 1.0:
        for i in range(4):
            a = clamp((g - snap - 1.0 - i * 0.25) / 0.3)
            if a > 0: c.drawLine(140 + i * 50, 1440, 140 + i * 50 + 40 * a, 1440 + 300 * a, stroke(C(200, 200, 210, 200), 8))

def s_rule2(c, t, T_):
    c.save(); cam(c, 1.4, 520, 1170)
    apt(c, t, lamp=1.0, curtains=0.8)
    p = pose(lean=4, head=14, ulL=-6, ulR=6, uaL=34, laL=-104, uaR=50, laR=-112)
    hero_reading(c, 420, 1500, 470, t, "worry", 0.6, p=p)
    dark(c, 0.3)
    c.restore()

def drone(c, x, y, s, t, light=True):
    c.save(); c.translate(x, y); c.scale(s, s); c.rotate(math.sin(t * 2) * 4)
    for dx in (-140, 140):
        c.drawLine(dx * 0.4, 0, dx, -30, stroke(OUT, 14))
        a = 0.5 + 0.5 * math.sin(t * 90 + dx)
        c.drawOval(skia.Rect.MakeLTRB(dx - 80, -44, dx + 80, -24), fill(C(200, 200, 210, int(90 + 60 * a))))
    outlined_rect(c, -90, -24, 90, 30, C(46, 46, 54), 8, 16)
    if (t % 0.8) < 0.4:
        c.drawCircle(0, 40, 30, glow(C(255, 40, 40, 200), 12)); c.drawCircle(0, 40, 10, fill(C(255, 80, 80)))
    c.restore()

def roof_bg(c, t):
    sky(c, C(4, 6, 22), C(24, 20, 54)); stars(c, 3, 120, 1100, t); moon(c, 220, 360, 60)
    skyline(c, 41, 1250, 200, 480, C(20, 18, 42), C(120, 110, 170), 0.06, t=t)
    rect(c, -600, 1380, W + 600, H + 700, fill(C(54, 52, 66))); c.drawLine(-600, 1380, W + 600, 1380, stroke(OUT, 10))
    outlined_rect(c, 760, 1220, 900, 1380, C(90, 90, 116), 7, 6)

def s_roof(c, t, T_):
    g0 = T("N11"); dr_t = frac("N11", 0.12) - g0; drop_t = frac("N11", 0.72) - g0
    c.save(); cam(c, 1.3 + 0.05 * t / 6, 480, 1080)
    roof_bg(c, t)
    k = ease(clamp((t - dr_t) / 2.6))
    dx = lerp(1300, 560, k); dy = lerp(380, 820, k) + math.sin(t * 2.3) * 12
    if t > drop_t + 0.4: dx += (t - drop_t - 0.4) * 200; dy -= (t - drop_t - 0.4) * 160
    # searchlight cone
    if t > dr_t:
        cone = skia.Path(); cone.moveTo(dx - 30, dy + 30); cone.lineTo(dx + 30, dy + 30); cone.lineTo(dx + 240, 1400); cone.lineTo(dx - 240, 1400); cone.close()
        p = fill(C(0, 0, 0)); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, dy), skia.Point(0, 1400)], [C(220, 240, 255, 110), C(220, 240, 255, 20)], None))
        c.drawPath(cone, p)
    # box falls
    if t > drop_t:
        by = min(1380, dy + 60 + 2400 * (t - drop_t) ** 2); bx = lerp(560, 520, clamp(t - drop_t))
        land = t > drop_t and by >= 1380
        sq = 1 - 0.15 * max(0, 1 - (t - drop_t - 0.3) * 6) if land else 1
        c.save(); c.translate(bx, by); c.scale(1 / sq, sq)
        outlined_rect(c, -90, -120, 90, 0, C(90, 110, 80), 8, 8); c.drawLine(-90, -60, 90, -60, stroke(OUT, 6))
        text_c(c, "?", 0, -32, font("Anton", 60), C(255, 255, 255)); c.restore()
    drone(c, dx, dy, 1.0, t)
    flinch = t > drop_t + 0.3 and t < drop_t + 0.9
    hp = scared(t) if flinch or t > dr_t else idle(t)
    stick(c, 300, 1380, 460, hp, HERO, face=1, expr="shock" if t > dr_t else "worry", look=0.9 if t < drop_t else 0.5, scarf_t=t, wind=0.5, blink=blink_at(t))
    c.restore()

def s_box(c, t, T_):
    g0 = T("N12"); mp = frac("N12", 0.38) - g0; circ = frac("N12", 0.55) - g0; br = frac("N12", 0.78) - g0
    zoom = 1.0 + 0.9 * ease(clamp((t - br) / 1.2))
    c.save(); cam(c, zoom, lerp(W / 2, 640, ease(clamp((t - br) / 1.2))), lerp(960, 860, ease(clamp((t - br) / 1.2))))
    rect(c, -600, -600, W + 600, H + 600, fill(C(40, 38, 48)))
    for i in range(-5, 16): c.drawLine(-600, i * 150, W + 600, i * 150 + 90, stroke(C(48, 46, 56), 5))
    outlined_rect(c, 100, 420, 980, 1500, C(110, 130, 96), 12, 12)
    rect(c, 140, 460, 940, 1460, fill(C(46, 54, 40)))
    items = [(0.0, "radio"), (0.25, "flash"), (0.5, "map")]
    for i, (dt, kind) in enumerate(items):
        a = back_out(clamp((t - 0.6 - dt * 4) / 0.35))
        if a <= 0: continue
        c.save()
        if kind == "radio":
            c.translate(330, 760); c.scale(a, a); outlined_rect(c, -150, -110, 150, 110, C(60, 60, 70), 8, 14)
            c.drawCircle(-60, 0, 60, fill(C(30, 30, 36))); c.drawLine(110, -110, 150, -260, stroke(OUT, 10))
            for j in range(4): c.drawLine(30, -50 + j * 30, 120, -50 + j * 30, stroke(C(120, 120, 130), 6))
        elif kind == "flash":
            c.translate(720, 760); c.rotate(-30); c.scale(a, a); outlined_rect(c, -40, -150, 40, 120, C(200, 60, 50), 8, 14)
            outlined_rect(c, -60, -200, 60, -140, C(220, 220, 230), 8, 10)
        c.restore()
    k = ease(clamp((t - mp) / 0.6))
    if k > 0:
        c.save(); c.translate(540, lerp(1300, 1050, k)); c.scale(lerp(0.3, 1.0, k), lerp(0.3, 1.0, k)); c.rotate(lerp(-12, -3, k))
        outlined_rect(c, -420, -330, 420, 330, C(236, 222, 186), 8, 6)
        for gx in range(-360, 400, 90): c.drawLine(gx, -320, gx + 30, 320, stroke(C(190, 180, 160), 4))
        for gy in range(-280, 320, 80): c.drawLine(-410, gy, 410, gy - 20, stroke(C(190, 180, 160), 4))
        river = skia.Path(); river.moveTo(-430, 200); river.cubicTo(-150, 80, 50, 260, 430, -60)
        c.drawPath(river, stroke(C(90, 150, 220), 70))
        c.drawLine(80, -160, 160, 260, stroke(C(70, 70, 80), 22)); c.drawLine(80, -160, 160, 260, stroke(C(240, 240, 240), 8))
        if t > circ:
            ck = clamp((t - circ) / 0.7)
            ring = skia.Path(); ring.addOval(skia.Rect.MakeLTRB(10, -40, 240, 160))
            pr = stroke(C(220, 30, 30), 14); L = 680
            pr.setPathEffect(skia.DashPathEffect.Make([L * ck + 0.1, L], 0)); c.drawPath(ring, pr)
        if t > br:
            q = back_out(clamp((t - br) / 0.3))
            c.save(); c.translate(240, -170); c.rotate(-8); c.scale(q, q)
            text_c(c, "DAY 30", 0, 0, font("Lucky", 80), C(220, 30, 30)); c.restore()
        c.restore()
    c.restore()

def s_power(c, t, T_):
    off_t = frac("N13", 0.75) - T("N13") + 0.1
    on = 1.0 if t < off_t else 0.0
    if off_t - 0.5 < t < off_t and (t * 20) % 2 < 1: on = 0.3
    c.save(); cam(c, 1.35, 560, 1170)
    apt(c, t, lamp=on, curtains=0.0, city_lit=1.0 if t < off_t + 0.4 else 0.0)
    stick(c, 640, 1500, 470, idle(t) if t < off_t else scared(t), HERO, face=-1, expr="neutral" if t < off_t else "shock", look=0.6, scarf_t=t, blink=blink_at(t))
    dark(c, 0.15 if on > 0.5 else 0.72)
    c.restore()

def s_rule3(c, t, T_):
    c.save(); cam(c, 1.4, 520, 1170)
    apt(c, t, lamp=0, curtains=clamp(t / 3.5), city_lit=0)
    hero_reading(c, 420, 1500, 470, t, "scared", 0.6, p=pose(lean=4, head=14, uaL=34, laL=-104, uaR=50, laR=-112))
    dark(c, 0.6)
    fx, fy = wpt(420, 1500, 470, pose(lean=4, head=14), 1, "hd"); face_light(c, fx + 40, fy, 300, 120)
    c.restore()

def facade_across(c, t, beam_on, k_horde):
    sky(c, C(4, 6, 20), C(16, 16, 40))
    stars(c, 5, 60, 600, t)
    rect(c, 80, 260, 1000, H + 100, fill(C(32, 32, 46))); rect(c, 60, 230, 1020, 268, fill(C(44, 44, 60)))
    for j in range(7):
        for i in range(4):
            x = 140 + i * 220; y = 340 + j * 180
            lit = (i, j) == (2, 3) and beam_on > 0
            outlined_rect(c, x, y, x + 150, y + 110, C(14, 14, 24) if not lit else C(90, 90, 70), 6, 4)
            if lit:
                a = 0.6 + 0.4 * math.sin(t * 9)
                ang = math.sin(t * 1.8) * 25
                c.save(); c.translate(x + 75, y + 55); c.rotate(ang + 90)
                cone = skia.Path(); cone.moveTo(0, -12); cone.lineTo(0, 12); cone.lineTo(700, 160); cone.lineTo(700, -160); cone.close()
                p = fill(C(0, 0, 0)); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(700, 0)], [C(255, 250, 210, int(150 * beam_on * a)), C(255, 250, 210, 0)], None))
                c.drawPath(cone, p); c.restore()
                c.drawCircle(x + 75, y + 55, 50, glow(C(255, 250, 220, int(230 * beam_on)), 20))
    rect(c, -600, 1480, W + 600, H + 700, fill(C(26, 24, 34)))
    if k_horde > 0:
        for i in range(9):
            x = lerp(-200 + i * 160, 300 + i * 50, k_horde) + math.sin(t + i) * 10; gy = 1540 + (i % 3) * 50
            p = pose(lean=-14, head=-30, uaL=-140, laL=-10, uaR=-150, laR=10) if k_horde > 0.7 else zwalk(t * 3 + i)
            stick(c, x, gy, 210, p, ZOMB, face=1, expr="z", look=0.3)

def s_across(c, t, T_):
    g0 = T("N14"); on_t = frac("N14", 0.37) - g0; off_t = frac("N14", 0.9) - g0
    beam = clamp((t - on_t) / 0.15) if t < off_t else 0.0
    if off_t - 0.6 < t < off_t and (t * 16) % 2 < 1: beam *= 0.2
    c.save(); cam(c, 1.0 + 0.25 * ease(clamp(t / 6)), 640, 1000)
    facade_across(c, t, beam, ease(clamp((t - on_t - 0.6) / 3.0)))
    c.restore()
    vignette(c, 0.6)

def helix_logo(c, x, y, s, a=255):
    c.save(); c.translate(x, y); c.scale(s, s)
    hexp = skia.Path()
    for i in range(6):
        ang = math.radians(60 * i - 30); px, py = math.cos(ang) * 60, math.sin(ang) * 60
        (hexp.moveTo if i == 0 else hexp.lineTo)(px, py)
    hexp.close(); c.drawPath(hexp, stroke(C(40, 210, 196, a), 9))
    for ph in (0, math.pi):
        p = skia.Path()
        for k in range(21):
            yy = -40 + k * 4; xx = math.sin(k / 20 * 2 * math.pi + ph) * 24
            (p.moveTo if k == 0 else p.lineTo)(xx, yy)
        c.drawPath(p, stroke(C(40, 210, 196, a), 6))
    c.restore()

def truck(c, x, gy, s=1.0, door_k=1.0, t=0):
    c.save(); c.translate(x, gy); c.scale(s, s)
    outlined_rect(c, -420, -380, 220, -60, C(226, 230, 234), 9, 14)
    outlined_rect(c, 220, -260, 420, -60, C(210, 214, 220), 9, 30)
    outlined_rect(c, 290, -240, 400, -150, C(60, 80, 100), 6, 10)
    helix_logo(c, -250, -230, 1.1); c.drawString("HELIX", -170, -195, font("Anton", 90), fill(C(30, 60, 70)))
    for wx in (-300, 60, 320): c.drawCircle(wx, -50, 62, fill(OUT)); c.drawCircle(wx, -50, 30, fill(C(140, 140, 150)))
    c.drawLine(-420, -110, 220, -110, stroke(C(40, 210, 196), 10))
    if (t % 0.7) < 0.35: c.drawCircle(320, -275, 18, glow(C(255, 160, 40, 220), 8))
    c.restore()

def s_trucks(c, t, T_):
    g0 = T("N15"); col_t = T("N16") - g0
    c.save(); cam(c, 1.25, 540, 1200)
    sky(c, C(70, 76, 96), C(120, 120, 130))
    building_far = random.Random(5)
    skyline(c, 51, 1000, 300, 600, C(70, 70, 86), None)
    rect(c, -600, 1000, W + 600, H + 700, fill(C(76, 74, 82)))
    for i in range(-2, 8): rect(c, i * 260 - (t * 0) % 260, 1300, i * 260 + 140, 1316, fill(C(200, 190, 110)))
    tx = lerp(1500, 620, ease_out(clamp(t / 2.4)))
    truck(c, tx, 1250, 1.0, t=t)
    # zombies being pushed toward the truck (cage at its back)
    if t > col_t - 1.5:
        for i in range(4):
            k = clamp((t - col_t + 1.5 - i * 0.7) / 2.5)
            zx = lerp(-260 - i * 150, tx - 380, k); gy = 1420 + (i % 2) * 40
            stick(c, zx, gy, 260, zwalk(t * 3 + i, 0.7), ZOMB, face=1, expr="z", alpha=int(255 * (1 - clamp((k - 0.9) * 10))))
    for i, (sx_, gy) in enumerate(((380, 1440), (180, 1500), (640, 1520))):
        if t < 1.2 + i * 0.5: continue
        k = ease_out(clamp((t - 1.2 - i * 0.5) / 1.0))
        x = lerp(tx - 100, sx_, k)
        p = walk(t * 7 + i) if k < 1 else pose(uaR=70, laR=-10, uaL=50, laL=-30)
        stick(c, x, gy, 290, p, SUIT, face=-1, look=0.3)
        hx, hy = wpt(x, gy, 290, p, -1, "handR"); c.drawLine(hx, hy, hx - 140, hy + 40, stroke(OUT, 9))
        c.drawCircle(hx - 150, hy + 44, 16, stroke(TEAL, 6))
    c.restore()
    grade(c, C(190, 205, 230))
    # we're peeking through a gap in the curtains
    rect(c, -10, -10, 90, H + 10, fill(C(90, 26, 34))); rect(c, 990, -10, W + 10, H + 10, fill(C(90, 26, 34)))
    for x in (30, 1030): c.drawLine(x, 0, x, H, stroke(C(66, 18, 26), 8))

def s_lookup(c, t, T_):
    up = ease(clamp((t - 0.6) / 0.7))
    c.save(); cam(c, 1.0 + 0.35 * ease(clamp(t / 2.6)), W / 2, lerp(1100, 900, ease(clamp(t / 2.6))))
    rect(c, -600, -600, W + 600, H + 600, lin(c, 0, 0, 0, H, [C(80, 84, 100), C(60, 60, 74)]))
    rect(c, -600, 1500, W + 600, H + 700, fill(C(70, 68, 76)))
    p = pose(lean=-8 * up, head=-40 * up, uaR=-60 * up + 12, laR=-60 * up)
    stick(c, 540, 1550, 720, p, SUIT, face=1, look=0.2)
    if up > 0.6:
        hx, hy = wpt(540, 1550, 720, p, 1, "handR")
        cone = skia.Path(); cone.moveTo(hx, hy - 10); cone.lineTo(hx - 400, -300); cone.lineTo(hx + 300, -300); cone.close()
        pp = fill(C(0, 0, 0)); pp.setShader(skia.GradientShader.MakeLinear([skia.Point(hx, hy), skia.Point(hx, -300)], [C(220, 255, 250, int(160 * (up - 0.6) / 0.4)), C(220, 255, 250, 0)], None))
        c.drawPath(cone, pp)
    helix_logo(c, 590, 1180, 0.8)
    c.restore()
    vignette(c, 0.6)

def s_getdown(c, t, T_):
    c.save(); cam(c, 1.2, 640, 1150, *shake(t, 3 if t < 0.5 else 0))
    apt(c, t, lamp=0, curtains=0.85, city_lit=0)
    duck = ease_out(clamp((t - 0.25) / 0.25))
    p = mix(pose(lean=10, head=-6, uaL=60, laL=-60, uaR=70, laR=-50), pose(lean=40, head=10, ulL=110, llL=150, ulR=100, llR=150, uaL=100, laL=-80, uaR=110, laR=-90, bob=-0.22), duck)
    stick(c, 760, 1500, 470, p, HERO, face=1, expr="scared", look=0.3, scarf_t=t)
    sweep = math.sin(t * 2.2) * 300
    c.drawCircle(780 + sweep, 760, 240, rad(780 + sweep, 760, 240, [C(220, 255, 250, 120), C(220, 255, 250, 0)]))
    dark(c, 0.55)
    c.restore()

def s_corner(c, t, T_):
    g = GT; rv = T("JS3") + 0.45
    f1 = lightning_k(g, rv) * 1.4; f2 = lightning_k(g, rv + 0.55) * 0.8
    fl = min(1.0, f1 + f2)
    c.save(); cam(c, 1.6, 760, 1230 if g < rv - 0.05 else 1060, *shake(t, 9 * fl))
    apt(c, t, lamp=0, curtains=0.3, city_lit=0, flash=fl)
    if g >= rv:   # it was standing at the glass
        c.save(); c.clipRect(skia.Rect.MakeLTRB(560, 520, 980, 1040))
        if f1 > 0.05:
            zs = dict(ZOMB, body=C(10, 12, 14), head=C(10, 12, 14), out=C(0, 0, 0))
            stick(c, 760, 1500, 820, pose(lean=-6, head=-8, uaL=-150, laL=-20, uaR=-160, laR=10), zs, face=-1, expr="z", look=0.0)
        elif g < rv + 0.55:
            for ex in (-24, 22):
                gl = fill(C(255, 230, 120, 150)); gl.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 10))
                c.drawCircle(735 + ex, 730, 12, gl)
        for hx in (640, 880):   # hand prints left on the glass
            c.drawCircle(hx, 640, 34, fill(C(150, 170, 140, 90))); c.drawCircle(hx, 640, 34, stroke(C(90, 110, 80, 120), 4))
        c.restore()
    curl = ease(clamp((g - rv) / 0.25))
    p = mix(pose(lean=-4, head=14, ulL=70, llL=110, ulR=62, llR=120, uaL=34, laL=-104, uaR=50, laR=-112),
            pose(lean=22, head=30, ulL=95, llL=150, ulR=90, llR=150, uaL=60, laL=-120, uaR=70, laR=-120), curl)
    hero_reading(c, 830, 1500, 460, t, "scared" if curl > 0.2 else "worry", 0.2, p=p, face=-1)
    dark(c, 0.6 * (1 - fl))
    c.restore()
    if fl > 0: rect(c, 0, 0, W, H, fill(C(220, 230, 255, int(90 * fl))))

def lightning_k(t, t0):
    k = t - t0
    if k < 0 or k > 0.35: return 0.0
    return (1 - k / 0.35) * (0.6 + 0.4 * math.sin(k * 90))

def s_nobody(c, t, T_):
    fl = lightning_k(t, 0.9) * 0.7
    c.save(); cam(c, 2.2 + 0.25 * t / 3, 800, 1090)
    apt(c, t, lamp=0, curtains=0.3, city_lit=0, flash=fl)
    p = pose(lean=22, head=30, ulL=95, llL=150, ulR=90, llR=150, uaL=60, laL=-120, uaR=70, laR=-120)
    hero_reading(c, 830, 1500, 460, t, "shock", 0.0, p=p, face=-1)
    dark(c, 0.5 * (1 - fl))
    c.restore()

def s_rule4(c, t, T_):
    c.save(); cam(c, 1.4, 520, 1170)
    apt(c, t, lamp=0, curtains=1.0, city_lit=0)
    outlined_rect(c, 560, 1330, 760, 1500, C(60, 110, 70), 8, 30); outlined_rect(c, 600, 1290, 720, 1340, C(60, 110, 70), 6, 16)
    hero_reading(c, 380, 1500, 460, t, "determined", 0.6, p=pose(lean=-6, head=14, ulL=70, llL=90, ulR=60, llR=100, uaL=40, laL=-100, uaR=55, laR=-112))
    dark(c, 0.55)
    c.restore()

def s_battery(c, t, T_):
    rect(c, 0, 0, W, H, fill(C(6, 6, 10)))
    c.save(); c.translate(W / 2, 900); s = 1.0 + 0.05 * t; c.scale(s, s)
    blink = (t % 0.8) < 0.5
    rrect(c, -330, -150, 330, 150, 46, stroke(C(230, 230, 236), 18)); rrect(c, 340, -55, 380, 55, 14, fill(C(230, 230, 236)))
    if blink: rrect(c, -300, -120, -270, 120, 14, fill(C(255, 40, 40)))
    c.restore()
    text_c(c, "1%", W / 2, 1290, font("Anton", 200), C(255, 50, 50) if blink else C(150, 30, 30))
    text_c(c, "LOW BATTERY", W / 2, 1380, inter("Bold", 48), C(200, 200, 210))

def dawn_sky(c, k=1.0):
    sky(c, C(40, 46, 96), C(250, 150, 110), 0, 1300)
    c.drawCircle(760, 1250, 260, rad(760, 1250, 300, [C(255, 220, 160, 220), C(255, 180, 120, 0)]))

def s_run(c, t, T_):
    c.save(); cam(c, 1.0, W / 2, 1000, *shake(t, 4))
    dawn_sky(c)
    off = t * 900
    c.save(); c.translate((off * 0.2) % 600, 0); skyline(c, 61, 1250, 260, 600, C(60, 50, 90), None, x0=-900, x1=W + 300); c.restore()
    c.save(); c.translate((off * 0.5) % 800, 0); skyline(c, 62, 1340, 160, 420, C(40, 34, 64), C(255, 200, 140), 0.05, x0=-1100, x1=W + 300); c.restore()
    rect(c, -600, 1380, W + 600, H + 700, fill(C(70, 64, 80)))
    for i in range(-3, 9):
        x = (i * 300 + off) % 2700 - 900; rect(c, x, 1560, x + 160, 1578, fill(C(220, 210, 140)))
    stick(c, 380, 1520, 480, run(t * 15), HERO, face=-1, expr="determined", look=0.2, scarf_t=t, wind=1.0)
    for i in range(7):
        x = 760 + i * 110 + math.sin(t * 3 + i) * 30 - min(1, t / 3) * 60; gy = 1480 + (i % 3) * 60
        stick(c, x, gy, 360 - (i % 3) * 30, run(t * 13 + i * 1.7, 0.85), ZOMB, face=-1, expr="z", look=-0.2)
    c.restore()
    speed_lines(c, t, 0.9)
    rect(c, 0, 0, W, H, fill(C(255, 120, 60, 20)))

def bridge(c, t, fog=1.0):
    dawn_sky(c)
    rect(c, -600, 1300, W + 600, H + 700, lin(c, 0, 1300, 0, H, [C(110, 90, 130), C(40, 40, 70)]))
    for tx in (-120, 980):
        outlined_rect(c, tx - 60, 420, tx + 60, 1460, C(90, 70, 100), 8, 6)
        rect(c, tx - 40, 600, tx + 40, 700, fill(C(250, 160, 120)))
    cab = skia.Path(); cab.moveTo(-120, 430); cab.quadTo(430, 1450, 980, 430)
    c.drawPath(cab, stroke(OUT, 14))
    for x in range(-60, 980, 70):
        k = (x + 120) / 1100; cy = 430 + (1 - (2 * k - 1) ** 2) * 510
        c.drawLine(x, cy, x, 1400, stroke(OUT, 4))
    rect(c, -600, 1400, W + 600, 1520, fill(C(60, 52, 70))); c.drawLine(-600, 1400, W + 600, 1400, stroke(OUT, 9))
    for x in range(-600, W + 600, 60): c.drawLine(x, 1330, x, 1400, stroke(OUT, 5))
    c.drawLine(-600, 1330, W + 600, 1330, stroke(OUT, 8))
    rect(c, -600, 1520, W + 600, H + 700, lin(c, 0, 1520, 0, H, [C(200, 140, 130), C(60, 50, 80)]))

def fog_layer(c, t, k):
    for i in range(6):
        x = (i * 400 + t * 40) % 2200 - 600
        c.drawCircle(x, 1300 + (i % 2) * 60, 360, glow(C(230, 210, 220, int(90 * k)), 90))

def s_bridge(c, t, T_):
    g0 = T("N22"); bz = T("N23") - g0
    c.save(); cam(c, 1.3 + 0.15 * ease(clamp(t / 7)), lerp(420, 540, ease(clamp(t / 2.2))), 1180)
    bridge(c, t)
    hx = lerp(-200, 540, ease_out(clamp(t / 2.2)))
    if t < 2.2: hp = run(t * 13, 0.8)
    elif t < bz: hp = idle(t)
    else: hp = hold_phone(t)
    lk = math.sin(t * 1.5) if 2.4 < t < bz else 0.6
    stick(c, hx, 1400, 430, hp, HERO, face=1 if lk > -0.2 else -1, expr="worry", look=abs(lk), scarf_t=t, wind=0.6, blink=blink_at(t))
    if t > bz:
        px, py = wpt(hx, 1400, 430, hp, 1, "handR"); small_phone(c, px + 6, py - 10, 430 / 420, 1.0, 1.0 if t - bz < 1.0 else 0, t)
    fog_layer(c, t, 1.0)
    c.restore()

def s_turn(c, t, T_):
    g = GT; js = T("JS4"); turn1 = js + 0.15; back = js + 2.55; snap = js + 3.3
    if g < snap:
        look_fog = ease(clamp((g - turn1) / 0.8)) * (1 - ease(clamp((g - back) / 0.6)))
        z = 1.3 + 0.12 * ease(clamp((g - turn1) / 2.4)); cx = lerp(560, 300, look_fog)
    else:
        k = ease_out(clamp((g - snap) / 0.12)); z = lerp(1.6, 2.4, k) + 0.06 * (g - snap); cx = lerp(520, 470, k)
    sx, sy = shake(g, 14 * (1 - clamp((g - snap) / 0.7)) if g >= snap else 1.5, 50)
    c.save(); cam(c, z, cx, 1100 if g < snap else 1060, sx, sy)
    bridge(c, t + 10)
    fog_layer(c, t + 10, 1.0)
    if g >= snap:
        sp = pose(lean=8, head=-6, uaR=70, laR=-20, uaL=-10, laL=-8)
        stick(c, 420, 1400, 470, sp, SUIT, face=1, look=0.6)
        helix_logo(c, 455, 1205, 0.4)
    if g < turn1: face, ex, hp = 1, "worry", idle(t, 0.3)
    elif g < back: face, ex, hp = -1, "scared", mix(idle(t), scared(t), clamp((g - turn1) / 0.3))
    elif g < snap: face, ex, hp = 1, "worry", idle(t, 0.5)
    else: face, ex, hp = 1, "shock", scared(t)
    stick(c, 560, 1400, 430, hp, HERO, face=face, expr=ex, look=0.6 if face > 0 else 0.9, scarf_t=t, wind=0.4)
    fog_layer(c, t + 30, 0.6)
    c.restore()
    if snap <= g < snap + 0.1: rect(c, 0, 0, W, H, fill(C(255, 255, 255, int(255 * (1 - (g - snap) / 0.1)))))
    hb = 0.5 + 0.5 * math.sin(t * 7)
    vignette(c, 0.5 + 0.3 * hb)

def s_black(c, t, T_):
    rect(c, 0, 0, W, H, fill(C(0, 0, 0)))
    if t < 0.35: rect(c, 0, H / 2 - 4, W, H / 2 + 4, fill(C(255, 255, 255, int(255 * (1 - t / 0.35)))))

def s_cta(c, t, T_):
    rect(c, 0, 0, W, H, fill(C(8, 8, 12)))
    c.drawCircle(W / 2, 760, 700, rad(W / 2, 760, 700, [C(254, 97, 0, 70), C(254, 97, 0, 0)]))
    k = back_out(clamp(t / 0.35))
    c.save(); c.translate(W / 2, 640); c.scale(k, k)
    c.drawCircle(0, 0, 150, fill(C(90, 90, 100))); text_c(c, "?", 0, 64, inter("Bold", 190), C(230, 230, 236))
    c.restore()
    text_c(c, "WHO IS THE", W / 2, 960, font("Lucky", 110), C(255, 255, 255), OUT, 18)
    text_c(c, "UNKNOWN NUMBER?", W / 2, 1090, font("Lucky", 104), C(254, 97, 0), OUT, 18)
    k2 = back_out(clamp((t - 1.0) / 0.3))
    c.save(); c.translate(W / 2, 1290); c.scale(k2, k2)
    rrect(c, -380, -70, 380, 50, 50, fill(C(255, 255, 255)))
    text_c(c, "COMMENT YOUR GUESS", 0, 10, font("Anton", 64), C(17, 17, 17)); c.restore()
    k3 = back_out(clamp((t - 2.0) / 0.3))
    c.save(); c.translate(W / 2, 1420); c.scale(k3, k3)
    text_c(c, "FOLLOW FOR PART 2", 0, 0, font("Anton", 70), C(255, 214, 10)); c.restore()

ICON = None
def s_end(c, t, T_):
    global ICON
    if ICON is None: ICON = skia.Image.open("icon-512.png")
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

# ---------------------------------------------------------------- shot list (start, end, fn, day, transition)
def _shots():
    b = [
     (0.0, s_pov, None, None), (T("U1") - 0.4, s_hook, None, "cut"), (E("N3") + 0.35, s_title, None, "cut"), (T("U3") - 0.45, s_day0, 0, "flash"),
     (T("N4") - 0.05, s_store, 0, "punch"), (T("N5") - 0.05, s_lock, 0, "punch"), (T("N6") - 0.05, s_alert, 0, "flash"),
     (T("N7") - 0.1, s_chaos, 0, "punch"), (T("U6") - 1.2, s_rule1, 1, "cut"),
     (T("N8") - 0.1, s_knock, 3, "punch"), (frac("N8", 0.33), s_peep, 3, "punch"), (T("N9") - 0.1, s_hand, 3, "punch"),
     (T("N10") - 0.1, s_peep2, 3, "punch"), (T("U8") - 1.2, s_rule2, 7, "cut"), (T("N11") - 0.1, s_roof, 7, "punch"),
     (T("N12") - 0.05, s_box, 7, "punch"), (T("N13") - 0.1, s_power, 12, "flash"), (T("U9") - 1.2, s_rule3, 12, "cut"),
     (T("N14") - 0.1, s_across, 12, "punch"), (T("N15") - 0.1, s_trucks, 18, "flash"), (T("N17") - 0.05, s_lookup, 18, "punch"),
     (T("U10") - 0.1, s_getdown, 18, "punch"), (T("N18") - 0.3, s_corner, 23, "flash"), (T("N19") - 0.05, s_nobody, 23, "punch"),
     (T("U13") - 0.45, s_rule4, 29, "flash"), (T("N20") - 0.1, s_battery, 29, "punch"), (T("N21") - 0.1, s_run, 30, "flash"),
     (T("N22") - 0.1, s_bridge, 30, "punch"), (T("U14") - 0.2, s_turn, 30, "cut"), (E("N24") + 0.5, s_black, None, "cut"),
     (T("N25") - 0.15, s_cta, None, "punch"), (D["story_end"], s_end, None, "punch"),
    ]
    out = []
    for i, (a, fn, d, tr) in enumerate(b):
        e = b[i + 1][0] if i + 1 < len(b) else TOTAL
        out.append((a, e, fn, d, tr))
    return out
SHOTS = _shots()

def day_at(t):
    for a, b, fn, d, tr in SHOTS:
        if a <= t < b: return d
    return None

def draw_counter(c, t):
    d = day_at(t)
    if d is None: return
    c.save(); c.translate(W / 2, 200)
    rrect(c, -170, -58, 170, 58, 36, fill(C(0, 0, 0, 170))); rrect(c, -170, -58, 170, 58, 36, stroke(C(255, 255, 255, 60), 4))
    f1 = font("Anton", 42); f2 = font("Anton", 86)
    c.drawString("DAY", -130, 20, f1, fill(C(254, 97, 0)))
    s = f"{d}"; tw = f2.measureText(s); c.drawString(s, 60 - tw / 2 + 10, 30, f2, fill(C(255, 255, 255)))
    rrect(c, -130, 72, 130, 82, 5, fill(C(255, 255, 255, 60))); rrect(c, -130, 72, -130 + 260 * clamp(d / 30), 82, 5, fill(C(254, 97, 0)))
    c.restore()

GRAIN = None
def grain(c, t):
    global GRAIN
    if GRAIN is None:
        rnd = np.random.default_rng(3)
        n = (rnd.normal(0, 1, (480, 270)) * 40 + 128).clip(0, 255).astype(np.uint8)
        GRAIN = skia.Image.fromarray(np.dstack([n, n, n, np.full_like(n, 22)]), colorType=skia.kRGBA_8888_ColorType)
    ox = (int(t * 60) * 37) % 200; oy = (int(t * 60) * 53) % 300
    p = skia.Paint(); p.setBlendMode(skia.BlendMode.kOverlay)
    c.drawImageRect(GRAIN, skia.Rect.MakeLTRB(-ox, -oy, W - ox + 400, H - oy + 600), skia.SamplingOptions(), p)

NOVIG = {s_title, s_alert, s_black, s_cta, s_end, s_battery, s_chaos, s_trucks, s_peep, s_peep2, s_across, s_lookup, s_turn}
GT = 0.0
STILL = None
RULES = [("U6", "RULE #1"), ("U8", "RULE #2"), ("U9", "RULE #3")]
def draw_rulecards(c, t):
    for k, lab in RULES:
        a = T(k) - 1.15; b = T(k) - 0.3
        if a <= t < b:
            lt = t - a; q = back_out(clamp(lt / 0.18), 2.4); fade = 1 - clamp((t - (b - 0.15)) / 0.15)
            rect(c, 0, 0, W, H, fill(C(6, 0, 2, int(235 * fade))))
            sx, sy = shake(t, 8, 50)
            c.save(); c.translate(W / 2 + sx, 1000 + sy); c.scale(q, q)
            for dx, col in ((-9, C(0, 255, 255, int(120 * fade))), (9, C(255, 0, 60, int(160 * fade)))):
                text_c(c, lab, dx, 0, font("Lucky", 200), col)
            text_c(c, lab, 0, 0, font("Lucky", 200), C(255, 40, 50, int(255 * fade)), C(0, 0, 0, int(255 * fade)), 26)
            c.restore()

def draw_countdown(c, fn, lt):
    base = {"s_day0": 16 * 3600 + 34 * 60 + 12, "s_store": 14 * 3600 + 7 * 60 + 40, "s_lock": 119, "s_alert": 59}.get(fn.__name__)
    if base is None: return
    rem = max(0, int(base - lt * (1.0 if fn.__name__ != "s_alert" else 1.0)))
    hms = f"{rem // 3600:02d}:{rem // 60 % 60:02d}:{rem % 60:02d}"
    blink = (lt % 1.0) < 0.5 or rem > 600
    c.save(); c.translate(W / 2, 318)
    rrect(c, -250, -38, 250, 38, 38, fill(C(150, 0, 10, 220) if blink else C(80, 0, 6, 220)))
    text_c(c, "MIDNIGHT IN  " + hms, 0, 16, font("Anton", 44), C(255, 255, 255))
    c.restore()

def danger_ranges():
    return [(frac("N4", 0.8), E("U5")), (T("N6"), E("N7") + 0.3), (T("JS2") + 1.35, E("N10b")), (T("N21"), E("N21")), (T("JS4") + 3.3, E("N24"))]
DANGER = None
def draw_danger(c, t):
    global DANGER
    if DANGER is None: DANGER = danger_ranges()
    for a, b in DANGER:
        if a <= t < b:
            k = min(clamp((t - a) / 0.3), clamp((b - t) / 0.3)); hb = 0.5 + 0.5 * math.sin(t * 7.5)
            c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), rad(W / 2, H * 0.45, H * 0.8, [C(255, 0, 20, 0), C(255, 0, 20, int(40 * k)), C(200, 0, 10, int((110 + 60 * hb) * k))], [0, 0.5, 1.0]))

HANDHELD_OFF = None
def frame(c, t):
    global GT, HANDHELD_OFF
    GT = t
    if HANDHELD_OFF is None: HANDHELD_OFF = {s_title, s_black, s_cta, s_end, s_battery, s_alert}
    c.clear(C(0, 0, 0))
    for a, b, fn, d, tr in SHOTS:
        if a <= t < b:
            lt = t - a
            c.save()
            if tr in ("punch", "flash") and lt < 0.3:
                z = 1 + 0.07 * (1 - ease_out(lt / 0.3)); c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2)
            if fn not in HANDHELD_OFF:   # nervous handheld camera + slow creeping push-in
                z = 1.0 + 0.04 * clamp(lt / max(1.0, b - a))
                c.translate(W / 2 + 6 * math.sin(t * 1.3) + 3 * math.sin(t * 3.1), H / 2 + 5 * math.cos(t * 1.1) + 2 * math.sin(t * 2.7))
                c.rotate(0.45 * math.sin(t * 0.8)); c.scale(z, z); c.translate(-W / 2, -H / 2)
            fn(c, lt, b - a)
            c.restore()
            draw_countdown(c, fn, lt)
            if tr == "flash" and lt < 0.2: rect(c, 0, 0, W, H, fill(C(255, 255, 255, int(200 * (1 - lt / 0.2)))))
            if fn not in NOVIG: vignette(c, 0.5)
            break
    draw_danger(c, t)
    draw_chat(c, t)
    draw_banners(c, t)
    draw_rulecards(c, t)
    draw_counter(c, t)
    if day_at(t) is not None or t < E("N3") + 0.3: draw_caption(c, t)
    grain(c, t)

def main():
    mode = sys.argv[1]
    surf = skia.Surface(W, H); c = surf.getCanvas()
    if mode == "preview":
        for ts in sys.argv[2:]:
            t = float(ts); frame(c, t); surf.makeImageSnapshot().save(f"prev/p_{t:06.2f}.jpg", skia.kJPEG, 80)
        return
    if mode == "sheet":   # contact sheet of many times
        ts = [float(x) for x in sys.argv[3:]]; out = sys.argv[2]
        from PIL import Image
        thumbs = []
        for t in ts:
            frame(c, t); arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
            thumbs.append(Image.fromarray(arr[:, :, :3]).resize((270, 480)))
        cols = 6; rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 270, rows * 480))
        for i, im in enumerate(thumbs): sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
        sheet.save(out, quality=85); return
    t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "15", "-tune", "animation", "-pix_fmt", "yuv420p",
                           "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        frame(c, n / FPS)
        ff.stdin.write(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        if n % 600 == 0: print("frame", n, flush=True)
    ff.stdin.close(); ff.wait(); print("done", out)

if __name__ == "__main__":
    main()
