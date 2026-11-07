# THE UNKNOWN NUMBER — stickman zombie series (Framey)

Multi-part TikTok/Reels series. Each part ~3 minutes, 1080x1920, 60 fps. No dog in this series.

## Series secret (do NOT reveal until the finale)
The unknown number is the hero's **dad**. He was kidnapped by **HELIX** — the company that made the zombies —
and forced to work for them. He texts his kid from inside HELIX to keep him alive.
Finale: they reunite after the hero rescues him / he escapes.

Clues to plant (never say "dad" before the finale):
- Part 1: "Because I owe you." / "You used to be scared of thunder. You still are." / hero says "Nobody alive knew that."
- Later ideas: calls him "kiddo" once; knows the scarf was a birthday gift; signs a text with a nickname only dad used;
  the white-suit man at the bridge keeps a photo of a kid with an orange scarf; same handwriting on the map.

## Narration rules (from Tomer)
- First person ("I"), told as it happens — the narrator NEVER knows what's coming (no "the day before the world ended",
  no "forever", no "one last time", no "nobody alive"). Reactions only: "How did it know that?"
- Part 1 opens: "At 7:25 AM, November 6th, I was watching videos on my phone... when an unknown number texted me."
  Opening shot is first-person POV: my hands holding my phone, a video playing, the text banner drops in.

## Part 1 beats (Day 0 → Day 30)
Hook (7:25 AM, Nov 6, POV phone): "At midnight, the world ends. Do exactly what I say, and you'll live." → "You're wearing the orange scarf right now."
Day 0 ("Don't go to school today") store (coughing cashier, yellow eyes) → lock door at 11:58 → 11:59 emergency alert → screaming.
Rule 1 (don't open the door, not even for people you know) → Day 3 Mr. Hale at the peephole → "Don't." → he turns.
Rule 2 (roof, 3 AM) → drone drops a crate: radio, flashlight, map with the bridge circled, "DAY 30".
Day 12 power dies → Rule 3 (they're drawn to light) → flashlight across the street goes out forever.
Day 18 HELIX trucks + men in white suits COLLECTING zombies → one looks up → "GET DOWN. NOW."
Day 23 "Why are you helping me?" → "Because I owe you." → "Who ARE you" → thunder clue.
Day 29 "Tomorrow. 6 AM. Get to the bridge. Don't stop. Don't look back." → phone at 1%.
Day 30 chase → empty bridge → "Turn around." → a man in a white suit (HELIX) → phone dies.
CTA: "Who is the unknown number? Comment your guess. Follow for Part 2."

## Part 2 starts
The white-suit man at the bridge. Is he the texter, or HELIX hunting the texter? (He is a HELIX guard;
the dad arranged for him to be there but he double-crosses / or helps.) Keep the dad hidden.

## Production notes
- Narrator: ElevenLabs "Angelo Marcello" (1LdBU508nR8vgkGDFHqP), model eleven_v4_turbo, via Speko.
- Unknown number voice: ROBOT / voice-changer (Tomer's pick). OpenAI "onyx" (gpt-4o-mini-tts) with instructions
  "cold, emotionless AI, flat deep monotone", then robot FX in audio_unk.py (52 Hz ring mod + metallic comb + buzz carrier
  + light bit-crush). Keep it the SAME every part. Story reason: the dad uses a voice changer so HELIX can't identify him —
  the finale can drop the effect to reveal his real voice.
- Texts shown in a dark-mode phone UI ("Unknown Number / No Caller ID"), hero's replies in orange bubbles.
- HELIX: teal (#28D2C4) hexagon logo with a double helix; white suits with teal glowing visors.
- Code: unk1.py (scenes), timeline.py (voice cutting + timing), audio_unk.py (score/SFX). Reuses ../stick100/rig.py + world.py.

## Tension rules (Part 1 "tense cut" — use in every part)
- Frame 1 must already be scary/intriguing (the text banner slams in with a BRAAM). Nothing calm in the first 2 seconds.
- Narrator: ElevenLabs eleven_v3 with audio tags ([whispers], [scared], [breathing heavily], [panicked]), slightly sped up, long pauses squeezed.
- Jump scares (~1 per 45 s, never more): build tension → near-total SILENCE (only heartbeat) → misdirect/fake-out → face slam + screech stinger + flash.
  Part 1: JS1 cashier face slam · JS2 empty peephole fake-out → neighbor's face slams the lens · JS3 lightning reveals a zombie at the window (gone on the next flash, handprints left) · JS4 "Turn around" → nothing there → turns back → white suit's hand on his shoulder.
- Big RULE #N cards, red "MIDNIGHT IN" countdown, red heartbeat pulse in danger moments, constant nervous handheld camera.
