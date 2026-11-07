# Soundtrack for "I Survived 100 Days": narration + music + sound effects, mixed to 48 kHz.
import wave, math
import numpy as np

SR = 48000
DUR = 109.8
N = int(DUR * SR)
rng = np.random.default_rng(7)

def tt(d): return np.arange(int(d * SR)) / SR

def env(n, a=0.005, r=0.2):
    e = np.ones(n); ka = max(1, int(a * SR)); kr = max(1, int(r * SR))
    e[:ka] = np.linspace(0, 1, ka); e[-kr:] *= np.linspace(1, 0, kr); return e

def lp(x, k):
    """one-pole low pass, k in 0..1 (smaller = darker)"""
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += k * (x[i] - acc); y[i] = acc
    return y

def lp_fast(x, width):
    w = max(1, int(width)); return np.convolve(x, np.ones(w) / w, mode="same")

def place(buf, at, sig, gain=1.0):
    i = int(at * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig)); buf[i:j] += sig[: j - i] * gain

def noise(d): return rng.uniform(-1, 1, int(d * SR))

# ---------- instruments
def kick(d=0.45):
    t = tt(d); f = 45 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)

def snare(d=0.25):
    t = tt(d); return (noise(d) * 0.7 + np.sin(2 * np.pi * 190 * t) * 0.4) * np.exp(-t * 18)

def hat(d=0.06):
    n = noise(d); n = n - lp_fast(n, 6); return n * np.exp(-tt(d) * 60)

def pad(freqs, d, bright=0.3):
    t = tt(d); s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.4, 0.0, 0.4):
            s += np.sin(2 * np.pi * (f + det) * t + rng.uniform(0, 6))
            s += bright * 0.3 * np.sin(2 * np.pi * 2 * (f + det) * t)
    return s / (len(freqs) * 3) * env(len(t), 0.8, 1.0)

def bass_note(f, d):
    t = tt(d); s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.exp(-t * 2.5)

def pluck(f, d=0.5):
    t = tt(d); s = np.sign(np.sin(2 * np.pi * f * t)) * 0.3 + np.sin(2 * np.pi * f * t)
    return lp_fast(s, 4) * np.exp(-t * 7)

def note(n): return 440 * 2 ** ((n - 69) / 12)

# ---------- sfx
def whoosh(d=0.45):
    n = noise(d); t = tt(d)
    return lp_fast(n, 18) * np.sin(np.pi * t / d) ** 2 * 1.6

def impact(d=1.2):
    t = tt(d); return (np.sin(2 * np.pi * (38 + 60 * np.exp(-t * 9)) * t) * 1.0 + lp_fast(noise(d), 30) * 0.6) * np.exp(-t * 3.5)

def riser(d):
    t = tt(d); f = 200 + 1600 * (t / d) ** 2
    return (lp_fast(noise(d), 8) * 0.5 + 0.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * (t / d) ** 2

def buzz(d=0.9):
    t = tt(d); s = np.sign(np.sin(2 * np.pi * 150 * t)) * (np.sin(2 * np.pi * 14 * t) > 0)
    return lp_fast(s, 6) * 0.5 * env(len(t), 0.01, 0.05)

def thud(d=0.5):
    t = tt(d); return (np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 20)) * t) + lp_fast(noise(d), 40) * 0.8) * np.exp(-t * 9)

def scratch(d=0.35):
    n = noise(d); n = n - lp_fast(n, 3); t = tt(d)
    return n * 0.35 * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t)) * env(len(t), 0.02, 0.1)

def creak(d=1.2):
    t = tt(d); f = 260 + 90 * np.sin(2 * np.pi * 1.3 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (np.sin(2 * np.pi * 37 * t) > -0.2)
    return lp_fast(s, 10) * 0.25 * env(len(t), 0.1, 0.3)

def bark():
    d = 0.22; t = tt(d); f = 520 * np.exp(-t * 4) + 180
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.6 * np.sin(2 * np.pi * np.cumsum(f * 2.02) / SR) + lp_fast(noise(d), 4) * 0.5
    return np.tanh(2.2 * s) * np.exp(-t * 11) * 0.7

def clang(d=1.6):
    t = tt(d); s = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((523, 1), (1247, 0.6), (1893, 0.45), (2780, 0.3), (3911, 0.2)))
    return s / 2.5 * np.exp(-t * 3.2) + noise(d) * 0.3 * np.exp(-t * 40)

def groan(d=1.6, f0=95):
    t = tt(d); f = f0 + 12 * np.sin(2 * np.pi * 0.7 * t)
    src = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.6 + lp_fast(noise(d), 3) * 0.3
    s = lp_fast(src, 14) * env(len(t), 0.25, 0.6)
    return s * 0.6

def heartbeat():
    t = tt(0.25); b = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 18)
    out = np.zeros(int(0.9 * SR)); out[: len(b)] += b; out[int(0.22 * SR): int(0.22 * SR) + len(b)] += 0.7 * b
    return out

def thunder(d=2.4):
    t = tt(d); n = lp_fast(noise(d), 60) * 3
    return n * (np.exp(-t * 1.6) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t))) + impact(d) * 0.5

def rain(d):
    n = noise(d); return (n - lp_fast(n, 4)) * 0.12 + lp_fast(n, 40) * 0.25

def tune(d, start_note=72):
    """Biscuit's favourite song: a bouncy 8-bit melody."""
    mel = [0, 4, 7, 12, 7, 4, 9, 7, 5, 4, 2, 4, 7, 4, 0, -1]
    out = np.zeros(int(d * SR)); step = 0.16
    for i in range(int(d / step)):
        f = note(start_note + mel[i % len(mel)]); t = tt(step)
        s = np.sign(np.sin(2 * np.pi * f * t)) * 0.25 * np.exp(-t * 6)
        place(out, i * step, s)
        if i % 2 == 0: place(out, i * step, np.sin(2 * np.pi * f / 2 * tt(0.3)) * 0.3 * np.exp(-tt(0.3) * 6))
    return out

# ---------- build music bed
music = np.zeros(N); sfx = np.zeros(N)

def section_pad(a, b, chord, gain, bright=0.3):
    place(music, a, pad([note(n) for n in chord], b - a, bright), gain)

def beat(a, b, bpm, gain=1.0, hats=True, snares=True, bass=None, half=False):
    spb = 60 / bpm; i = 0; t0 = a
    while t0 < b - 0.05:
        if i % 4 == 0 or (not half and i % 4 == 2): place(music, t0, kick(), 0.9 * gain)
        if snares and i % 4 == 2 and half: place(music, t0, snare(), 0.35 * gain)
        if snares and not half and i % 8 in (2, 6): place(music, t0, snare(), 0.35 * gain)
        if hats: place(music, t0 + spb / 2, hat(), 0.25 * gain)
        if bass and i % 2 == 0: place(music, t0, bass_note(note(bass[(i // 2) % len(bass)]), spb * 2), 0.35 * gain)
        t0 += spb; i += 1

# hook: dark tension
section_pad(0.0, 8.3, [38, 45, 50, 53], 0.55)
beat(0.0, 8.0, 92, 0.8, hats=False, snares=False, half=True, bass=[26, 26, 25, 25])
place(sfx, 0.0, impact(), 0.9)
place(sfx, 7.4, riser(0.8), 0.6)
# rewind
place(sfx, 8.2, whoosh(1.0), 0.8)
for k in range(10): place(sfx, 8.3 + k * 0.33, np.sin(2 * np.pi * (900 - k * 60) * tt(0.08)) * 0.2 * np.exp(-tt(0.08) * 30))
# day 1 -> 12: uneasy pulse
section_pad(12.0, 30.3, [45, 48, 52, 57], 0.35, 0.5)
beat(14.9, 30.2, 100, 0.55, snares=False, bass=[33, 33, 36, 31])
# market sneak: sparse tension
section_pad(39.5, 49.2, [40, 47, 50], 0.45)
for k in range(int((47.3 - 39.6) / 0.6)): place(music, 39.6 + k * 0.6, pluck(note(64 if k % 2 else 59), 0.35), 0.25)
section_pad(30.3, 39.6, [48, 52, 55, 60], 0.35, 0.6)      # Biscuit: warm
# chase: full drums
beat(51.7, 55.6, 160, 1.0, bass=[28, 28, 31, 26])
place(music, 51.7, pad([note(n) for n in (40, 47, 52)], 3.9, 0.8), 0.4)
# farm: light, hopeful plucks
section_pad(55.5, 63.8, [48, 52, 55, 59], 0.3, 0.6)
for k in range(int(8.2 / 0.3)):
    place(music, 55.6 + k * 0.3, pluck(note([60, 64, 67, 71, 67, 64][k % 6]), 0.4), 0.22)
# day 64 dread
section_pad(63.7, 73.3, [37, 44, 49], 0.5, 0.1)
# storm
section_pad(73.3, 77.3, [36, 43, 46], 0.5, 0.2)
# day 99 -> idea -> throw: build
section_pad(77.2, 95.7, [38, 45, 50, 53], 0.45, 0.4)
beat(77.2, 87.6, 110, 0.7, bass=[26, 26, 29, 24])
beat(87.8, 95.6, 120, 0.85, bass=[26, 29, 31, 33])
# day 100: dawn, soft
section_pad(95.7, 103.1, [50, 54, 57, 62], 0.35, 0.6)
for k in range(int(7.3 / 0.45)): place(music, 95.8 + k * 0.45, pluck(note([74, 69, 66, 69][k % 4]), 0.6), 0.16)
# too quiet: silence then a low drone + hit
place(music, 103.15, pad([note(31), note(38)], 1.3, 0.05), 0.5)
# CTA + end: bouncy
beat(104.4, 109.7, 118, 0.7, bass=[33, 36, 38, 40])
place(music, 104.4, tune(5.3, 76), 0.5)

# ---------- sound effects at story moments
cuts = [8.2, 12.1, 14.9, 20.6, 25.2, 30.3, 39.6, 47.3, 49.2, 51.7, 55.5, 63.7, 73.3, 77.2, 82.3, 91.4, 95.7, 104.4, 107.3]
for c in cuts: place(sfx, c - 0.18, whoosh(0.4), 0.45)
place(sfx, 12.35, buzz(), 0.55); place(sfx, 13.35, buzz(), 0.55)
for k in range(5): place(sfx, 15.2 + k * 0.5, groan(0.7, 160) * 0, 0)
place(sfx, 17.6, groan(2.0, 90), 0.4)
for a in (21.15, 21.95, 22.65, 23.25, 23.75, 24.2): place(sfx, a, thud(), 0.7)
place(sfx, 28.6, clang(0.6) * 0.3, 0.6)
for k in range(5): place(sfx, 30.5 + k * 0.8, scratch(), 0.8)
place(sfx, 35.1, creak(0.9), 0.7)
place(sfx, 36.0, bark(), 0.8); place(sfx, 36.3, bark(), 0.7); place(sfx, 38.0, bark(), 0.6)
for k in range(12): place(sfx, 39.7 + k * 0.62, thud(0.2) * 0.3, 0.3)       # soft steps
place(sfx, 48.45, clang(), 0.9)
for k in range(4): place(sfx, 49.4 + k * 0.22, groan(1.0, 110 + k * 8), 0.45)
place(sfx, 50.4, impact(), 0.7)
for k in range(14): place(sfx, 51.8 + k * 0.25, thud(0.15), 0.4)
place(sfx, 55.0, groan(1.2, 100), 0.3)
for k in range(5): place(sfx, 63.8 + k * 0.9, heartbeat(), 0.8)
place(sfx, 69.0, creak(1.0) * 0.6, 0.6); place(sfx, 70.0, creak(1.4), 0.8)
place(sfx, 71.9, impact(), 0.8); place(sfx, 72.0, groan(1.4, 85), 0.6)
place(sfx, 73.3, rain(4.0), 0.6)
for a in (73.8, 75.4, 76.6): place(sfx, a, thunder(), 0.75)
for k in range(8): place(sfx, 77.4 + k * 0.6, groan(0.9, 95 + (k % 3) * 10), 0.35)
for k in range(6): place(sfx, 77.5 + k * 0.8, thud(0.3), 0.5)
place(sfx, 84.3, np.sin(2 * np.pi * 1320 * tt(0.4)) * np.exp(-tt(0.4) * 8) * 0.3, 1.0)   # idea ding
place(sfx, 87.7, tune(3.7, 72), 0.55)
place(sfx, 91.5, tune(4.2, 72) * np.linspace(1, 0.2, int(4.2 * SR)), 0.5)
place(sfx, 91.75, whoosh(0.7), 0.9)
for k in range(6): place(sfx, 93.4 + k * 0.35, groan(0.9, 100 + k * 5), 0.3)
place(sfx, 96.0, creak(0.8), 0.6)
for k in range(6): place(sfx, 96.9 + k * 0.5, thud(0.15) * 0.4, 0.3)
place(sfx, 103.3, impact(1.4), 1.0)
place(sfx, 104.45, bark(), 0.9); place(sfx, 105.1, bark(), 0.8); place(sfx, 106.0, bark(), 0.8)
place(sfx, 107.3, impact(0.8) * 0.5, 0.6)

# ---------- narration
def read_wav(p):
    w = wave.open(p); sr = w.getframerate(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    if ch == 2: a = a.reshape(-1, 2).mean(1)
    return a, sr
v, vsr = read_wav("voice.wav")
v = np.interp(np.arange(int(len(v) * SR / vsr)) * vsr / SR, np.arange(len(v)), v)
voice = np.zeros(N); place(voice, 0.0, v, 1.0)
voice *= 0.95 / (np.abs(voice).max() + 1e-9)

# duck music under the voice
e = lp_fast(np.abs(voice), int(0.12 * SR)); e = e / (e.max() + 1e-9)
duck = 1.0 - 0.6 * np.clip(e * 3, 0, 1)
music *= 0.38 / (np.abs(music).max() + 1e-9) * 2.2
mix = voice * 1.0 + music * duck + sfx * 0.42
# soft limiter + loudness target
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
rms = np.sqrt(np.mean(mix[int(0.5 * SR):] ** 2)); mix *= 0.2 / rms
mix = np.clip(mix, -0.98, 0.98)
fade = int(0.6 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
with wave.open("mix.wav", "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((mix * 32767).astype(np.int16).tobytes())
print("mix.wav", len(mix) / SR, "s, peak", np.abs(mix).max())
