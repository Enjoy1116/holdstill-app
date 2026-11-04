# More "Want to make stop-motion like this?" scenes, drawn frame by frame (8 photos a second).
# Each scene takes only=None (all frames) or a list of frame numbers (quick preview).
import math, random
from PIL import ImageDraw
from cool import room, _shadow, _ball, _finish, COLORS, TABLE, S, CW

G = (TABLE + 50) * S          # where things stand on the table
MID = CW * S // 2


def _dk(c, f=0.72):
    return tuple(int(v * f) for v in c)


def _put_ball(im, cx, ground, r, hop=0, sq=1.0, look=0):
    k = 1 - min(hop / (700 * S), 0.5)
    _shadow(im, cx, ground + 3 * S, r * 0.85 * k, 12 * S * k, int(65 * k))
    _ball(ImageDraw.Draw(im), cx, ground - hop - r * sq + 6 * S, r, sq, look)


def _run(n, draw, seed, only):
    rnd = random.Random(seed); frames = []
    for k in range(n):
        if only is not None and k not in only:
            continue
        im = room(); draw(im, k, rnd); frames.append(_finish(im, k, rnd))
    return frames


# ---------------------------------------------------------------- 1. stacking cups
def stack(only=None):
    """Five cups drop in one by one and stack into a tower, then the clay ball climbs to the top."""
    widths = [300, 250, 205, 165, 130]; hgt = 72 * S; IN = 4
    k0 = len(widths) * IN + 2                      # ball starts
    n = k0 + 3 + 6 + 10

    def draw(im, k, rnd):
        _shadow(im, MID, G + 3 * S, 175 * S, 14 * S, 70)
        d = ImageDraw.Draw(im); y = G; top = G
        for i, w in enumerate(widths):
            a = k - i * IN
            if a < 0: break
            w *= S
            if a < IN - 1: p = (a + 1) / (IN - 1); off = (1 - p) ** 2 * 750 * S; sq = 1.0
            else: off = 0; sq = 0.8 if a == IN - 1 else 1.0
            h = hgt * sq; jx = rnd.uniform(-2, 2) * S; c = COLORS[i]
            x0, x1, yb = MID - w / 2 + jx, MID + w / 2 + jx, y - off
            d.rounded_rectangle([x0, yb - h, x1, yb], 12 * S, fill=_dk(c))
            d.rounded_rectangle([x0, yb - h, x1, yb - 12 * S], 12 * S, fill=c)
            d.rectangle([x0 + 10 * S, yb - h * 0.62, x1 - 10 * S, yb - h * 0.5], fill=(255, 255, 255))
            if off == 0: y -= hgt; top = y
        b = k - k0; r = 58 * S; sx = MID + 330 * S
        if b < 0: _put_ball(im, sx, G, r, look=-1)
        elif b < 3: _put_ball(im, sx, G, r, [70, 0, 70][b] * S, [1.08, 0.78, 1.08][b], -1)
        elif b < 9:
            p = (b - 2) / 6; cx = sx + (MID - sx) * p; g = G + (top - G) * p
            _put_ball(im, cx, g, r, math.sin(p * math.pi) * 260 * S, 1.06, -1)
        else:
            e = b - 9
            hop = [0, 90, 130, 90, 0, 0, 60, 0, 0, 0][min(e, 9)] * S
            sq = [0.72, 1.08, 1.1, 1.08, 0.8, 1.0, 1.06, 0.85, 1.0, 1.0][min(e, 9)]
            _put_ball(im, MID, top, r, hop, sq, 1 if e > 4 else 0)
    return _run(n, draw, 11, only)


# ---------------------------------------------------------------- 2. toy car race
def _car(im, x, ground, c, sc, spin, jy):
    W_, H_, wr = 300 * S * sc, 92 * S * sc, 34 * S * sc
    _shadow(im, x + W_ / 2, ground + 3 * S, W_ * 0.55, 13 * S * sc, 70)
    d = ImageDraw.Draw(im); yb = ground - wr * 0.9 + jy
    d.rounded_rectangle([x + W_ * 0.22, yb - H_ - 70 * S * sc, x + W_ * 0.72, yb - H_ + 10 * S], 22 * S * sc, fill=_dk(c, 0.85))
    d.rounded_rectangle([x + W_ * 0.27, yb - H_ - 56 * S * sc, x + W_ * 0.67, yb - H_ + 2 * S], 14 * S * sc, fill=(170, 215, 245))
    d.rounded_rectangle([x, yb - H_, x + W_, yb], 26 * S * sc, fill=c)
    d.rectangle([x + 12 * S, yb - H_ * 0.55, x + W_ - 12 * S, yb - H_ * 0.42], fill=(255, 255, 255))
    d.ellipse([x + W_ - 26 * S * sc, yb - H_ * 0.8, x + W_ - 8 * S * sc, yb - H_ * 0.62], fill=(255, 236, 140))
    for wx in (x + W_ * 0.22, x + W_ * 0.78):
        wy = ground - wr + jy
        d.ellipse([wx - wr, wy - wr, wx + wr, wy + wr], fill=(34, 34, 38))
        d.ellipse([wx - wr * 0.5, wy - wr * 0.5, wx + wr * 0.5, wy + wr * 0.5], fill=(200, 200, 205))
        for q in (0, math.pi / 2):
            a = spin + q
            d.line([(wx - math.cos(a) * wr * 0.5, wy - math.sin(a) * wr * 0.5), (wx + math.cos(a) * wr * 0.5, wy + math.sin(a) * wr * 0.5)], fill=(90, 90, 96), width=int(5 * S * sc))


def race(only=None):
    """Two toy cars race to a checkered finish line; the clay ball cheers the winner."""
    N = 26; n = N + 12; FIN = 770 * S
    back, front = G - 40 * S, G + 45 * S

    def pos(k):
        t = min(k, N - 1) / (N - 1)
        return (-320 + 800 * (1 - (1 - t) ** 2)) * S, (-700 + 1200 * t ** 1.4) * S

    def draw(im, k, rnd):
        d = ImageDraw.Draw(im); sq = 22 * S
        for row in range(6):                       # finish line on the table
            for col in range(2):
                y0 = back - 70 * S + row * sq * 1.15
                d.rectangle([FIN + col * sq, y0, FIN + (col + 1) * sq, y0 + sq * 1.15], fill=(250, 250, 250) if (row + col) % 2 else (25, 25, 25))
        bx, rx = pos(k); pbx, prx = pos(k - 1) if k else (bx, rx)
        won = k >= N
        r = 46 * S; e = k - N                     # ball behind the finish line
        hop = (math.sin((e % 4) / 4 * math.pi) * 150 * S) if won and e < 12 else 0
        _put_ball(im, 905 * S, back - 20 * S, r, hop, 0.78 if won and e % 4 == 0 else 1.0, -1 if not won else 0)
        for x, px, g, c, sc in ((bx, pbx, back, COLORS[1], 0.85), (rx, prx, front, COLORS[0], 1.0)):
            dx = x - px
            if dx > 30 * S:                        # speed lines
                d = ImageDraw.Draw(im)
                for j in range(3):
                    yy = g - (40 + j * 30) * S * sc
                    d.line([(x - 30 * S - dx * 0.8, yy), (x - 20 * S, yy)], fill=(255, 255, 255), width=int(5 * S))
            _car(im, x, g, c, sc, x / (34 * S * sc), rnd.uniform(-2, 2) * S if dx > 0 else 0)
    return _run(n, draw, 7, only)


# ---------------------------------------------------------------- 3. the ball splits in three
def split(only=None):
    """The clay ball bounces, squishes flat, and pops into three little balls that bounce in a wave."""
    n = 31; R = 66 * S; r = 42 * S; xs = [240 * S, MID, 720 * S]

    def draw(im, k, rnd):
        if k < 8:
            ph = (k % 4) / 4; cx = 300 * S + (MID - 300 * S) * k / 7
            _put_ball(im, cx, G, R, math.sin(ph * math.pi) * 230 * S, 0.75 if ph == 0 else 1.06, 1)
        elif k < 10:
            _put_ball(im, MID, G, R, 0, [0.6, 0.45][k - 8], 0)
        elif k < 15:
            p = (k - 9) / 5
            for i, tx in enumerate(xs):
                _put_ball(im, MID + (tx - MID) * p, G, r * (0.8 + 0.2 * p), math.sin(p * math.pi) * (300 if i == 1 else 230) * S, 1.0, i - 1)
        else:
            e = k - 15
            for i, tx in enumerate(xs):
                q = (e - 2 * i) % 8
                hop = math.sin(q / 4 * math.pi) * 150 * S if q < 4 else 0
                sq = 0.78 if q in (0, 4) and e >= 2 * i else 1.06 if q < 4 else 1.0
                _put_ball(im, tx + rnd.uniform(-1.5, 1.5) * S, G, r, hop, sq, 1 - i)
    return _run(n, draw, 13, only)


# ---------------------------------------------------------------- 4. rocket launch
def rocket(only=None):
    """The clay ball hops into a paper rocket, it shakes, puffs smoke, and blasts off."""
    n = 34; W_, H_ = 150 * S, 330 * S; cx = 600 * S; win = (cx, G - 225 * S)
    K_IN, K_SHAKE, K_UP = 12, 13, 18

    def draw(im, k, rnd):
        up = ((k - K_UP + 1) ** 2) * 28 * S if k >= K_UP else 0
        jx = rnd.uniform(-7, 7) * S if K_SHAKE <= k < K_UP + 3 else 0
        if k >= K_SHAKE:                           # smoke puffs at the base
            d = ImageDraw.Draw(im); s = k - K_SHAKE
            for j in range(7):
                age = s - j * 0.6
                if age <= 0: continue
                rr = min(age, 8) * 14 * S * (1 if j % 2 else 0.8)
                ox = (j - 3) * 55 * S * (1 + age * 0.12); oy = -min(age, 8) * 6 * S
                g = 235 - min(int(age * 4), 40)
                d.ellipse([cx + ox - rr, G + oy - rr * 0.8, cx + ox + rr, G + oy + rr * 0.8], fill=(g, g, g))
        if up < 900 * S:
            x0 = cx - W_ / 2 + jx; yb = G - 10 * S - up
            if k >= K_SHAKE and up < 700 * S:      # flames
                d = ImageDraw.Draw(im); fl = rnd.uniform(0.8, 1.25) * (90 + min(up / S, 200) * 0.6) * S
                d.polygon([(cx - 48 * S + jx, yb), (cx + 48 * S + jx, yb), (cx + jx, yb + fl)], fill=(255, 150, 30))
                d.polygon([(cx - 24 * S + jx, yb), (cx + 24 * S + jx, yb), (cx + jx, yb + fl * 0.6)], fill=(255, 230, 90))
            if up == 0: _shadow(im, cx, G + 3 * S, 120 * S, 14 * S, 70)
            d = ImageDraw.Draw(im); red = (226, 58, 48)
            d.polygon([(x0 - 55 * S, yb), (x0 + 10 * S, yb), (x0 + 10 * S, yb - 120 * S)], fill=red)
            d.polygon([(x0 + W_ + 55 * S, yb), (x0 + W_ - 10 * S, yb), (x0 + W_ - 10 * S, yb - 120 * S)], fill=red)
            d.rounded_rectangle([x0, yb - H_, x0 + W_, yb], 18 * S, fill=(244, 242, 236))
            d.rectangle([x0, yb - 70 * S, x0 + W_, yb - 50 * S], fill=red)
            d.polygon([(x0, yb - H_ + 10 * S), (x0 + W_, yb - H_ + 10 * S), (x0 + W_ / 2, yb - H_ - 130 * S)], fill=red)
            wx, wy = win[0] + jx, win[1] - up
            d.ellipse([wx - 58 * S, wy - 58 * S, wx + 58 * S, wy + 58 * S], fill=(120, 120, 130))
            d.ellipse([wx - 48 * S, wy - 48 * S, wx + 48 * S, wy + 48 * S], fill=(170, 215, 245))
            if k >= K_IN: _ball(d, wx, wy, 34 * S, 1.0, 0)
        if k < K_IN:                               # ball hops over and dives in the window
            p = k / K_IN; bx = 150 * S + (cx - 150 * S) * p
            if k < 8:
                ph = (k % 4) / 4; _put_ball(im, bx, G, 58 * S, math.sin(ph * math.pi) * 180 * S, 0.78 if ph == 0 else 1.06, 1)
            else:
                q = (k - 7) / 5; _put_ball(im, bx, G + (win[1] + 40 * S - G) * q, 58 * S - 20 * S * q, math.sin(q * math.pi) * 200 * S, 1.06, 1)
    return _run(n, draw, 17, only)


SCENES = ["stack", "race", "split", "rocket"]
