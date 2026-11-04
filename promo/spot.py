# SPOT THE MISTAKE: a smooth looping animation with ONE wrong frame, shown twice, then revealed.
# Usage: python3 spot.py <variant> [--preview]   (variants in VARIANTS below)
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
        p = subprocess.Popen([FF, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-i", f"{OUT}/_spot_{name}.wav", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    shots = []
    for seg, k, n, t0 in frames:
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
        else: p.stdin.write(im.tobytes())
    if preview:
        sheet = Image.new("RGB", (270 * len(shots), 480))
        for i, s in enumerate(shots): sheet.paste(s, (270 * i, 0))
        sheet.save(f"{OUT}/spot_{name}_preview.jpg"); print("preview"); return
    p.stdin.close(); p.wait(); os.remove(f"{OUT}/_spot_{name}.wav"); print("spot", name, total / FPS, out)

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
