# Draws the stop-motion clip frames in a light process (no video assets loaded), so the
# video render that follows reuses them instead of drawing them itself. Usage: python3 precool.py name [name...]
import os, sys, glob, gc
D = os.environ.get("WORK", "/home/user/work"); CF = D + "/cool"; os.makedirs(CF, exist_ok=True)
import cool, cool2
for name in sys.argv[1:]:
    if glob.glob(f"{CF}/{name}_*.jpg"): print("have", name); continue
    fr = cool.blocks("/mnt/files/v/Inter.ttf") if name == "blocks" else cool.dominoes() if name == "dominoes" else getattr(cool2, name)()
    for i, im in enumerate(fr): im.save(f"{CF}/{name}_{i:03d}.jpg", quality=90)
    print("drew", name, len(fr)); del fr; gc.collect()
