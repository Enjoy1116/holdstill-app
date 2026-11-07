# Builds the story timeline for "The Unknown Number — Part 1":
# cuts the two voice takes into lines, places them with dramatic gaps, writes voice stems + events.json
import wave, json
import numpy as np

SR = 48000

def read(p):
    w = wave.open(p); sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    return np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a)

NARR = read("narr.raw"); UNK = read("unk.raw"); NARR2 = read("narr2.raw"); UNK2 = read("unk2.raw")

N = {  # narrator lines: (start, end) in the take, text
 "N1": (0.1, 7.3, "At 7:25 AM, November 6th, I was watching videos on my phone... when an unknown number texted me.", "2"),
 "N2": (7.9, 11.0, "I thought it was a prank. Then it texted again.", "2"),
 "N3": (11.6, 15.0, "I was. How did it know that? I was home alone.", "2"),
 "N4": (12.0, 19.5, "So I went. The store was almost empty. The cashier kept coughing. And his eyes... were yellow."),
 "N5": (20.3, 22.5, "At 11:58, I locked the door."),
 "N6": (23.1, 27.2, "At 11:59, every phone in the city started screaming."),
 "N7": (27.7, 29.4, "Then the real screaming started."),
 "N8": (30.1, 35.9, "On day 3, someone knocked. It was Mr. Hale, my neighbor. He was begging me to let him in."),
 "N9": (36.6, 39.7, "My hand was already on the lock... when my phone buzzed."),
 "N10": (40.2, 45.3, "I didn't open it. 10 seconds later, he stopped begging. And started scratching."),
 "N11": (46.1, 52.1, "At 3 AM, something buzzed over the city. A drone. It dropped a box, right at my feet."),
 "N12": (52.6, 60.7, "Inside, a radio, a flashlight, and a map. One place was circled in red. The bridge. Day 30."),
 "N13": (61.2, 63.1, "On day 12, the power died."),
 "N14": (15.7, 20.9, "Across the street, someone turned on a flashlight. 30 seconds later... it went out.", "2"),
 "N15": (70.1, 75.9, "Day 18. Trucks came. Men in white suits, with a logo I had never seen before."),
 "N16": (76.4, 79.2, "They weren't killing the zombies. They were collecting them."),
 "N17": (79.8, 82.4, "Then one of them looked up. Right at my window."),
 "N18": (83.1, 85.6, "On day 23, I finally asked."),
 "N19": (21.4, 23.6, "How did they know that? Nobody knew that.", "2"),
 "N20": (88.9, 90.5, "My phone was at 1%."),
 "N21": (91.1, 96.2, "Day 30. I ran. I didn't stop. And they heard every single step."),
 "N22": (96.7, 100.2, "I made it to the bridge. It was empty. Nobody was there."),
 "N23": (24.2, 25.6, "Then my phone buzzed.", "2"),
 "N24": (103.8, 106.4, "Behind me... was a man in a white suit."),
 "N25": (107.2, 110.2, "Who do you think the unknown number is? Follow for part 2."),
}
U = {  # unknown-number lines: (start, end), bubbles [(offset, text)]
 "U1": (0.1, 5.5, [(0.0, "At midnight, the world ends."), (2.7, "Do exactly what I say, and you'll live.")], "2"),
 "U2": (7.6, 9.4, [(0.0, "You're wearing the orange scarf right now.")]),
 "U3": (7.8, 14.3, [(0.0, "Don't go to school today."), (1.9, "Buy water, canned food, batteries."), (5.2, "Go. NOW.")], "2"),
 "U4": (19.4, 21.6, [(0.0, "No time."), (1.7, "Trust me.")]),
 "U5": (23.3, 29.0, [(0.0, "Don't touch him."), (1.2, "Go home."), (3.0, "Lock your door at exactly 11:58.")]),
 "U6": (30.8, 36.5, [(0.0, "RULE 1: Don't open the door. For anyone."), (4.4, "Not even people you know.")]),
 "U7": (38.5, 38.8, [(0.0, "Don't.")]),
 "U8": (40.6, 44.6, [(0.0, "RULE 2: The roof. 3 AM."), (3.5, "Come alone.")]),
 "U9": (46.5, 50.7, [(0.0, "RULE 3: They're drawn to light."), (3.3, "Keep the curtains shut.")]),
 "U10": (52.4, 54.2, [(0.0, "GET DOWN."), (1.6, "NOW.")]),
 "U11": (56.3, 57.2, [(0.0, "Because I owe you.")]),
 "U12": (59.1, 62.5, [(0.0, "You used to be scared of thunder."), (2.8, "You still are.")]),
 "U13": (64.2, 71.1, [(0.0, "Tomorrow. 6 AM."), (1.8, "Get to the bridge."), (4.2, "Don't stop. Don't look back.")]),
 "U14": (73.2, 73.7, [(0.0, "Turn around.")]),
}
H = {"H1": "who is this??", "H2": "why are you helping me?", "H3": "who ARE you"}

# (gap before, id) — gaps are where the suspense breathes
SEQ = [
 (0.5, "N1"), (0.35, "U1"), (0.5, "N2"), (0.5, "U2"), (0.8, "N3"),
 (2.2, "U3"), (0.4, "H1"), (0.4, "U4"), (0.6, "N4"), (0.5, "U5"), (0.7, "N5"), (0.6, "N6"), (0.5, "N7"),
 (1.0, "U6"),
 (0.8, "N8"), (0.4, "N9"), (0.5, "U7"), (1.3, "N10"),
 (1.0, "U8"), (0.6, "N11"), (0.5, "N12"),
 (1.0, "N13"), (0.5, "U9"), (0.5, "N14"),
 (1.0, "N15"), (0.4, "N16"), (0.5, "N17"), (0.3, "U10"),
 (1.2, "N18"), (0.4, "H2"), (0.7, "U11"), (0.4, "H3"), (1.0, "U12"), (0.9, "N19"),
 (1.0, "U13"), (0.5, "N20"),
 (1.1, "N21"), (0.5, "N22"), (0.8, "N23"), (1.0, "U14"), (1.8, "N24"), (1.6, "N25"),
]

def cut(src, a, b, pa=0.1, pb=0.28):
    i = max(0, int((a - pa) * SR)); j = min(len(src), int((b + pb) * SR))
    seg = src[i:j].copy(); f = int(0.012 * SR)
    seg[:f] *= np.linspace(0, 1, f); seg[-f * 4:] *= np.linspace(1, 0, f * 4)
    return seg, (a - pa) - i / SR  # leading offset of the first word

def type_len(s): return 0.5 + 0.075 * len(s)

t = 0.0; events = []
nstem = np.zeros(int(200 * SR)); ustem = np.zeros(int(200 * SR))
for gap, k in SEQ:
    t += gap
    if k[0] == "N":
        a, b, txt = N[k][:3]; seg, _ = cut(NARR2 if len(N[k]) > 3 else NARR, a, b, 0.12, 0.25)
        i = int(t * SR); nstem[i:i + len(seg)] += seg
        events.append(dict(id=k, kind="N", t=round(t + 0.08, 3), end=round(t + 0.08 + (b - a), 3), text=txt))
        t += len(seg) / SR - 0.15
    elif k[0] == "U":
        a, b, bubbles = U[k][:3]; seg, _ = cut(UNK2 if len(U[k]) > 3 else UNK, a, b, 0.1, 0.3)
        i = int(t * SR); ustem[i:i + len(seg)] += seg
        t0 = t + 0.1
        events.append(dict(id=k, kind="U", t=round(t0 - 0.25, 3), end=round(t0 + (b - a), 3),
                           bubbles=[[round(t0 + o - (0.25 if j == 0 else 0.05), 3), s] for j, (o, s) in enumerate(bubbles)]))
        t += len(seg) / SR - 0.15
    else:
        d = type_len(H[k])
        events.append(dict(id=k, kind="H", t=round(t, 3), end=round(t + d, 3), text=H[k]))
        t += d
END = t + 0.4
CARD = 2.6
total = END + CARD
nstem = nstem[: int(total * SR)]; ustem = ustem[: int(total * SR)]
for name, st in (("narr48.wav", nstem), ("unk48.wav", ustem)):
    with wave.open(name, "wb") as o:
        o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
        o.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
json.dump(dict(events=events, story_end=round(END, 3), total=round(total, 3)), open("events.json", "w"), indent=1)
for e in events: print(f"{e['t']:7.2f} {e['end']:7.2f} {e['id']:4s} {e.get('text', e.get('bubbles', [['', '']])[0][1])[:60]}")
print("story end", round(END, 2), "total", round(total, 2))
