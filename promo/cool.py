# Short "made with Framey" style stop-motion clips, drawn frame by frame (8 photos a second).
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont

CW, CH, S = 960, 1280, 2          # clip size (3:4 like a phone photo); drawn at 2x then shrunk
TABLE = 760

_ROOM = []
def room():
    if not _ROOM:
        im = Image.new("RGBA", (CW * S, CH * S)); _room(ImageDraw.Draw(im), None); _ROOM.append(im)
    return _ROOM[0].copy()
def _room(d, rnd):
    w, h = CW * S, CH * S
    for y in range(0, TABLE * S, 8):  # warm wall
        c = 233 - int(18 * y / (TABLE * S)); d.rectangle([0, y, w, y + 8], fill=(c, c - 13, c - 34))
    for i in range(0, w, 240 * S // 2): d.rectangle([i, 0, i + 6, TABLE * S], fill=(215, 200, 175))
    for y in range(TABLE * S, h, 8):  # wooden table
        k = (y - TABLE * S) / (h - TABLE * S); d.rectangle([0, y, w, y + 8], fill=(int(166 - 44 * k), int(106 - 32 * k), int(60 - 20 * k)))
    for i in range(6):
        y0 = (TABLE + 60 + i * 80) * S
        d.line([(0, y0), (w // 3, y0 - 20 * S), (2 * w // 3, y0 + 30 * S), (w, y0 - 5 * S)], fill=(120, 72, 38), width=3 * S)

def _shadow(base, cx, cy, rx, ry, a=90):
    m = int(30 * S); w, h = int(2 * rx + 2 * m), int(2 * ry + 2 * m)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([m, m, w - m, h - m], fill=(40, 20, 5, a))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10 * S)), (int(cx - rx - m), int(cy - ry - m)))

def _ball(d, cx, cy, r, sq=1.0, look=0):
    rx, ry = r / math.sqrt(sq), r * sq
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(232, 82, 8))
    d.ellipse([cx - rx * 0.75, cy - ry * 0.85, cx + rx * 0.2, cy - ry * 0.05], fill=(255, 140, 70))  # clay shine
    d.ellipse([cx - rx * 0.6, cy - ry * 0.55, cx + rx * 0.05, cy - ry * 0.15], fill=(246, 106, 32))
    for ex in (-0.32, 0.32):
        x = cx + ex * rx; y = cy - 0.2 * ry
        d.ellipse([x - 0.23 * r, y - 0.23 * r, x + 0.23 * r, y + 0.23 * r], fill=(255, 255, 255))
        d.ellipse([x - 0.1 * r + look * 0.08 * r, y - 0.1 * r, x + 0.1 * r + look * 0.08 * r, y + 0.1 * r], fill=(17, 17, 17))
    d.arc([cx - 0.3 * rx, cy + 0.0 * ry, cx + 0.3 * rx, cy + 0.42 * ry], 15, 165, fill=(90, 30, 0), width=int(0.08 * r))

CROP = (0, 330 * S, CW * S, 1090 * S)  # frame the scene closer
def _finish(im, k, rnd):
    im = im.convert("RGB").crop(CROP).resize((CW, (CROP[3] - CROP[1]) // S), Image.LANCZOS)
    return ImageEnhance.Brightness(im).enhance(1 + rnd.uniform(-0.025, 0.025))  # tiny light flicker, like real stop-motion

COLORS = [(240, 90, 20), (52, 110, 222), (250, 196, 40), (46, 170, 96), (236, 84, 140), (128, 84, 214)]

def blocks(font_path):
    """Six blocks hop in one by one and spell FRAMEY, then the clay ball hops along the top."""
    rnd = random.Random(3); frames = []
    bw = 138 * S; gap = 8 * S; x0 = (CW * S - (6 * bw + 5 * gap)) // 2; top = TABLE * S + 40 * S - bw
    f = ImageFont.truetype(font_path, 96 * S)
    try: f.set_variation_by_axes([32, 800])
    except Exception: pass
    letters = "FRAMEY"; IN = 4  # frames per block
    ball_start = 6 * IN + 2; n = ball_start + 6 * 3 + 12
    for k in range(n):
        im = room(); d = ImageDraw.Draw(im)
        for i in range(6):
            a = k - i * IN
            if a < 0: continue
            tx = x0 + i * (bw + gap); y = top
            if a < IN:  # hopping in from the right
                p = (a + 1) / IN; x = tx + (1 - p) * (CW * S - tx + 60 * S); y = top - math.sin(p * math.pi) * 150 * S
            else: x = tx
            wave = 0
            bk = k - (ball_start + 6 * 3 + 2)  # end: blocks bounce in a wave
            if bk >= 0 and 0 <= bk - i < 3: wave = [40, 70, 25][bk - i] * S
            y -= wave; jx = rnd.uniform(-2, 2) * S; jy = rnd.uniform(-1.5, 1.5) * S
            _shadow(im, x + bw / 2, TABLE * S + 42 * S, bw * 0.62, 16 * S, 70); d = ImageDraw.Draw(im)
            c = COLORS[i]; dk = tuple(int(v * 0.72) for v in c)
            d.rounded_rectangle([x + jx, y + jy + 14 * S, x + bw + jx, y + bw + jy], 14 * S, fill=dk)
            d.rounded_rectangle([x + jx, y + jy, x + bw + jx, y + bw - 12 * S + jy], 14 * S, fill=c)
            tw = d.textlength(letters[i], font=f); d.text((x + jx + (bw - tw) / 2, y + jy + 4 * S), letters[i], font=f, fill=(255, 255, 255))
        b = k - ball_start  # the ball hops block to block
        if b >= 0:
            r = 62 * S
            cxs = lambda s: x0 + s * (bw + gap) + bw / 2
            gy = lambda s: (TABLE * S + 40 * S) if s < 0 else top
            if b < 18:
                s = b // 3; ph = (b % 3) / 3
                cx = cxs(s - 1) + (cxs(s) - cxs(s - 1)) * ph; g0 = gy(s - 1) + (gy(s) - gy(s - 1)) * ph
                hop = math.sin(ph * math.pi) * 160 * S; sq = 0.8 if ph == 0 else 1.06
            else:
                e = b - 18; cx = cxs(5); g0 = top; hop = [0, 120, 160, 120, 0, 0][min(e, 5)] * S if e < 6 else 0
                sq = [0.75, 1.1, 1.08, 1.1, 0.78, 1.0][min(e, 5)] if e < 6 else 1.0
            if g0 == top: _shadow(im, cx, top + 6 * S, r * 0.8, 10 * S, 55)
            else: _shadow(im, cx, g0 + 2 * S, r * 0.85, 12 * S, 60)
            d = ImageDraw.Draw(im)
            _ball(d, cx, g0 - hop - r * sq + 6 * S, r, sq, look=1)
        frames.append(_finish(im, k, rnd))
    return frames

def dominoes():
    """A line of dominoes falls, the last one bumps the ball, which bounces away happy."""
    rnd = random.Random(5); frames = []
    N = 9; dw, dh = 34 * S, 210 * S; sp = 72 * S; x0 = 40 * S; base = TABLE * S + 70 * S
    fall_at = [2 + i * 2 for i in range(N)]
    n = fall_at[-1] + 4 + 16
    for k in range(n):
        im = room(); d = ImageDraw.Draw(im)
        for i in range(N):
            a = (k - fall_at[i]) / 3; a = max(0, min(1, a))
            ang = a * (72 if i < N - 1 else 80) * math.pi / 180
            px = x0 + i * sp + dw; py = base  # pivot: bottom-right corner
            pts = [(-dw, 0), (0, 0), (0, -dh), (-dw, -dh)]
            rot = [(px + x * math.cos(ang) - y * math.sin(ang) * -1 * -1, py + x * math.sin(ang) + y * math.cos(ang)) for x, y in pts]
            rot = [(px + (x * math.cos(ang) - y * math.sin(ang)), py + (x * math.sin(ang) + y * math.cos(ang))) for x, y in pts]
            j = rnd.uniform(-1.5, 1.5) * S; rot = [(x + j, y) for x, y in rot]
            c = COLORS[i % 6]
            _shadow(im, px - dw / 2 + math.sin(ang) * dh / 2, base + 4 * S, dw + math.sin(ang) * dh / 2, 10 * S, 60); d = ImageDraw.Draw(im)
            d.polygon(rot, fill=c); d.line(rot + [rot[0]], fill=tuple(int(v * 0.7) for v in c), width=3 * S)
            mx = sum(x for x, _ in rot) / 4; my = sum(y for _, y in rot) / 4; d.ellipse([mx - 7 * S, my - 7 * S, mx + 7 * S, my + 7 * S], fill=(255, 255, 255))
        # the ball waits at the end of the line, gets bumped, and bounces off to the right
        r = 66 * S; bx0 = x0 + (N - 1) * sp + dw + 140 * S; hit = fall_at[-1] + 2; b = k - hit
        if b < 0: cx, hy, sq, look = bx0, 0, 1.0, -1
        else:
            ph = (b % 4) / 4; amp = 260 * S * (0.7 ** (b // 4)) if b < 12 else 0
            cx = bx0 + min(b, 4) * 12 * S; hy = math.sin(ph * math.pi) * amp; sq = 0.74 if ph == 0 and b < 12 else 1.06 if b < 12 else 1.0; look = 1
        _shadow(im, cx, base + 4 * S, r * 0.85, 13 * S, 70); d = ImageDraw.Draw(im)
        _ball(d, cx, base - hy - r * sq + 6 * S, r, sq, look)
        frames.append(_finish(im, k, rnd))
    return frames

if __name__ == "__main__":
    import sys
    fp = sys.argv[1]; out = sys.argv[2]
    for name, fr in (("blocks", blocks(fp)), ("dominoes", dominoes())):
        for i, im in enumerate(fr): im.save(f"{out}/{name}_{i:03d}.jpg", quality=88)
        print(name, len(fr))
