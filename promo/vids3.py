# "Want to make stop-motion like this?" videos. Usage: python3 vids3.py <blocks|dominoes|all>
import sys, glob
WHICH3 = sys.argv[1] if len(sys.argv) > 1 else "all"
sys.argv = [sys.argv[0], "none"]
from vids import *  # helpers, assets, end card; scene_frames adds the Framey badge
import cool

CF = D + "/cool"; os.makedirs(CF, exist_ok=True)

def clip(name):
    fs = sorted(glob.glob(f"{CF}/{name}_*.jpg"))
    if not fs:
        fr = cool.blocks(FB) if name == "blocks" else cool.dominoes()
        for i, im in enumerate(fr): im.save(f"{CF}/{name}_{i:03d}.jpg", quality=90)
        del fr; fs = sorted(glob.glob(f"{CF}/{name}_*.jpg"))
    return fs

_cache = {}
def get(path, w, r=40):
    key = (path, w)
    if key not in _cache:
        if len(_cache) > 40: _cache.clear()
        f = Image.open(path).convert("RGB"); h = int(f.height * w / f.width)
        _cache[key] = rounded(f.resize((w, h), Image.LANCZOS), r)
    return _cache[key]

def want(name, hook):
    fs = clip(name); n = len(fs); T1 = n / 8 + 0.6
    L1 = text_layer(hook, 86)
    def a(t):  # the cool stop-motion, big
        im = bg(); f = get(fs[min(n - 1, int(t * 8))], 1000, 44)
        im.paste(f, ((W - f.width) // 2, 640), f); pop(im, L1, W / 2, 270, t)
        return im
    LB = text_layer([[("Make it with ", WHITE), ("Framey", OR)]], 92)
    def b(t):  # step 1: snap a photo in the app
        im = bg(); put_phone(im, A + "/a_shoot.png", 1180, W / 2, 620, t, 0.05)
        pop(im, LB, W / 2, 260, t); pop(im, text_layer([[("1. ", OR), ("Snap a photo", WHITE)]], 64), W / 2, 400, t, 0.25)
        for at in (0.9, 1.9): tap(im, W / 2, 620 + 16 + int(1180 * 0.915), t, at)
        return im
    LC = text_layer([[("2. ", OR), ("Move it a tiny bit", WHITE)]], 76)
    ks = [n // 9, n // 5, n * 2 // 7]
    def c(t):  # step 2: two photos next to each other
        im = bg(); pop(im, LC, W / 2, 300, t); k = ks[int(t * 1.1) % 3]
        w = 480; y = 760
        for j, x, txt, col in ((k, 40, f"Photo {k + 1}", GREY), (k + 1, W - 40 - w, f"Photo {k + 2}", OR)):
            f = get(fs[j], w, 30); im.paste(f, (x, y), f)
            d = ImageDraw.Draw(im); ft = font(FB, 44); tw = d.textlength(txt, font=ft); d.text((x + (w - tw) / 2, y + f.height + 26), txt, font=ft, fill=col)
        return im
    LD = text_layer([[("3. ", OR), ("Framey plays them fast", WHITE)]], 70)
    def dd(t):  # step 3: it's a movie
        im = bg(); f = get(fs[int(t * 8) % n], 1000, 44); im.paste(f, ((W - f.width) // 2, 640), f)
        pop(im, LD, W / 2, 300, t); pop(im, text_layer([[("= your own stop-motion movie!", GREY)]], 50), W / 2, 640 + f.height + 50, t, 0.4)
        return im
    build(f"want-{name}", [("a", T1, a), ("b", BEAT * 6, b), ("c", BEAT * 6, c), ("d", BEAT * 6, dd), END],
          clicks=(T1 + 0.9, T1 + 1.9))

if WHICH3 in ("blocks", "all"):
    want("blocks", [[("Want to make", WHITE)], [("stop-motion", OR), (" like this?", WHITE)]])
if WHICH3 in ("dominoes", "all"):
    want("dominoes", [[("Want to make", WHITE)], [("stop-motion", OR), (" like this?", WHITE)]])
