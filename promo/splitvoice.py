# Splits one narration WAV (all lines of an episode read in order, with pauses between them)
# into one WAV per shot. Picks the n-1 cut points among the pauses so that each piece's length
# matches its line's text length (dynamic programming), favouring long pauses.
# Usage: python3 splitvoice.py <narration.wav> <episode> <number_of_lines> <out_dir> [stick.json]
import sys, os, wave, json
import numpy as np

src, name, n, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
sj = sys.argv[5] if len(sys.argv) > 5 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "stick.json")
with wave.open(src) as w:
    sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
win = int(0.02 * sr); m = len(a) // win
rms = np.sqrt((a[: m * win].reshape(m, win) ** 2).mean(1))
thr = max(0.008, np.percentile(rms, 30) * 0.6)
quiet = rms < thr
runs, i = [], 0
while i < m:
    if quiet[i]:
        j = i
        while j < m and quiet[j]: j += 1
        if i > 0 and j < m and j - i >= 6: runs.append(((i + j) // 2, j - i))
        i = j
    else: i += 1
if len(runs) < n - 1: raise SystemExit(f"found only {len(runs) + 1} pieces, expected {n}")
try:
    lines = [s["say"] for s in json.load(open(sj))[name]["shots"]][:n]
    wts = np.array([len(x) + 8 for x in lines], float)
except Exception:
    lines = [""] * n; wts = np.ones(n)
voiced = np.where(~quiet)[0]; v0, v1 = voiced[0], voiced[-1]
exp = v0 + (v1 - v0) * np.cumsum(wts)[:-1] / wts.sum()
span = (v1 - v0) / n; W_POS = float(os.environ.get('W_POS', '15'))
R = len(runs); pos = np.array([r[0] for r in runs], float); ln = np.array([r[1] for r in runs], float)
def cost(k, r): return ((pos[r] - exp[k]) / span) ** 2 * W_POS - np.log(ln[r])
INF = 1e18; D = np.full((n - 1, R), INF); B = np.zeros((n - 1, R), int)
for r in range(R): D[0, r] = cost(0, r)
for k in range(1, n - 1):
    best, bi = INF, -1
    for r in range(R):
        if r - 1 >= 0 and D[k - 1, r - 1] < best: best, bi = D[k - 1, r - 1], r - 1
        if bi >= 0: D[k, r] = best + cost(k, r); B[k, r] = bi
r = int(np.argmin(D[n - 2])); cuts = [r]
for k in range(n - 2, 0, -1): r = B[k, r]; cuts.append(r)
cuts = sorted(cuts)
sl = np.sort(ln)[::-1]
if R >= n and sl[n - 2] >= 1.2 * sl[n - 1]:
    cuts = sorted(np.argsort(-ln)[: n - 1])
bounds = [0] + [int(pos[c]) * win for c in cuts] + [len(a)]
os.makedirs(out, exist_ok=True)
for k in range(n):
    seg = a[bounds[k]: bounds[k + 1]]; r2 = np.sqrt(np.convolve(seg ** 2, np.ones(win) / win, "same"))
    loud = np.where(r2 > thr)[0]
    if len(loud): seg = seg[max(0, loud[0] - win * 2): loud[-1] + win * 4]
    with wave.open(f"{out}/{name}_{k}.wav", "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((np.clip(seg, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"{name}_{k}.wav {len(seg) / sr:.2f}s  {lines[k][:40]}")
