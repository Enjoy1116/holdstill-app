# Tense cut of "The Unknown Number — Part 1": scared narrator (eleven_v3), robot texter, tight gaps,
# and 4 jump-scare beats (JS1-JS4) with silence built in. Writes narr48.wav, unk48.wav, events.json.
import wave, json
import numpy as np
import botvoice as bv   # robot take, line cuts and sentence splits (also writes its own unk48 — overwritten below)

SR = 48000
def read(p):
    w = wave.open(p); sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    return np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a)
NARR = read("narr3f.wav"); TEMPO = 1.07

def env(x, win=0.02):
    n = int(win * SR); m = len(x) // n
    return np.sqrt((x[: m * n].reshape(m, n) ** 2).mean(1)), n

def squeeze(seg, max_gap=0.45, keep=0.32, thr=0.008):
    """Shorten long internal pauses so the scared delivery keeps moving."""
    e, n = env(seg); quiet = e < thr; out = []; i = 0; last = 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]: j += 1
            if (j - i) * n / SR > max_gap and i > 0 and j < len(quiet):
                out.append(seg[last * n:(i * n) + int(keep / 2 * SR)]); last = j - int(keep / 2 * SR / n)
            i = j
        else: i += 1
    out.append(seg[last * n:])
    return np.concatenate(out)

N3SRC = read("n3newf.wav")
def cutn(a, b, pa=0.1, pb=0.3, src=None):
    a, b = a / TEMPO, b / TEMPO
    seg = (NARR if src is None else src)[max(0, int((a - pa) * SR)):int((b + pb) * SR)].copy()
    seg = squeeze(seg); f = int(0.01 * SR); seg[:f] *= np.linspace(0, 1, f); seg[-f * 4:] *= np.linspace(1, 0, f * 4)
    return seg

N = {
 "N1": (0.0, 8.8, "At 7:25 AM, November 6th, I was watching videos on my phone... when an unknown number texted me."),
 "N2": (10.0, 13.4, "I thought it was a prank. Then it texted again."),
 "N3": (0.14, 12.6, "I checked. There was a pizza... and a chair... inside my fridge. How did it know that? I was home alone."),
 "N4": (21.9, 31.2, "So I went. The store was empty. The cashier kept coughing. And his eyes... were yellow."),
 "N5": (32.8, 35.6, "11:58. I locked the door."),
 "N6": (36.8, 42.0, "11:59. Every phone in the city started screaming."),
 "N7": (43.2, 45.2, "Then the real screaming started."),
 "N8": (47.3, 55.7, "Day 3. Someone knocked. It was Mr. Hale, my neighbor. He was begging me to let him in."),
 "N9": (56.7, 61.0, "My hand was already on the lock... when my phone buzzed."),
 "N10": (62.2, 67.0, "I didn't open it. 10 seconds later, he stopped begging."),
 "N10b": (67.8, 69.4, "And started scratching."),
 "N11": (71.2, 80.4, "3 AM. Something was buzzing over the city. A drone. It dropped a box, right at my feet."),
 "N12": (81.6, 93.0, "Inside: a radio, a flashlight, and a map. One place was circled in red. The bridge. Day 30."),
 "N13": (94.2, 96.8, "Day 12. The power died."),
 "N14": (97.9, 105.2, "Across the street, someone turned on a flashlight. 30 seconds later... it went out."),
 "N15": (106.8, 114.3, "Day 18. Trucks. Men in white suits, with a logo I'd never seen before."),
 "N16": (115.5, 119.6, "They weren't killing the zombies. They were collecting them."),
 "N17": (120.8, 124.3, "Then one of them looked up. Right at my window."),
 "N18": (125.8, 129.0, "Day 23. I had to ask."),
 "N19": (130.2, 133.8, "How did they know that? Nobody knew that."),
 "N20": (135.3, 137.4, "My phone was at 1%."),
 "N21": (138.8, 146.4, "Day 30. I ran. I didn't stop. And they heard every single step."),
 "N22": (147.5, 152.6, "I made it to the bridge. It was empty. Nobody was there."),
 "N23": (153.7, 155.1, "Then my phone buzzed."),
 "N24": (155.9, 159.1, "Behind me... was a man in a white suit."),
 "N25": (160.2, 165.5, "Who is the unknown number? Comment your guess. Follow for part 2."),
}
BUB = {
 "U1": ["At midnight, the world ends.", "Do exactly what I say, and you'll live."],
 "U2": ["There's a pizza and a chair in your fridge."],
 "U3": ["Don't go to school today.", "Buy water, canned food, batteries.", "Go. NOW."],
 "U4": ["No time.", "Trust me."],
 "U5": ["Don't touch him.", "Go home.", "Lock your door at exactly 11:58."],
 "U6": ["RULE 1: Don't open the door. For anyone.", "Not even people you know."],
 "U7": ["Don't."],
 "U8": ["RULE 2: The roof. 3 AM.", "Come alone."],
 "U9": ["RULE 3: They're drawn to light.", "Keep the curtains shut."],
 "U10": ["GET DOWN.", "NOW."],
 "U11": ["Because I owe you."],
 "U12": ["You used to be scared of thunder.", "You still are."],
 "U13": ["Tomorrow. 6 AM.", "Get to the bridge.", "Don't stop. Don't look back."],
 "U14": ["Turn around."],
}
H = {"H1": "who is this??", "H2": "why are you helping me?", "H3": "who ARE you"}
JS = {"JS1": 1.7, "JS2": 2.2, "JS3": 1.6, "JS4": 4.2}

SEQ = [
 (0.15, "N1"), (0.2, "U1"), (0.25, "N2"), (0.3, "U2"), (0.9, "N3"),
 (1.4, "U3"), (0.25, "H1"), (0.25, "U4"), (0.35, "N4"), (0.0, "JS1"), (0.1, "U5"), (0.35, "N5"), (0.3, "N6"), (0.25, "N7"),
 (1.3, "U6"), (0.45, "N8"), (0.3, "N9"), (0.45, "U7"), (0.9, "N10"), (0.0, "JS2"), (0.0, "N10b"),
 (1.3, "U8"), (0.4, "N11"), (0.3, "N12"),
 (0.7, "N13"), (1.3, "U9"), (0.3, "N14"),
 (0.7, "N15"), (0.25, "N16"), (0.3, "N17"), (0.2, "U10"),
 (0.9, "N18"), (0.25, "H2"), (0.4, "U11"), (0.25, "H3"), (0.6, "U12"), (0.0, "JS3"), (0.15, "N19"),
 (1.0, "U13"), (0.3, "N20"),
 (0.7, "N21"), (0.3, "N22"), (0.4, "N23"), (0.5, "U14"), (0.0, "JS4"), (0.0, "N24"), (1.3, "N25"),
]

def robot_chunks(k):
    if k == "U2": return [bv.trim(read("u2new.raw"))]
    if k == "U14": return [bv.trim(bv.TURN)]
    seg = bv.BOT[int(bv.cuts[k][0] * SR):int(bv.cuts[k][1] * SR)]
    return bv.split_at(seg, bv.cuts[k][0], bv.SPLITS[k]) if k in bv.SPLITS else [bv.trim(seg)]

def type_len(s): return 0.45 + 0.06 * len(s)

t = 0.0; events = []
nstem = np.zeros(int(200 * SR)); ustem = np.zeros(int(200 * SR))
for gap, k in SEQ:
    t += gap
    if k in N:
        a, b, txt = N[k]; seg = cutn(a, b, src=N3SRC if k == "N3" else None)
        i = int(t * SR); nstem[i:i + len(seg)] += seg
        d = len(seg) / SR
        events.append(dict(id=k, kind="N", t=round(t + 0.1, 3), end=round(t + d - 0.3, 3), text=txt))
        t += d - 0.2
    elif k in BUB:
        chunks = robot_chunks(k); bubbles = []; tt = t + 0.15
        for j, c in enumerate(chunks):
            i = int(tt * SR); ustem[i:i + len(c)] += c
            bubbles.append([round(tt - 0.12, 3), BUB[k][j] if j < len(BUB[k]) else ""])
            tt += len(c) / SR + 0.22
        if len(chunks) < len(BUB[k]):          # fewer audio chunks than bubbles: spread the rest
            for j in range(len(chunks), len(BUB[k])): bubbles.append([round(tt - 0.4 + 0.3 * j, 3), BUB[k][j]])
        events.append(dict(id=k, kind="U", t=bubbles[0][0], end=round(tt - 0.22, 3), bubbles=bubbles))
        t = tt - 0.22
    elif k in H:
        d = type_len(H[k]); events.append(dict(id=k, kind="H", t=round(t, 3), end=round(t + d, 3), text=H[k])); t += d
    else:
        events.append(dict(id=k, kind="S", t=round(t, 3), end=round(t + JS[k], 3))); t += JS[k]
END = t + 0.3; CARD = 2.6; total = END + CARD
for name, st in (("narr48.wav", nstem), ("unk48.wav", ustem)):
    st = st[: int(total * SR)]
    with wave.open(name, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR); o.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
json.dump(dict(events=events, story_end=round(END, 3), total=round(total, 3)), open("events.json", "w"), indent=1)
for e in events: print(f"{e['t']:7.2f} {e['end']:7.2f} {e['id']:5s} {(e.get('text') or (e.get('bubbles') or [['', '']])[0][1])[:50]}")
print("story end", round(END, 2), "total", round(total, 2))
