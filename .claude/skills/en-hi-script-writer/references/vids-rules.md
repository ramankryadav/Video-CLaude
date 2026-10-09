# Google Vids box and tag rules (the user's fixed rules)

These rules come from the vids-voiceover-designer skill. They override every general text-to-speech habit.

| Rule | Value |
|---|---|
| Pace | Only `[natural pace]`, placed at the start of each section's first box. Never `[slow pace]` or `[rushed pace]`. |
| Pauses | Numbers only: `[0.3s]` between ordinary sentences, `[0.4s]` before a turn or a number, `[0.5s]` before a reveal, a rule line or a punchline. **Never more than 0.5 s.** Never `[short/medium/long pause]`. |
| Whisper | Never `[whisper]`. |
| Box | Exactly **3 sentences**, at least **15 spoken words**, one line per box. Keep boxes under ~65 words (long boxes lag in Vids). |
| Headings | `## Section name (years)` lines (not spoken). |

**Allowed tags** (exact and lowercase; anything else gets read aloud):
- Emotion: admiration, adoration, amused, awe, confusion, curiosity, determination, enthusiasm, excited, frustrated, happy, hope, interest, positive, surprised, thoughtful
- Style: authoritative, bold, cautious, natural, sarcasm, serious (shouting and robotic almost never)
- Sounds (at most ~1 per 10 boxes): swallow, inhale, clear throat, gasp, shush, urgh, snorts, giggles

**Mapping tags to beats** (don't run one tag more than 3 boxes in a row):

| Beat | Tag |
|---|---|
| Numbers, money mechanics, reveals | `[serious]`, `[authoritative]` |
| Lessons, reflection | `[thoughtful]` |
| A doubter's flex, gentle jokes, irony | `[sarcasm]`, `[amused]` |
| Questions, open loops | `[curiosity]`, `[interest]` |
| Twists | `[surprised]`, `[awe]` |
| Turning points | `[hope]`, `[determination]` |
| Temptation, bad news | `[cautious]` |
| Setbacks | `[frustrated]` |
| A mentor's quiet praise, heroes | `[admiration]` |
| Outro | `[positive]`, `[happy]` |
| The opener "This is X." | `[bold]` |

**Text-to-speech wording:**
- Spell numbers out the way they're spoken; years and clock times can stay as digits in English.
- Write T S M C, Mister, Doctor, percent and dollars as words.
- No quote marks: dialogue goes in as reported speech ("Two hundred grand, he says, that's six years").
- No `$ % & /`.

**The validator** is `scripts/build_vo.py <file> --title … --voice Zeno|Hindi --out page.html`. It fails on any rule break and prints the runtime at 150 / 145 / 134 wpm. Use the 150 figure: the real Zeno pace is ~152.
