# Replaces the unknown-number voice with a robot/voice-changer take, synced to the existing bubble times
# (so the video doesn't need re-rendering). Writes unk48.wav (dry) — audio_unk.py applies the robot FX.
import wave, json
import numpy as np

SR = 48000
def read(p):
    w = wave.open(p); sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    return np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a)

BOT = read("bot.raw"); TURN = read("bot_turn.raw")
# transcript word spans per line (s)
LINES = {"U1": (0.1, 4.3), "U2": (4.8, 6.8), "U3": (7.5, 12.8), "U4": (12.9, 14.4), "U5": (14.8, 19.4), "U6": (20.2, 24.8),
         "U7": (25.2, 25.7), "U8": (26.1, 29.7), "U9": (30.0, 33.7), "U10": (33.9, 35.1), "U11": (35.7, 36.6),
         "U12": (36.9, 39.5), "U13": (39.8, 44.7)}

def env(x, win=0.02):
    n = int(win * SR); m = len(x) // n
    return np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1)), n

def silences(x, thr=0.006, min_len=0.08):
    e, n = env(x); quiet = e < thr; runs = []; i = 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) * n / SR >= min_len: runs.append(((i * n) / SR, (j * n) / SR))
            i = j
        else: i += 1
    return runs

SIL = silences(BOT)
def nearest_cut(t):
    best = min(SIL, key=lambda r: abs((r[0] + r[1]) / 2 - t)); return (best[0] + best[1]) / 2

ids = list(LINES)
cuts = {}
for i, k in enumerate(ids):
    a = 0.0 if i == 0 else cuts[ids[i - 1]][1]
    b = nearest_cut((LINES[k][1] + LINES[ids[i + 1]][0]) / 2) if i + 1 < len(ids) else min(len(BOT) / SR, LINES[k][1] + 0.4)
    cuts[k] = (a, b)

def trim(seg):
    e, n = env(seg); on = np.where(e > 0.01)[0]
    if len(on) == 0: return seg
    s = max(0, on[0] * n - int(0.03 * SR)); t = min(len(seg), (on[-1] + 1) * n + int(0.12 * SR))
    seg = seg[s:t].copy(); f = int(0.01 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f * 3:] *= np.linspace(1, 0, f * 3)
    return seg

SPLITS = {"U1": [1.9], "U3": [8.9, 11.5], "U4": [13.75], "U5": [15.75, 16.6], "U6": [23.4], "U8": [28.9], "U9": [32.3],
          "U10": [34.65], "U12": [38.55], "U13": [41.55, 42.65]}
def split_at(seg, off, times):
    e, n = env(seg); pts = [0]
    for t in times:
        c = int((t - off) * SR / n); lo, hi = max(0, c - 12), min(len(e), c + 13)
        pts.append((lo + int(np.argmin(e[lo:hi]))) * n + n // 2)
    pts.append(len(seg))
    return [trim(seg[pts[i]:pts[i + 1]]) for i in range(len(pts) - 1)]

def split(seg, parts):
    if parts <= 1: return [trim(seg)]
    runs = [r for r in silences(seg, 0.006, 0.12) if 0.2 < r[0] and r[1] < len(seg) / SR - 0.2]
    runs = sorted(sorted(runs, key=lambda r: r[0] - r[1])[: parts - 1])
    if len(runs) < parts - 1: return [trim(seg)]
    pts = [0] + [int((r[0] + r[1]) / 2 * SR) for r in runs] + [len(seg)]
    return [trim(seg[pts[i]:pts[i + 1]]) for i in range(parts)]

D = json.load(open("events.json")); EV = {e["id"]: e for e in D["events"]}
out = np.zeros(int(D["total"] * SR) + SR)
for k in ids + ["U14"]:
    seg = TURN if k == "U14" else BOT[int(cuts[k][0] * SR):int(cuts[k][1] * SR)]
    bubbles = EV[k]["bubbles"]
    chunks = split_at(seg, cuts[k][0], SPLITS[k]) if k in SPLITS else [trim(seg)]
    if len(chunks) == 1:
        at = [bubbles[0][0] + 0.25]
    else:
        at = [bubbles[0][0] + 0.25] + [bt + 0.05 for bt, _ in bubbles[1:]]
    last_end = 0
    for c, t in zip(chunks, at):
        t = max(t, last_end + 0.05); i = int(t * SR); out[i:i + len(c)] += c; last_end = t + len(c) / SR
    print(k, len(chunks), "chunks", round(cuts[k][0], 2) if k != "U14" else "", [round(len(c) / SR, 2) for c in chunks])
out = out[: int(D["total"] * SR)]
with wave.open("unk48.wav", "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
