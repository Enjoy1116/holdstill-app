# Backgrounds, props and effects for "I Survived 100 Days".
import math, random
import skia
from rig import C, stroke, fill, lerp, clamp, ease, ease_out, OUT

W, H = 1080, 1920

def lin(c, x0, y0, x1, y1, cols, pos=None):
    p = fill(C(0, 0, 0)); p.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, pos))
    return p

def rad(cx, cy, r, cols, pos=None):
    p = fill(C(0, 0, 0)); p.setShader(skia.GradientShader.MakeRadial(skia.Point(cx, cy), r, cols, pos))
    return p

def glow(col, sigma):
    p = fill(col); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma)); return p

def rect(c, l, t, r, b, paint): c.drawRect(skia.Rect.MakeLTRB(l, t, r, b), paint)
def rrect(c, l, t, r, b, rad_, paint): c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(l, t, r, b), rad_, rad_), paint)

def outlined_rect(c, l, t, r, b, col, w=7, rr=8):
    rrect(c, l - w / 2, t - w / 2, r + w / 2, b + w / 2, rr + w / 2, fill(OUT))
    rrect(c, l + w / 2, t + w / 2, r - w / 2, b - w / 2, max(1, rr - w / 2), fill(col))

def sky(c, top, bot, y0=0, y1=H):
    c.drawRect(skia.Rect.MakeLTRB(-400, y0 - 400, W + 400, y1), lin(c, 0, y0, 0, y1, [top, bot]))

def moon(c, x, y, r):
    c.drawCircle(x, y, r * 3.2, rad(x, y, r * 3.2, [C(200, 210, 255, 70), C(200, 210, 255, 0)]))
    c.drawCircle(x, y, r, fill(C(240, 240, 228)))
    for dx, dy, rr in ((-0.3, -0.2, 0.18), (0.25, 0.15, 0.12), (0.05, 0.4, 0.09)):
        c.drawCircle(x + dx * r, y + dy * r, rr * r, fill(C(214, 214, 200)))

def stars(c, seed, n, y1, t=0):
    rnd = random.Random(seed)
    for i in range(n):
        x, y = rnd.uniform(-100, W + 100), rnd.uniform(-200, y1)
        a = 120 + 100 * math.sin(t * rnd.uniform(1, 3) + i)
        c.drawCircle(x, y, rnd.uniform(1.2, 3.0), fill(C(255, 255, 255, clamp(a, 20, 255))))

_SKY_CACHE = {}
def skyline(c, seed, base_y, h0, h1, col, win_col=None, win_p=0.3, x0=-300, x1=W + 300, wmin=90, wmax=200, t=0, flicker=0.0):
    rnd = random.Random(seed)
    x = x0
    while x < x1:
        bw = rnd.uniform(wmin, wmax); bh = rnd.uniform(h0, h1)
        top = base_y - bh
        rect(c, x, top, x + bw, base_y + 2000, fill(col))
        if rnd.random() < 0.3:
            rect(c, x + bw * 0.4, top - 40, x + bw * 0.46, top, fill(col))
        if win_col is not None:
            cols = max(2, int(bw // 34)); rows = int(bh // 46)
            for i in range(cols):
                for j in range(rows):
                    r2 = rnd.random()
                    if r2 < win_p:
                        on = 1.0
                        if flicker and rnd.random() < 0.15: on = 0.5 + 0.5 * math.sin(t * rnd.uniform(4, 9) + i * j)
                        wx = x + 12 + i * (bw - 24) / cols; wy = top + 22 + j * 46
                        rect(c, wx, wy, wx + 14, wy + 20, fill(C(skia.ColorGetR(win_col), skia.ColorGetG(win_col), skia.ColorGetB(win_col), int(255 * on))))
        x += bw + rnd.uniform(4, 30)

def vignette(c, k=0.55):
    c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), rad(W / 2, H * 0.45, H * 0.75, [C(0, 0, 0, 0), C(0, 0, 0, 0), C(0, 0, 0, int(255 * k))], [0, 0.55, 1.0]))

def grade(c, col, mode=skia.BlendMode.kMultiply):
    p = fill(col); p.setBlendMode(mode); c.drawRect(skia.Rect.MakeLTRB(0, 0, W, H), p)

def smoke(c, x, y, t, scale=1.0, seed=0, col=(40, 40, 50)):
    rnd = random.Random(seed)
    for i in range(14):
        ph = (t * 0.25 + i / 14) % 1.0
        px = x + math.sin(i * 1.7 + t * 0.6) * 40 * scale + ph * 120 * scale
        py = y - ph * 520 * scale
        r = (40 + ph * 140) * scale * rnd.uniform(0.8, 1.2)
        c.drawCircle(px, py, r, glow(C(*col, int(170 * (1 - ph))), r * 0.35))

def fire_glow(c, x, y, r, t):
    k = 0.85 + 0.15 * math.sin(t * 13) * math.sin(t * 7.3)
    c.drawCircle(x, y, r * k, rad(x, y, r * k, [C(255, 140, 40, 150), C(255, 80, 20, 60), C(255, 60, 20, 0)]))

def rain(c, t, n=220, seed=3, ang=0.18, col=(170, 190, 255, 140), speed=2600):
    rnd = random.Random(seed)
    p = stroke(C(*col), 3)
    for i in range(n):
        x0 = rnd.uniform(-300, W + 300); y0 = rnd.uniform(0, H + 400)
        y = (y0 + t * speed * rnd.uniform(0.85, 1.15)) % (H + 400) - 200
        x = x0 + y * ang
        c.drawLine(x, y, x - ang * 60, y - 60, p)

def music_notes(c, pts, t, col=C(255, 214, 10)):
    f = skia.Font(None, 72)
    for i, (x, y, a) in enumerate(pts):
        p = fill(C(skia.ColorGetR(col), skia.ColorGetG(col), skia.ColorGetB(col), int(255 * a)))
        c.save(); c.translate(x, y); c.rotate(math.sin(t * 5 + i) * 15)
        c.drawCircle(0, 0, 16, p); c.drawRect(skia.Rect.MakeLTRB(10, -58, 16, 0), p)
        c.drawRect(skia.Rect.MakeLTRB(10, -58, 34, -46), p)
        c.restore()

# ---------- props
def door(c, x, y, w, h, open_k=0.0, col=C(150, 96, 58), knob=True, light=None):
    """Door frame at x..x+w, top y. open_k 0..1 swings toward viewer (shown as narrowing)."""
    rect(c, x - 22, y - 22, x + w + 22, y + h, fill(OUT))
    rect(c, x - 12, y - 12, x + w + 12, y + h, fill(C(220, 210, 196)))
    rect(c, x, y, x + w, y + h, fill(light if light is not None else C(14, 12, 18)))
    dw = w * (1 - 0.82 * ease(open_k))
    outlined_rect(c, x, y, x + dw, y + h, col, 8, 4)
    for py in (0.12, 0.55):
        outlined_rect(c, x + dw * 0.16, y + h * py, x + dw * 0.84, y + h * (py + 0.33), C(170, 112, 70), 5, 4)
    if knob and dw > 60:
        c.drawCircle(x + dw * 0.85, y + h * 0.52, 15, fill(OUT)); c.drawCircle(x + dw * 0.85, y + h * 0.52, 10, fill(C(230, 190, 80)))

def window_frame(c, x, y, w, h, draw_outside, t):
    c.save(); c.clipRect(skia.Rect.MakeLTRB(x, y, x + w, y + h)); draw_outside(c, t); c.restore()
    p = stroke(OUT, 26); c.drawRect(skia.Rect.MakeLTRB(x, y, x + w, y + h), p)
    p2 = stroke(C(236, 230, 220), 16); c.drawRect(skia.Rect.MakeLTRB(x, y, x + w, y + h), p2)
    c.drawLine(x + w / 2, y, x + w / 2, y + h, stroke(C(236, 230, 220), 12))
    c.drawLine(x, y + h / 2, x + w, y + h / 2, stroke(C(236, 230, 220), 12))

def can(c, x, y, s=1.0, rot=0, label="BEANS", col=C(200, 60, 50)):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    outlined_rect(c, -34, -88, 34, 0, C(190, 190, 200), 6, 6)
    rect(c, -31, -70, 31, -18, fill(col))
    f = skia.Font(_tf("Anton"), 22); tw = f.measureText(label)
    c.drawString(label, -tw / 2, -36, f, fill(C(255, 240, 220)))
    c.restore()

_TF = {}
def _tf(name):
    if name not in _TF:
        _TF[name] = skia.Typeface.MakeFromFile({"Anton": "fonts/Anton-Regular.ttf", "Lucky": "fonts/LuckiestGuy-Regular.ttf",
                                                 "Bangers": "fonts/Bangers-Regular.ttf"}[name])
    return _TF[name]

def font(name, size): return skia.Font(_tf(name), size)

def text_c(c, s, x, y, f, col, outline=None, ow=10):
    tw = f.measureText(s)
    if outline is not None:
        p = stroke(outline, ow); c.drawString(s, x - tw / 2, y, f, p)
    c.drawString(s, x - tw / 2, y, f, fill(col))
    return tw

def phone(c, x, y, s, t, screen="calls", buzz=0.0, vol=0.0):
    c.save(); c.translate(x + math.sin(t * 70) * 6 * buzz, y); c.scale(s, s); c.rotate(math.sin(t * 55) * 3 * buzz)
    outlined_rect(c, -110, -210, 110, 210, C(30, 30, 38), 10, 36)
    rrect(c, -94, -190, 94, 190, 24, fill(C(20, 24, 44)))
    if screen == "calls":
        c.drawCircle(0, -80, 44, fill(C(70, 200, 110)))
        hp = skia.Path(); hp.addRoundRect(skia.Rect.MakeLTRB(-22, -96, 22, -64), 14, 14); c.drawPath(hp, fill(C(255, 255, 255)))
        text_c(c, "47", 0, 40, font("Anton", 92), C(255, 255, 255))
        text_c(c, "MISSED CALLS", 0, 86, font("Anton", 30), C(255, 120, 120))
    elif screen == "music":
        rrect(c, -64, -150, 64, -22, 16, fill(C(254, 97, 0)))
        music_notes(c, [(-6, -60, 1.0)], t, C(255, 255, 255))
        text_c(c, "BISCUIT'S", 0, 30, font("Anton", 30), C(255, 255, 255))
        text_c(c, "FAVORITE SONG", 0, 66, font("Anton", 30), C(255, 214, 10))
        rrect(c, -70, 110, 70, 126, 8, fill(C(70, 70, 90)))
        rrect(c, -70, 110, -70 + 140 * vol, 126, 8, fill(C(80, 220, 120)))
        text_c(c, "VOLUME", 0, 160, font("Anton", 22), C(180, 180, 200))
    c.restore()

def heart(c, x, y, s, a=255, col=(240, 70, 100)):
    p = skia.Path(); p.moveTo(x, y + s * 0.35)
    p.cubicTo(x - s * 0.9, y - s * 0.3, x - s * 0.4, y - s * 0.9, x, y - s * 0.35)
    p.cubicTo(x + s * 0.4, y - s * 0.9, x + s * 0.9, y - s * 0.3, x, y + s * 0.35)
    c.drawPath(p, fill(C(*col, a)))

def plant(c, x, gy, grow, t, tomatoes=True, sway=1.0):
    """Tomato plant in a planter box; grow 0..1."""
    outlined_rect(c, x - 90, gy - 70, x + 90, gy, C(130, 84, 50), 7, 6)
    if grow <= 0: return
    h = 40 + 230 * grow
    sw = math.sin(t * 2.0 + x) * 10 * sway
    stem = skia.Path(); stem.moveTo(x, gy - 70); stem.cubicTo(x + sw * 0.3, gy - 70 - h * 0.4, x - sw * 0.2, gy - 70 - h * 0.7, x + sw, gy - 70 - h)
    c.drawPath(stem, stroke(C(40, 110, 50), 12))
    for i in range(int(2 + 5 * grow)):
        k = (i + 1) / (2 + 5 * grow); ly = gy - 70 - h * k; lx = x + sw * k
        side = -1 if i % 2 else 1
        lp = skia.Path(); lp.moveTo(lx, ly); lp.quadTo(lx + side * 60, ly - 40, lx + side * 90, ly - 6); lp.quadTo(lx + side * 50, ly + 10, lx, ly); lp.close()
        c.drawPath(lp, fill(C(60, 160, 70))); c.drawPath(lp, stroke(C(30, 90, 40), 4))
        if tomatoes and grow > 0.6 and i % 2 == 0:
            tr = 20 * clamp((grow - 0.6) / 0.4)
            c.drawCircle(lx + side * 40, ly + 24, tr + 4, fill(OUT)); c.drawCircle(lx + side * 40, ly + 24, tr, fill(C(230, 50, 40)))

def barrel(c, x, gy, fillk=0.7, rot=0):
    c.save(); c.translate(x, gy); c.rotate(rot)
    outlined_rect(c, -70, -190, 70, 0, C(60, 110, 170), 8, 18)
    rrect(c, -56, -170 + 160 * (1 - fillk), 56, -16, 10, fill(C(110, 170, 230)))
    for yy in (-150, -40): c.drawLine(-70, yy, 70, yy, stroke(OUT, 8))
    c.restore()

def shelf(c, x, y, w, h, seed, t=0, tremble=0):
    rnd = random.Random(seed)
    outlined_rect(c, x, y, x + w, y + h, C(190, 196, 206), 8, 4)
    rows = 4
    for r_ in range(rows):
        sy = y + h * (r_ + 1) / (rows + 0.3)
        c.drawLine(x + 6, sy, x + w - 6, sy, stroke(OUT, 9))
        px = x + 16
        while px < x + w - 50:
            bw = rnd.uniform(34, 62); bh = rnd.uniform(50, 100)
            col = rnd.choice([(230, 80, 70), (250, 190, 60), (80, 150, 230), (90, 190, 120), (240, 240, 240), (200, 110, 200)])
            j = math.sin(t * 50 + px) * tremble
            outlined_rect(c, px + j, sy - bh, px + bw + j, sy - 4, C(*col), 5, 4)
            px += bw + rnd.uniform(4, 10)

def speed_lines(c, t, k=1.0, col=(255, 255, 255)):
    rnd = random.Random(int(t * 30))
    for i in range(int(26 * k)):
        y = rnd.uniform(200, H - 200); x = rnd.uniform(-200, W)
        L = rnd.uniform(160, 420)
        c.drawLine(x, y, x + L, y, stroke(C(*col, int(rnd.uniform(40, 110) * k)), rnd.uniform(3, 7)))

def lightning(c, t0, t, seed):
    k = t - t0
    if k < 0 or k > 0.35: return 0
    a = (1 - k / 0.35)
    rnd = random.Random(seed)
    x = rnd.uniform(200, 880); y = -50
    p = skia.Path(); p.moveTo(x, y)
    while y < 900:
        x += rnd.uniform(-70, 70); y += rnd.uniform(40, 110); p.lineTo(x, y)
    c.drawPath(p, stroke(C(200, 220, 255, int(140 * a)), 30))
    c.drawPath(p, stroke(C(255, 255, 255, int(255 * a)), 9))
    return a
