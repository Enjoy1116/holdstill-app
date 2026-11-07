# Character rig for "I Survived 100 Days": stick figures, zombies and Biscuit the dog, drawn with skia.
import math, random
import skia

def C(r, g, b, a=255):
    return skia.Color(int(r), int(g), int(b), int(a))

def lerp(a, b, k): return a + (b - a) * k
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_in(x): x = clamp(x); return x ** 3
def back_out(x, s=1.70158):
    x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1

def stroke(col, w):
    return skia.Paint(AntiAlias=True, Color=col, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=skia.Paint.kRound_Cap, StrokeJoin=skia.Paint.kRound_Join)
def fill(col):
    return skia.Paint(AntiAlias=True, Color=col, Style=skia.Paint.kFill_Style)

OUT = C(18, 16, 24)
HERO = dict(body=C(250, 248, 242), out=OUT, scarf=C(254, 97, 0), head=C(250, 248, 242), eye=C(20, 20, 28), kind="hero")
ZOMB = dict(body=C(118, 150, 104), out=C(20, 30, 22), head=C(146, 184, 120), eye=C(255, 236, 120), kind="zombie")
CIVS = [dict(body=C(*c), out=OUT, head=C(250, 230, 210), eye=C(20, 20, 28), kind="civ")
        for c in ((80, 140, 230), (230, 80, 90), (90, 190, 120), (240, 190, 60), (170, 110, 220))]

# lengths in units of character height (~1.0 from feet to top of head)
L_TORSO, L_NECK, R_HEAD = 0.29, 0.03, 0.115
L_UA, L_LA, L_UL, L_LL = 0.16, 0.15, 0.21, 0.205

BASE = dict(lean=0, head=0, uaL=-12, laL=-8, uaR=12, laR=8, ulL=-6, llL=0, ulR=6, llR=0,
            rot=0, bob=0, squash=1.0)

def pose(**kw):
    p = dict(BASE); p.update(kw); return p

def mix(a, b, k):
    return {key: lerp(a[key], b[key], k) for key in BASE}

def _dir(angle_deg, length):
    """angle 0 = straight down, positive = toward the facing direction (+x)."""
    a = math.radians(angle_deg)
    return math.sin(a) * length, math.cos(a) * length

def joints(p, s):
    """Positions relative to the hip (0,0) for a character facing +x, scale s (px for height 1)."""
    hip = (0.0, 0.0)
    lean = p["lean"]
    dx, dy = _dir(180 + lean, L_TORSO * s)            # torso goes up
    sh = (hip[0] + dx, hip[1] + dy)
    nx, ny = _dir(180 + lean + p["head"] * 0.5, L_NECK * s)
    nk = (sh[0] + nx, sh[1] + ny)
    hx, hy = _dir(180 + lean + p["head"], R_HEAD * s)
    hd = (nk[0] + hx, nk[1] + hy)
    J = dict(hip=hip, sh=sh, nk=nk, hd=hd)
    for side in "LR":
        ua = p["ua" + side] + lean; la = ua + p["la" + side]
        e = _dir(ua, L_UA * s); el = (sh[0] + e[0], sh[1] + e[1] + 0.012 * s)
        h = _dir(la, L_LA * s); hand = (el[0] + h[0], el[1] + h[1])
        ul = p["ul" + side]; ll = ul - abs(p["ll" + side])     # knees bend backward
        k = _dir(ul, L_UL * s); kn = (hip[0] + k[0], hip[1] + k[1])
        f = _dir(ll, L_LL * s); ft = (kn[0] + f[0], kn[1] + f[1])
        J["el" + side], J["hand" + side], J["kn" + side], J["ft" + side] = el, hand, kn, ft
    return J

def foot_drop(p, s):
    J = joints(p, s)
    return max(J["ftL"][1], J["ftR"][1])

def _limb(c, pts, col, out, w):
    path = skia.Path(); path.moveTo(*pts[0])
    for q in pts[1:]: path.lineTo(*q)
    c.drawPath(path, stroke(out, w + w * 0.55))
    c.drawPath(path, stroke(col, w))

def draw_face(c, x, y, r, st, expr, face, look, blink):
    eye = st["eye"]
    if st["kind"] == "zombie":
        # glowing empty eyes and a jagged mouth
        glow = fill(C(255, 230, 120, 120)); glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, r * 0.25))
        for ex in (-0.32, 0.22):
            c.drawCircle(x + (ex + 0.18 * look) * r * face, y - 0.12 * r, r * 0.26, glow)
            c.drawCircle(x + (ex + 0.18 * look) * r * face, y - 0.12 * r, r * 0.14, fill(eye))
        m = skia.Path(); mx = x + 0.1 * r * face; my = y + 0.38 * r
        m.moveTo(mx - 0.32 * r, my)
        for i in range(1, 7):
            m.lineTo(mx - 0.32 * r + i * 0.107 * r, my + (0.1 * r if i % 2 else -0.04 * r))
        c.drawPath(m, stroke(C(30, 40, 30), r * 0.08))
        return
    ex0 = x + 0.18 * look * r * face
    h = 0.3 * r * (0.12 if blink else 1.0)
    if expr == "shock":
        h *= 1.35
    for ex in (-0.3, 0.3):
        cx = ex0 + ex * r
        c.drawOval(skia.Rect.MakeLTRB(cx - 0.13 * r, y - 0.12 * r - h / 2, cx + 0.13 * r, y - 0.12 * r + h / 2), fill(eye))
        if not blink and expr != "sleep":
            c.drawCircle(cx + 0.04 * r, y - 0.12 * r - h * 0.2, r * 0.05, fill(C(255, 255, 255)))
    bp = stroke(eye, r * 0.07)
    if expr in ("worry", "shock", "sad", "scared"):
        for sgn in (-1, 1):
            cx = ex0 + sgn * 0.3 * r
            c.drawLine(cx - 0.14 * r, y - 0.46 * r + (0.08 * r if sgn < 0 else -0.02 * r) * (1 if expr != "sad" else -1),
                       cx + 0.14 * r, y - 0.46 * r + (-0.02 * r if sgn < 0 else 0.08 * r) * (1 if expr != "sad" else -1), bp)
    elif expr in ("angry", "determined", "disgust"):
        for sgn in (-1, 1):
            cx = ex0 + sgn * 0.3 * r
            c.drawLine(cx - 0.14 * r, y - 0.5 * r + (-0.06 * r if sgn < 0 else 0.06 * r),
                       cx + 0.14 * r, y - 0.5 * r + (0.06 * r if sgn < 0 else -0.06 * r), bp)
    mx, my = ex0 + 0.02 * r, y + 0.36 * r
    mp = stroke(eye, r * 0.075)
    if expr in ("happy", "love"):
        c.drawArc(skia.Rect.MakeLTRB(mx - 0.3 * r, my - 0.25 * r, mx + 0.3 * r, my + 0.15 * r), 20, 140, False, mp)
    elif expr in ("shock", "scared"):
        c.drawOval(skia.Rect.MakeLTRB(mx - 0.13 * r, my - 0.12 * r, mx + 0.13 * r, my + 0.2 * r), fill(eye))
    elif expr in ("sad", "disgust"):
        c.drawArc(skia.Rect.MakeLTRB(mx - 0.25 * r, my - 0.02 * r, mx + 0.25 * r, my + 0.3 * r), 200, 140, False, mp)
        if expr == "disgust":
            c.drawLine(mx + 0.18 * r, my + 0.02 * r, mx + 0.3 * r, my + 0.1 * r, mp)
    elif expr == "sleep":
        c.drawLine(mx - 0.12 * r, my, mx + 0.12 * r, my, mp)
    else:
        c.drawLine(mx - 0.16 * r, my + 0.02 * r, mx + 0.16 * r, my - 0.01 * r, mp)

def stick(c, x, gy, s, p, st=HERO, face=1, expr="neutral", look=0.0, blink=False, scarf_t=0.0, alpha=255, plant=True, wind=0.0):
    """Draw a stick figure whose feet touch ground y=gy (if plant) at x. face=1 right, -1 left."""
    J = joints(p, s)
    drop = foot_drop(p, s) if plant else L_UL * s + L_LL * s
    hy = gy - drop - p["bob"] * s
    c.save()
    c.translate(x, hy)
    if p["rot"]: c.rotate(p["rot"] * face)
    c.scale(face, 1)
    w = s * 0.062
    if alpha < 255:
        c.saveLayerAlpha(None, alpha)
    body = st["body"]; dark = C(*(int(v * 0.72) for v in (skia.ColorGetR(body), skia.ColorGetG(body), skia.ColorGetB(body))))
    # back limbs (L) first, darker for depth
    _limb(c, [J["sh"], J["elL"], J["handL"]], dark, st["out"], w)
    _limb(c, [J["hip"], J["knL"], J["ftL"]], dark, st["out"], w)
    _limb(c, [J["hip"], J["sh"], J["nk"]], body, st["out"], w * 1.12)
    _limb(c, [J["hip"], J["knR"], J["ftR"]], body, st["out"], w)
    if st["kind"] == "hero":       # scarf flowing behind
        sx, sy = J["nk"]
        wave = math.sin(scarf_t * 9) * 0.03 * s * (0.4 + wind)
        hang = [(sx - 0.03 * s, sy + 0.05 * s), (sx - 0.05 * s, sy + 0.11 * s), (sx - 0.06 * s + wave * 0.3, sy + 0.17 * s)]
        fly = [(sx - 0.09 * s, sy + 0.01 * s + wave), (sx - 0.16 * s, sy - 0.01 * s - wave), (sx - 0.23 * s, sy + 0.02 * s + wave)]
        q = [(lerp(a[0], b[0], wind), lerp(a[1], b[1], wind)) for a, b in zip(hang, fly)]
        sp = skia.Path(); sp.moveTo(sx - 0.01 * s, sy + 0.005 * s)
        sp.cubicTo(q[0][0], q[0][1], q[1][0], q[1][1], q[2][0], q[2][1])
        c.drawPath(sp, stroke(st["out"], w * 1.25)); c.drawPath(sp, stroke(st["scarf"], w * 0.8))
        c.drawCircle(sx, sy, w * 0.75, fill(st["scarf"]))
    if st["kind"] == "zombie":     # torn shirt scrap
        shp = skia.Path(); a, b = J["hip"], J["sh"]
        shp.moveTo(lerp(a[0], b[0], 0.15) - w, lerp(a[1], b[1], 0.15)); shp.lineTo(lerp(a[0], b[0], 0.85) - w, lerp(a[1], b[1], 0.85))
        shp.lineTo(lerp(a[0], b[0], 0.85) + w * 1.1, lerp(a[1], b[1], 0.85)); shp.lineTo(lerp(a[0], b[0], 0.3) + w * 1.3, lerp(a[1], b[1], 0.3))
        shp.lineTo(lerp(a[0], b[0], 0.2) + w * 0.4, lerp(a[1], b[1], 0.1)); shp.close()
        c.drawPath(shp, fill(C(70, 64, 84))); c.drawPath(shp, stroke(st["out"], w * 0.35))
    _limb(c, [J["sh"], J["elR"], J["handR"]], body, st["out"], w)
    hx, hy2 = J["hd"]; r = R_HEAD * s
    c.drawCircle(hx, hy2, r + w * 0.3, fill(st["out"]))
    c.drawCircle(hx, hy2, r - w * 0.05, fill(st["head"]))
    c.save(); c.scale(face, 1)
    draw_face(c, hx * face, hy2, r, st, expr, 1, look * face if face else look, blink)
    c.restore()
    if alpha < 255:
        c.restore()
    c.restore()
    return J

# ---------- poses
def walk(ph, amp=1.0):
    s = math.sin(ph); c2 = math.cos(ph)
    return pose(lean=4 * amp, ulL=-24 * s * amp, llL=max(0, 40 * math.sin(ph - 1.2)) * amp, ulR=24 * s * amp,
                llR=max(0, 40 * math.sin(ph + math.pi - 1.2)) * amp,
                uaL=22 * s * amp, laL=-18 * amp, uaR=-22 * s * amp, laR=18 * amp, bob=0.012 * abs(c2) * amp)

def run(ph, amp=1.0):
    s = math.sin(ph)
    return pose(lean=16 * amp, head=-6, ulL=-48 * s * amp + 10, llL=(55 + 35 * math.sin(ph - 1.0)) * amp,
                ulR=48 * s * amp + 10, llR=(55 + 35 * math.sin(ph + math.pi - 1.0)) * amp,
                uaL=55 * s * amp, laL=-85 * amp, uaR=-55 * s * amp, laR=85 * amp, bob=0.035 * abs(math.cos(ph)) * amp)

def sneak(ph):
    s = math.sin(ph)
    return pose(lean=22, head=-14, ulL=-22 * s + 22, llL=60 + 15 * math.sin(ph - 1), ulR=22 * s + 22, llR=60 + 15 * math.sin(ph + 2),
                uaL=40, laL=-60, uaR=55, laR=-70, bob=-0.03)

def zwalk(ph, amp=1.0):
    s = math.sin(ph)
    return pose(lean=12, head=18 + 6 * math.sin(ph * 0.5), ulL=-16 * s * amp, llL=max(0, 22 * math.sin(ph - 1)) * amp,
                ulR=16 * s * amp, llR=max(0, 22 * math.sin(ph + 2)) * amp,
                uaL=78 + 6 * s, laL=8, uaR=86 - 6 * s, laR=4, bob=0.01 * abs(math.cos(ph)))

def idle(t, k=1.0):
    b = math.sin(t * 2.2) * 0.004 * k
    return pose(uaL=-10 - 2 * math.sin(t * 2.2), uaR=10 + 2 * math.sin(t * 2.2), bob=b)

def scared(t):
    j = math.sin(t * 40) * 1.5
    return pose(lean=-8, head=-6, uaL=40 + j, laL=-120, uaR=50 - j, laR=-110, ulL=-14, llL=14, ulR=14, llR=14, bob=-0.01)

def push(t):
    return pose(lean=34, head=-10, uaL=70, laL=10, uaR=78, laR=6, ulL=-36, llL=18, ulR=26, llR=10, bob=-0.02)

def sit():
    return pose(lean=-4, ulL=80, llL=80, ulR=86, llR=86, uaL=10, laL=40, uaR=20, laR=50)

def throw(k):
    """k 0..1: wind up, then release around 0.55."""
    if k < 0.5:
        q = ease(k / 0.5)
        return pose(lean=lerp(0, -16, q), uaR=lerp(12, -150, q), laR=lerp(8, -30, q), uaL=lerp(-12, 50, q), laL=-20,
                    ulL=lerp(-6, -24, q), ulR=lerp(6, 18, q), llR=10)
    q = ease_out((k - 0.5) / 0.5)
    return pose(lean=lerp(-16, 24, q), uaR=lerp(-150, 80, q), laR=lerp(-30, 10, q), uaL=lerp(50, -40, q), laL=-20,
                ulL=lerp(-24, -10, q), ulR=lerp(18, 30, q), llR=lerp(10, 30, q))

def cheer(t):
    w = math.sin(t * 10) * 8
    return pose(uaL=-150 + w, laL=-10, uaR=150 - w, laR=10, bob=0.02 * abs(math.sin(t * 6)))

def hold_phone(t):
    return pose(uaR=60, laR=-110, uaL=-8, laL=-4, head=8)

def brace(t):
    j = math.sin(t * 30) * 2
    return pose(lean=-20, head=6, uaL=-70 + j, laL=-20, uaR=-62 - j, laR=-24, ulL=-30, llL=20, ulR=-6, llR=30)

def lie():
    return pose(rot=-90, uaL=20, uaR=10, ulL=4, ulR=-4)

# ---------- Biscuit the dog
DOG = C(214, 148, 74); DOG_D = C(170, 108, 50)

def dog(c, x, gy, s, t, face=1, mode="walk", ph=0.0, wag=1.0, expr="happy"):
    """s = body length scale. mode: walk | run | sit | stand."""
    c.save(); c.translate(x, gy); c.scale(face, 1)
    w = s * 0.09
    o = OUT
    bob = 0
    if mode == "run": bob = -abs(math.sin(ph)) * s * 0.08
    legs = []
    hipx, shx, by = -0.3 * s, 0.3 * s, -0.36 * s + bob
    for i, (lx, phase) in enumerate(((hipx, 0), (hipx + 0.08 * s, math.pi), (shx, math.pi), (shx - 0.08 * s, 0))):
        if mode in ("walk", "run"):
            amp = 30 if mode == "walk" else 55
            a = math.radians(amp * math.sin(ph + phase))
        elif False:
            a = 0
        else:
            a = 0
        L = 0.3 * s
        legs.append(((lx, by + 0.05 * s), (lx + math.sin(a) * L, by + 0.05 * s + math.cos(a) * L * (0.55 if (mode == "sit" and i < 2) else 1))))
    for i in (1, 3):
        _limb(c, [legs[i][0], legs[i][1]], DOG_D, o, w)
    # tail
    tw = math.sin(t * 22 * wag) * 0.5 * wag
    tp = skia.Path(); tp.moveTo(hipx - 0.05 * s, by - 0.02 * s)
    tp.quadTo(hipx - 0.3 * s, by - 0.25 * s, hipx - 0.32 * s + tw * 0.2 * s, by - 0.48 * s - abs(tw) * 0.05 * s)
    c.drawPath(tp, stroke(o, w * 1.5)); c.drawPath(tp, stroke(DOG, w * 0.95))
    # body
    bodyr = skia.Rect.MakeLTRB(hipx - 0.14 * s, by - 0.26 * s, shx + 0.16 * s, by + 0.12 * s)
    if False:
        pass
    c.drawRRect(skia.RRect.MakeRectXY(bodyr, 0.17 * s, 0.17 * s), fill(o))
    c.drawRRect(skia.RRect.MakeRectXY(bodyr.makeInset(w * 0.45, w * 0.45), 0.15 * s, 0.15 * s), fill(DOG))
    c.drawOval(skia.Rect.MakeLTRB(-0.05 * s, by - 0.15 * s, 0.25 * s, by + 0.02 * s), fill(C(236, 190, 130)))
    for i in (0, 2):
        _limb(c, [legs[i][0], legs[i][1]], DOG, o, w)
    # head
    hx, hy = shx + 0.2 * s, by - 0.32 * s
    c.drawCircle(hx, hy, 0.22 * s + w * 0.4, fill(o)); c.drawCircle(hx, hy, 0.22 * s, fill(DOG))
    sn = skia.Rect.MakeLTRB(hx + 0.05 * s, hy - 0.02 * s, hx + 0.36 * s, hy + 0.16 * s)
    c.drawRRect(skia.RRect.MakeRectXY(sn.makeOutset(w * 0.4, w * 0.4), 0.09 * s, 0.09 * s), fill(o))
    c.drawRRect(skia.RRect.MakeRectXY(sn, 0.08 * s, 0.08 * s), fill(C(236, 190, 130)))
    c.drawCircle(hx + 0.34 * s, hy + 0.02 * s, 0.055 * s, fill(o))
    # ear flops
    ep = skia.Path(); ep.moveTo(hx - 0.12 * s, hy - 0.16 * s)
    ep.quadTo(hx - 0.32 * s, hy - 0.05 * s + math.sin(t * 7) * 0.02 * s, hx - 0.2 * s, hy + 0.16 * s)
    ep.quadTo(hx - 0.08 * s, hy + 0.0 * s, hx - 0.02 * s, hy - 0.18 * s); ep.close()
    c.drawPath(ep, fill(DOG_D)); c.drawPath(ep, stroke(o, w * 0.5))
    c.drawCircle(hx + 0.08 * s, hy - 0.06 * s, 0.045 * s, fill(o))
    c.drawCircle(hx + 0.095 * s, hy - 0.075 * s, 0.015 * s, fill(C(255, 255, 255)))
    if expr == "happy":
        tg = skia.Rect.MakeLTRB(hx + 0.16 * s, hy + 0.12 * s, hx + 0.26 * s, hy + 0.3 * s)
        c.drawRRect(skia.RRect.MakeRectXY(tg, 0.05 * s, 0.05 * s), fill(C(236, 90, 110)))
    # collar
    c.drawLine(hx - 0.14 * s, hy + 0.12 * s, hx + 0.04 * s, hy + 0.2 * s, stroke(C(254, 97, 0), w * 0.8))
    c.restore()
