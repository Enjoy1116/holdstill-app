# More Framey feature shorts. Usage: python3 vids2.py <green|music|how|create|all>
import sys
WHICH2 = sys.argv[1] if len(sys.argv) > 1 else "all"
sys.argv = [sys.argv[0], "none"]
from vids import *  # helpers, assets, scenes, end card (renders nothing with "none")

def loop(frames, t, fps=8):
    return frames[int(t * fps) % len(frames)]

def big(im, f, w=820, top=560, r=48):
    h = int(f.height * w / f.width); fr = rounded(f.resize((w, h), Image.LANCZOS), r)
    im.paste(fr, ((W - w) // 2, top), fr); return h

def label(im, txt, y, col=GREY, size=54, t=1, delay=0):
    pop(im, text_layer([[(txt, col)]], size), W / 2, y, t, delay)

# ---- green screen: what you film -> what you get
if WHICH2 in ("green", "all"):
    import gc; raw.clear(); (locked.clear() if hop is not locked else None); gc.collect()
    gj = json.load(open(A + "/green.json"))
    G = [dec(u) for u in gj["green"]]
    K = [dec(u) for u in gj["keyed"]]; del gj
    LG1 = text_layer([[("Green paper +", WHITE)], [("one tap =", OR)]], 104)
    def g1(t):
        im = bg(); h = big(im, loop(G, t)); pop(im, LG1, W / 2, 200, t); label(im, "What you film", 560 + h + 50, t=t, delay=0.3); return im
    LG2 = text_layer([[("Outer space", OR)], [("for your toys", WHITE)]], 104)
    def g2(t):
        im = bg(); h = big(im, loop(K, t)); pop(im, LG2, W / 2, 200, t); label(im, "What you get", 560 + h + 50, OR, t=t, delay=0.3); return im
    def g3(t):
        im = bg(); w = 450; y = 660
        a = rounded(loop(G, t).resize((w, int(G[0].height * w / G[0].width)), Image.LANCZOS), 36)
        b2 = rounded(loop(K, t).resize((w, int(K[0].height * w / K[0].width)), Image.LANCZOS), 36)
        im.paste(a, (70, y), a); im.paste(b2, (W - 70 - w, y), b2)
        d = ImageDraw.Draw(im); f = font(FB, 44)
        for x0, txt, col in ((70, "Before", GREY), (W - 70 - w, "After", OR)):
            tw = d.textlength(txt, font=f); d.text((x0 + (w - tw) / 2, y + a.height + 30), txt, font=f, fill=col)
        pop(im, text_layer([[("Framey's", WHITE)], [("green screen", OR)]], 104), W / 2, 200, t); return im
    build("green-screen", [("a", BEAT * 6, g1), ("b", BEAT * 6, g2), ("c", BEAT * 6, g3), END])

# ---- music: search a song, hear it with your movie
if WHICH2 in ("music", "all"):
    LM1 = text_layer([[("Every movie needs", WHITE)], [("a soundtrack", OR)]], 100)
    def m1(t):
        im = bg(); h = big(im, loop(hop, t)); pop(im, LM1, W / 2, 200, t); label(im, "Pick the perfect song", 560 + h + 50, OR, 54, t, 0.4); return im
    LM2 = text_layer([[("Search any song.", WHITE)], [("Hear it with your movie.", OR)]], 84)
    def m2(t):
        im = bg(); put_phone(im, A + "/song.png", 1240, W / 2, 560, t, 0.05); pop(im, LM2, W / 2, 200, t); return im
    build("music", [("a", BEAT * 6, m1), ("b", BEAT * 8, m2), END])

# ---- how stop-motion works: photos -> movie
if WHICH2 in ("how", "all"):
    LH1 = text_layer([[("How does", WHITE)], [("stop-motion work?", OR)]], 100)
    def h1(t):
        im = bg(); pop(im, LH1, W / 2, 200, t)
        n = min(len(hop), int(t / (BEAT * 8 / len(hop))) + 1); cw = 300; ch = int(hop[0].height * cw / hop[0].width)
        cols = 3; x0 = (W - cols * cw - (cols - 1) * 20) // 2; y0 = 520
        for i in range(min(n, 9)):
            f = rounded(hop[i].resize((cw, ch), Image.LANCZOS), 20)
            im.paste(f, (x0 + (i % cols) * (cw + 20), y0 + (i // cols) * (ch + 20)), f)
        label(im, f"{n} photos", y0 + 3 * (ch + 20) + 20, OR, 60, t, 0)
        return im
    LH2 = text_layer([[("Move it a tiny bit", WHITE)], [("between each photo", OR)]], 92)
    def h2(t):
        im = bg(); pop(im, LH2, W / 2, 200, t); w = 470; y = 640
        k = int(t * 2) % (len(hop) - 1)
        for j, x in ((k, 50), (k + 1, W - 50 - w)):
            f = rounded(hop[j].resize((w, int(hop[0].height * w / hop[0].width)), Image.LANCZOS), 30); im.paste(f, (x, y), f)
        d = ImageDraw.Draw(im); f2 = font(FB, 44)
        d.text((50, y + int(hop[0].height * w / hop[0].width) + 26), f"Photo {k + 1}", font=f2, fill=GREY)
        d.text((W - 50 - w, y + int(hop[0].height * w / hop[0].width) + 26), f"Photo {k + 2}", font=f2, fill=OR)
        return im
    LH3 = text_layer([[("Play them fast =", WHITE)], [("it moves!", OR)]], 104)
    def h3(t):
        im = bg(); h = big(im, loop(hop, t)); pop(im, LH3, W / 2, 200, t); label(im, "8 photos every second", 560 + h + 50, t=t, delay=0.3); return im
    build("how-it-works", [("a", BEAT * 8, h1), ("b", BEAT * 6, h2), ("c", BEAT * 6, h3), END])

# ---- create: titles + drawing
if WHICH2 in ("create", "all"):
    LC1 = text_layer([[("Add a title", WHITE)], [("in one tap", OR)]], 104)
    def c1(t):
        im = bg(); put_phone(im, A + "/c_title.png", 1240, W / 2, 560, t, 0.05); pop(im, LC1, W / 2, 190, t); return im
    LC2 = text_layer([[("Draw right on", WHITE)], [("your frames", OR)]], 104)
    def c2(t):
        im = bg(); put_phone(im, A + "/b_draw.png", 1240, W / 2, 560, t, 0.05); pop(im, LC2, W / 2, 190, t); return im
    build("titles-and-drawing", [("a", BEAT * 6, c1), ("b", BEAT * 6, c2), END])
