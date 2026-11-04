# Splits one narration WAV (all lines of an episode read in order, with pauses between them)
# into one WAV per shot, cutting at the longest pauses.
# Usage: python3 splitvoice.py <narration.wav> <episode> <number_of_lines> <out_dir>
import sys, os, wave
import numpy as np

src, name, n, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
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
        if i > 0 and j < m: runs.append((j - i, i, j))
        i = j
    else: i += 1
cuts = sorted(sorted(runs, reverse=True)[: n - 1], key=lambda r: r[1])
if len(cuts) < n - 1: raise SystemExit(f"found only {len(cuts) + 1} lines, expected {n}")
bounds = [0] + [(s + e) // 2 * win for _, s, e in cuts] + [len(a)]
os.makedirs(out, exist_ok=True)
for k in range(n):
    seg = a[bounds[k]: bounds[k + 1]]; r2 = np.sqrt(np.convolve(seg ** 2, np.ones(win) / win, "same"))
    loud = np.where(r2 > thr)[0]
    if len(loud): seg = seg[max(0, loud[0] - win * 2): loud[-1] + win * 4]
    with wave.open(f"{out}/{name}_{k}.wav", "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr); o.writeframes((np.clip(seg, -1, 1) * 32767).astype(np.int16).tobytes())
    print(f"{name}_{k}.wav {len(seg) / sr:.2f}s")
