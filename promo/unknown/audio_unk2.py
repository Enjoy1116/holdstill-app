# Soundtrack for "The Unknown Number — Part 1": narrator + phone-filtered unknown voice + score + sfx (48 kHz).
import wave, math, json
import numpy as np
import unk1
from unk1 import EV, T, E, frac, SHOTS

TOTAL = unk1.TOTAL
src = open("/home/claude/stick100/audio.py").read().split("# ---------- build music bed")[0]
src = src.replace("DUR = 109.8", f"DUR = {TOTAL}")
exec(src)

def shot_start(name):
    for a, b, fn, d, tr in SHOTS:
        if fn.__name__ == name: return a
    raise KeyError(name)

music = np.zeros(N); sfx = np.zeros(N); amb = np.zeros(N)

def sine(f, d, decay=0.0):
    t = tt(d); return np.sin(2 * np.pi * f * t) * (np.exp(-t * decay) if decay else 1)

def ding():
    a = sine(1318, 0.12, 18) * 0.6; b = sine(1760, 0.3, 10) * 0.6
    out = np.zeros(int(0.45 * SR)); out[:len(a)] += a; out[int(0.11 * SR):int(0.11 * SR) + len(b)] += b
    return out

def send():
    w = whoosh(0.25) * 0.4; w[:int(0.08 * SR)] += sine(880, 0.08, 30) * 0.3; return w

def click(): n = noise(0.025); return (n - lp_fast(n, 3)) * np.exp(-tt(0.025) * 160) * 0.5

def vibrate(d=0.8):
    t = tt(d); s = np.sin(2 * np.pi * 170 * t) * (np.sin(2 * np.pi * 2.5 * t) > -0.2) + lp_fast(noise(d), 12) * 0.4
    return s * 0.6 * env(len(t), 0.01, 0.05)

def boom(d=2.2):
    t = tt(d); return (np.sin(2 * np.pi * (32 + 50 * np.exp(-t * 6)) * t) * 1.2 + lp_fast(noise(d), 80) * 0.5) * np.exp(-t * 1.8)

def reverse_riser(d=1.2):
    r = riser(d); return r * 1.2

def tick():
    return (sine(3200, 0.025, 200) * 0.5 + click() * 0.8)

def cough():
    d = 0.32; n = lp_fast(noise(d), 5); t = tt(d)
    return (n - lp_fast(n, 40)) * 1.4 * np.exp(-t * 12) * (1 + 0.6 * np.sin(2 * np.pi * 130 * t))

def scream(d=1.2, f0=620, seed=0):
    r = np.random.default_rng(seed); t = tt(d)
    f = f0 * (1 + 0.35 * np.sin(np.pi * t / d)) * (1 + 0.03 * np.sin(2 * np.pi * 6 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(np.sin(ph * k) / k for k in range(1, 9)) + r.uniform(-1, 1, len(t)) * 0.4
    s = s - lp_fast(s, 30); s = lp_fast(s, 3)
    return s * 0.4 * env(len(t), 0.05, 0.4)

def eas(d):
    t = tt(d); s = np.sin(2 * np.pi * 853 * t) + np.sin(2 * np.pi * 960 * t)
    return np.tanh(2 * s) * 0.35 * env(len(t), 0.02, 0.1)

def hum(d, f=60):
    t = tt(d); s = np.sign(np.sin(2 * np.pi * f * t)) * 0.3 + np.sin(2 * np.pi * 2 * f * t) * 0.3
    return lp_fast(s, 20) * env(len(t), 0.3, 0.3)

def drone_hum(d):
    t = tt(d); f = 190 + 6 * np.sin(2 * np.pi * 0.5 * t)
    s = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR) * 0.4
    s = lp_fast(s, 5) * (0.7 + 0.3 * np.sin(2 * np.pi * 31 * t))
    return s * np.linspace(0, 1, len(t)) ** 0.5

def wind(d): n = noise(d); return lp_fast(n, 120) * 3 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.2 * tt(d)))

def power_down(d=1.4):
    t = tt(d); f = 420 * np.exp(-t * 2.5) + 30
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.2) * 0.6

def beep(f=1100, d=0.18): return sine(f, d) * env(int(d * SR), 0.005, 0.03) * 0.35

def engine(d):
    t = tt(d); s = np.sign(np.sin(2 * np.pi * 38 * t)) * 0.5 + lp_fast(noise(d), 60) * 1.2
    return lp_fast(s, 30) * env(len(t), 0.8, 0.8)

def phone_die():
    t = tt(0.9); return np.sin(2 * np.pi * np.cumsum(700 * np.exp(-t * 3)) / SR) * np.exp(-t * 3) * 0.5

def footsteps(a, b, step, gain):
    k = 0
    while a + k * step < b: place(sfx, a + k * step, thud(0.18) * 0.5, gain); k += 1

# ---------------- music

def beat(a, b, bpm, gain=1.0, hats=True, snares=True, bass=None, half=False):
    spb = 60 / bpm; i = 0; t0 = a
    while t0 < b - 0.05:
        if i % 4 == 0 or (not half and i % 4 == 2): place(music, t0, kick(), 0.9 * gain)
        if snares and i % 4 == 2 and half: place(music, t0, snare(), 0.35 * gain)
        if snares and not half and i % 8 in (2, 6): place(music, t0, snare(), 0.35 * gain)
        if hats: place(music, t0 + spb / 2, hat(), 0.25 * gain)
        if bass and i % 2 == 0: place(music, t0, bass_note(note(bass[(i // 2) % len(bass)]), spb * 2), 0.35 * gain)
        t0 += spb; i += 1
def drone_pad(a, b, chord, g, bright=0.15): place(music, a, pad([note(n) for n in chord], b - a, bright), g)

st = {fn.__name__: (a, b) for a, b, fn, d, tr in SHOTS}
A = lambda n: st[n][0]; B = lambda n: st[n][1]


# ================= HORROR SCORE (tense cut) =================
def braam(d=3.0, f=43.65):
    t = tt(d); s = np.zeros_like(t)
    for ff, a in ((f, 1.0), (f * 1.005, 0.8), (f * 1.5, 0.5), (f * 2, 0.45), (f * 2.01, 0.35)):
        s += a * (2 * ((ff * t) % 1) - 1)
    s = lp_fast(s, 10) * 0.6 + lp_fast(s, 3) * 0.25 * np.exp(-t * 3)
    return np.tanh(s * 1.6) * env(len(t), 0.05, 1.6) * np.exp(-t * 0.6)

def screech(d=1.1, seed=1):
    r = np.random.default_rng(seed); t = tt(d); s = np.zeros_like(t)
    for f0 in (1760, 1866, 2349, 2489, 3136):
        f = f0 * (1 - 0.25 * t / d) * (1 + 0.01 * np.sin(2 * np.pi * 9 * t))
        s += np.sin(2 * np.pi * np.cumsum(f) / SR + r.uniform(0, 6))
    s = s / 5 + r.uniform(-1, 1, len(t)) * 0.5
    s = s - lp_fast(s, 4)
    return np.tanh(s * 2.5) * np.exp(-t * 2.6) * env(len(t), 0.003, 0.2)

def stinger(at, big=1.0):
    place(sfx, at, screech(1.2, int(at)), 1.0 * big)
    place(sfx, at, impact(1.4), 1.2 * big); place(sfx, at, boom(2.6), 1.2 * big)
    place(sfx, at + 0.02, scream(1.0, 900, int(at) + 3), 0.6 * big)

def strings_trem(d, notes, rate=9.0):
    t = tt(d); s = np.zeros_like(t)
    for n in notes:
        f = note(n); s += 2 * ((f * t + 0.3 * np.sin(2 * np.pi * 5 * t)) % 1) - 1
    s = lp_fast(s / len(notes), 14) * (0.55 + 0.45 * np.sin(2 * np.pi * rate * t))
    return s * env(len(t), 1.0, 1.0)

def tick_run(a, b, i0, i1, g=0.4):
    t = a
    while t < b:
        place(music, t, tick(), g); k = (t - a) / max(0.01, b - a); t += lerp(i0, i1, k)

def heartbeats(a, b, i0=0.9, i1=0.55, g=1.0):
    t = a
    while t < b:
        place(sfx, t, heartbeat(), g); k = (t - a) / max(0.01, b - a); t += lerp(i0, i1, k)

from rig import lerp

# silence windows: everything except heartbeat/voice is pulled down so the scare hits from silence
QUIET = [(T("JS1") + 0.05, T("JS1") + 0.6), (T("JS2") - 0.1, T("JS2") + 1.35), (T("JS3") + 0.05, T("JS3") + 0.45), (T("JS3") + 0.8, T("JS3") + 1.07),
         (T("JS4") + 0.05, T("JS4") + 3.3)]
SCARES = [T("JS1") + 0.6, T("JS2") + 1.35, T("JS3") + 1.07, T("JS4") + 3.3]

# --- hook: instant hit
place(sfx, 0.0, braam(3.5), 1.0); place(sfx, 0.0, impact(1.2), 0.8)
drone_pad(0, A("s_title"), [26, 27, 33, 38], 0.5, 0.05)
place(music, 0.0, strings_trem(A("s_title"), [50, 51, 57], 7), 0.35)
tick_run(0.3, A("s_title"), 0.5, 0.42, 0.3)
place(sfx, T("U2") + 0.1, braam(3.0, 41.2), 1.0)
place(sfx, A("s_title") - 1.0, riser(1.0), 0.8)
place(sfx, A("s_title"), impact(1.6), 1.0); place(sfx, A("s_title"), braam(2.5, 36.7), 0.9)
# --- day 0: clock speeding toward midnight
drone_pad(A("s_day0"), A("s_alert"), [33, 34, 40, 45], 0.45, 0.2)
place(music, A("s_day0"), strings_trem(A("s_alert") - A("s_day0"), [57, 58, 64], 8), 0.3)
tick_run(A("s_day0"), A("s_alert"), 0.5, 0.18, 0.35)
heartbeats(frac("N4", 0.5), T("JS1"), 0.8, 0.5, 0.9)
# alert + chaos
beat(A("s_alert"), A("s_rule1") - 0.2, 140, 1.0, bass=[26, 26, 27, 25])
place(music, A("s_alert"), strings_trem(A("s_rule1") - A("s_alert"), [62, 63, 69], 12), 0.4)
# rule cards
for k in ("U6", "U8", "U9"): place(sfx, T(k) - 1.15, braam(2.2, 41.2), 1.0); place(sfx, T(k) - 1.15, impact(1.0), 0.7)
# day 1-3: dread, heartbeat on the lock
drone_pad(A("s_rule1"), A("s_rule2"), [25, 26, 32, 37], 0.5, 0.05)
place(music, A("s_knock"), strings_trem(T("JS2") - A("s_knock"), [49, 50, 56], 6), 0.35)
heartbeats(T("N9"), T("U7"), 0.7, 0.45, 1.1)
place(sfx, T("U7"), braam(2.6, 38.9), 1.1); place(sfx, T("U7"), impact(1.2), 0.9)
# day 7
drone_pad(A("s_rule2"), A("s_power"), [28, 29, 35, 40], 0.4, 0.2)
place(music, A("s_roof"), strings_trem(A("s_power") - A("s_roof"), [52, 53, 59], 5), 0.3)
place(sfx, frac("N12", 0.86), braam(2.4), 0.9)
# day 12
drone_pad(A("s_power"), A("s_trucks"), [24, 25, 31], 0.5, 0.05)
heartbeats(frac("N14", 0.4), E("N14"), 0.8, 0.6, 0.8)
# day 18 industrial pulse
beat(A("s_trucks"), A("s_corner"), 96, 0.7, hats=True, snares=True, half=True, bass=[23, 23, 24, 21])
place(music, A("s_trucks"), strings_trem(A("s_corner") - A("s_trucks"), [47, 48, 54], 8), 0.3)
place(sfx, A("s_lookup") + 0.6, braam(2.6, 38.9), 1.0)
place(sfx, T("U10"), impact(1.2), 1.0); place(sfx, T("U10"), braam(2.0), 0.8)
# day 23 – thunder reveal
drone_pad(A("s_corner"), A("s_run"), [33, 34, 40, 45], 0.4, 0.2)
place(amb, A("s_corner"), rain(B("s_nobody") - A("s_corner")), 0.6)
place(sfx, T("JS3") + 0.45, thunder(3.0), 1.2)
place(sfx, T("JS3") + 1.0, thunder(2.0), 0.6)
# day 29-30
tick_run(A("s_rule4"), A("s_run"), 0.45, 0.25, 0.3)
beat(A("s_run"), A("s_bridge"), 168, 1.0, bass=[28, 28, 29, 26])
place(music, A("s_run"), strings_trem(A("s_bridge") - A("s_run"), [64, 65, 71], 14), 0.45)
drone_pad(A("s_bridge"), A("s_black"), [26, 27, 33, 38], 0.5, 0.1)
place(sfx, T("U14"), braam(3.0, 36.7), 1.1)
heartbeats(T("JS4"), T("JS4") + 3.3, 0.75, 0.42, 1.2)
place(sfx, T("N24") + 1.2, braam(2.4, 34.6), 0.9)
place(sfx, A("s_black"), phone_die(), 1.0)
# CTA
drone_pad(A("s_cta"), TOTAL, [38, 45, 50, 53], 0.35, 0.4)
beat(A("s_cta"), TOTAL - 0.3, 92, 0.6, hats=True, snares=True, half=True, bass=[26, 26, 29, 24])

# ---- sound effects (story)
_n3 = T("N3"); _d3 = E("N3") - _n3
place(amb, A("s_fridge"), hum(B("s_fridge") - A("s_fridge"), 50), 0.6)
footsteps(A("s_fridge"), A("s_fridge") + 1.3, 0.33, 0.3)
place(sfx, _n3 + _d3 * 0.13, creak(0.7), 0.9); place(sfx, _n3 + _d3 * 0.13, whoosh(0.4), 0.4)
place(sfx, _n3 + _d3 * 0.42, braam(2.6, 41.2), 1.0)
for a, b, fn, d, tr in SHOTS[1:]:
    if tr != "cut": place(sfx, a - 0.2, whoosh(0.4), 0.35)
place(sfx, E("N9") - 0.5, vibrate(0.9), 0.9)
place(sfx, frac("N23", 0.6), vibrate(0.9), 0.9)
place(amb, A("s_store"), hum(B("s_store") - A("s_store"), 60), 0.35)
c0 = frac("N4", 0.42)
for k in range(3): place(sfx, c0 + k * 1.1, cough(), 0.9); place(sfx, c0 + k * 1.1 + 0.18, cough() * 0.7, 0.9)
footsteps(A("s_store") + 0.1, A("s_store") + 4.0, 0.42, 0.25)
place(sfx, A("s_lock") + 1.25, clang(0.4) * 0.5, 0.8); place(sfx, A("s_lock") + 1.25, thud(0.3), 0.8)
place(sfx, A("s_alert") + 0.05, eas(B("s_alert") - A("s_alert") - 0.1), 0.6)
for k in range(8): place(sfx, A("s_chaos") + 0.05 + k * 0.28, scream(1.1, 520 + k * 50, k), 0.6)
place(sfx, A("s_chaos"), groan(2.0, 90), 0.5)
for kn in [0.15, 0.45, 0.75, 1.5, 1.75, 2.0]: place(sfx, A("s_knock") + kn, thud(0.35), 1.1)
for k in range(3): place(sfx, A("s_peep") + 0.4 + k * 1.3, thud(0.3) * 0.6, 0.6)
for k in range(10): place(sfx, T("N10b") + 0.1 + k * 0.35, scratch(0.35), 1.0)
place(amb, A("s_roof"), wind(B("s_roof") - A("s_roof")), 0.4)
place(sfx, frac("N11", 0.12), drone_hum(frac("N11", 0.72) - frac("N11", 0.12) + 1.5), 0.45)
place(sfx, frac("N11", 0.72) + 0.38, thud(0.6), 1.0); place(sfx, frac("N11", 0.72) + 0.38, impact(0.6), 0.5)
place(sfx, frac("N12", 0.38), whoosh(0.5) * 0.8, 0.6)
place(amb, A("s_power"), hum(frac("N13", 0.75) - A("s_power") + 0.1, 60), 0.4)
place(sfx, frac("N13", 0.75) + 0.1, power_down(), 1.0)
place(sfx, frac("N14", 0.37), click() * 3, 0.9)
for k in range(5): place(sfx, frac("N14", 0.45) + k * 0.6, groan(1.0, 90 + k * 8), 0.4)
place(sfx, frac("N14", 0.9), scream(0.9, 700, 9) * 0.6, 0.6)
place(amb, A("s_trucks"), engine(B("s_trucks") - A("s_trucks")), 0.6)
for k in range(8): place(sfx, A("s_trucks") + 2.5 + k * 0.6, beep(), 0.5)
footsteps(A("s_run"), B("s_run"), 0.19, 0.45)
for k in range(7): place(sfx, A("s_run") + k * 0.8, groan(0.9, 100 + k * 6), 0.45)
place(amb, A("s_bridge"), wind(B("s_turn") - A("s_bridge")), 0.5)
footsteps(A("s_bridge"), A("s_bridge") + 2.2, 0.22, 0.3)

# ---- apply silence windows, then the stingers on top (so they hit from silence)
gate = np.ones(N)
for a, b in QUIET:
    i, j = int(a * SR), int(b * SR); r = int(0.25 * SR)
    gate[i:j] = 0.04
    gate[max(0, i - r):i] = np.minimum(gate[max(0, i - r):i], np.linspace(1, 0.04, i - max(0, i - r)))
music *= gate; amb *= gate
hb_keep = np.zeros(N)   # heartbeats survive the gate: rebuild them for the quiet windows only
for a, b in QUIET:
    if b - a > 1.0: 
        t = a
        while t < b - 0.2: place(hb_keep, t, heartbeat(), 1.0); t += 0.62
sfx *= gate
sfx += hb_keep * 1.1
# ---------------- voices
def read_wav(p):
    w = wave.open(p); return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
nar = read_wav("narr48.wav"); unk = read_wav("unk48.wav")
nar = np.pad(nar, (0, max(0, N - len(nar))))[:N]; unk = np.pad(unk, (0, max(0, N - len(unk))))[:N]

def bandpass(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.clip((f - lo * 0.7) / (lo * 0.3), 0, 1) * np.clip((hi * 1.3 - f) / (hi * 0.3), 0, 1)
    return np.fft.irfft(X * m, len(x))
from scipy.signal import lfilter
def robot(x):
    """Clear but robotic: mostly the dry voice, plus a light ring-mod + metallic comb layer."""
    tt_ = np.arange(len(x)) / SR
    x = x / (np.abs(x).max() + 1e-9)
    ring = x * np.sin(2 * np.pi * 60 * tt_)
    d = int(0.004 * SR); a = np.zeros(d + 1); a[0] = 1; a[d] = -0.35
    metal = lfilter([1.0], a, x)
    y = 0.62 * x + 0.30 * ring + 0.38 * metal / (np.abs(metal).max() + 1e-9)
    pres = bandpass(y, 1800, 4200)                                     # presence lift so words cut through
    y = y + 0.35 * pres
    y = bandpass(y, 120, 7500)
    return np.tanh(y * 1.4) / np.tanh(1.4)
unk_f = robot(unk)
unk_f *= 0.95 / (np.abs(unk_f).max() + 1e-9)
nar *= 0.95 / (np.abs(nar).max() + 1e-9)
def rms_active(x):
    a = np.abs(x) > 0.02; return np.sqrt(np.mean(x[a] ** 2))
unk_f *= rms_active(nar) / rms_active(unk_f) * 0.95
voice = nar + unk_f

e = lp_fast(np.abs(voice), int(0.12 * SR)); e = e / (e.max() + 1e-9)
duck = 1.0 - 0.62 * np.clip(e * 3, 0, 1)
music *= 0.38 / (np.abs(music).max() + 1e-9) * 2.0
amb *= 0.3 / (np.abs(amb).max() + 1e-9)
mix = voice + music * duck + sfx * 0.42 * (0.55 + 0.45 * duck) + amb * duck
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
rms = np.sqrt(np.mean(mix[int(0.5 * SR):] ** 2)); mix *= 0.14 / rms      # body sits lower so the scares can hit HARD
mix = np.clip(mix, -0.9, 0.9)
# --- jump-scare blasts, added AFTER the limiter at near full scale (way louder than the voice)
def blast(seed):
    d = 1.3; t = tt(d); r = np.random.default_rng(seed)
    s = screech(d, seed) * 1.0 + scream(d, 820, seed) * 0.8 + scream(d, 1250, seed + 9) * 0.6
    s += np.tanh(r.uniform(-1, 1, len(t)) * 3) * 0.5 * np.exp(-t * 3)          # noise blast
    low = boom(d) * 1.3 + impact(d) * 1.0
    s = np.tanh((s + low) * 3.0) * env(len(t), 0.002, 0.35)
    return s / (np.abs(s).max() + 1e-9)
for i, at in enumerate(SCARES):
    b = blast(i + 3) * 0.97; k = int(at * SR); n = min(len(b), N - k)
    mix[k:k + n] = np.clip(mix[k:k + n] * 0.15 + b[:n], -0.99, 0.99)
fade = int(0.8 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
with wave.open("mix.wav", "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes())
print("mix.wav", len(mix) / SR, "s")
