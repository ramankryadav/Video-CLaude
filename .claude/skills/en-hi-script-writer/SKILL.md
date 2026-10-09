---
name: en-hi-script-writer
description: Write a complete voiceover script for the user's YouTube videos in TWO languages. The ENGLISH version is written first, then a HINDI version is adapted from it box-for-box so both voiceovers can be synced to the same video. Output is Google Vids-ready (3-sentence boxes with tags) plus copy/done pages. It carries every formula from the user's past scripts. One is "The ENTIRE History of X" fast documentary formula for The Long Story channel (Panama Canal, Taiwan; modelled on GoDocs). The other is the second-person POV money-story formula for POV Secret / Counter Finance (Whitlock old-money generations, Landlord rules, Grandpa's house, Dad Left at 9, Retired with $200K). Use this whenever the user asks to write, make or draft a script for a video, asks for "the script like our previous ones", gives a topic or title and wants the VO text, asks for a Hindi version or a Hindi script of a video, or wants English and Hindi scripts together. Use it even if they only say "script for <topic>" or "next video script". Also use it after recording, to fix transcription errors against the script, find skipped or duplicated boxes, or sync the Hindi VO to the English timing.
---

# English + Hindi script writer

The user makes faceless long-form videos and voices them in **Google Vids** (English voice **Zeno**, plus a Hindi voice), one box at a time. This skill writes the script in English first, then adapts it into Hindi **box for box**: same number of boxes, same 3 sentences, same tags, same story beat in each box. Because every picture in the video changes per sentence, matching boxes and sentences is what makes the Hindi VO sync onto the same video without looking dubbed.

## Which formula?

| User says / channel | Formula | Reference |
|---|---|---|
| "ENTIRE History of …", a country, empire, canal, megaproject; The Long Story channel | **Documentary formula** (GoDocs-style, fast, third person) | `references/formula-documentary.md`, examples `taiwan_EN.txt`, `panama_EN.txt` |
| "POV: …", old money, retirement, family money, inheritance, a mentor with rules; POV Secret / Counter Finance | **POV story formula** (second person, cinematic, one family or person, a recurring object) | `references/formula-pov-story.md`, example `landlord_pov_EN.txt` |

If the formula is unclear, ask in one line. Otherwise, pick and say which one you used.

## Workflow

### 1. Lock the inputs
- Topic and title, target length (default **15 min** for documentaries, **25–30 min** for POV stories), and a reference video or script if the user gives one.
- If they give a YouTube reference, study it: transcribe it, measure words per minute, and copy its hook, its structure and its ending. See `references/research-and-facts.md`. YouTube caption downloads usually 429 here, so download the video and use faster-whisper.
- If no topic is given, suggest one with evidence (the entire-history-studio / viral-topic-finder research), not from intuition.

### 2. Research and verify facts BEFORE writing
- Build a short fact sheet: dates, numbers, names, places. Verify anything you're not sure of with web search.
- Run every money calculation in Python (for example compound growth or tax arithmetic). Viewers check the math in the comments.
- Hedge anything uncertain, and keep geopolitics neutral. The rules are in `references/research-and-facts.md`.

### 3. Write the ENGLISH script, already in Vids boxes
- Follow the formula reference exactly: hook, structure, recurring devices, ending.
- Write straight into the box format: one line per box, exactly **3 sentences**, at least **15 words**, `## ` headings per section. Tag rules are in `references/vids-rules.md`.
- **Length budget:** Zeno reads at about **150–154 spoken words per minute** (measured: Panama 2,289 words = 889 s; Taiwan 2,347 words = 955 s). So 15 min ≈ **2,250–2,300 words**, 20 min ≈ 3,050, 30 min ≈ 4,500.
- Save as `<project>/VO_tagged_chunks.txt`. Validate:
  ```
  python ~/.claude/skills/en-hi-script-writer/scripts/build_vo.py VO_tagged_chunks.txt --title "<title>" --voice Zeno --out "<scratchpad>/<slug>-en-vo.html"
  ```
  Fix every error until `RESULT: OK`. If you're more than 5% off the target length, add or cut whole story beats; never pad sentences.

### 4. Adapt the HINDI script from the English
- Read `references/hindi-adaptation.md` first. It's not a literal translation; it's spoken Hindi of the same length, box for box.
- Save as `<project>/VO_tagged_chunks_HINDI.txt`, then check the pair:
  ```
  python ~/.claude/skills/en-hi-script-writer/scripts/check_pair.py VO_tagged_chunks.txt VO_tagged_chunks_HINDI.txt
  python ~/.claude/skills/en-hi-script-writer/scripts/build_vo.py VO_tagged_chunks_HINDI.txt --title "<Hindi title> (Hindi VO)" --voice Hindi --out "<scratchpad>/<slug>-hi-vo.html"
  ```
  `check_pair.py` must report equal box counts, identical tags per box, 3 sentences each (`।` counts), no digits or Latin letters left in the Hindi, and the per-box length ratio. Shorten any box flagged as too long.

### 5. Publish both pages
Publish both HTML pages as Artifacts (`icon: "microphone"`). Then report:
- both links and the file paths
- box count and word count for each language, and the estimated runtime (words ÷ 152)
- the reference used, the fact checks done, and anything hedged

### 6. After the user records (when they send the VO files)
- **Fix the transcript** for each language: `scripts/align_transcript.py` (faster-whisper word timestamps, re-spelled from the script). It reports any **skipped or duplicated box**. This happened on Panama: one box was generated twice and the next one was missing. Tell the user the exact cut points and the box text to regenerate.
- **Sync the Hindi to the English**: `scripts/sync_hindi.py`. Each Hindi sentence starts where its English sentence starts (the visual cut). Pauses absorb differences first, then pitch-preserved Rubber Band stretching up to 12% faster or 4% slower. It writes a report of sentences that still spill over; rewrite only those boxes shorter. See `references/after-recording.md`.
- Measured on Taiwan: English 15:55, Hindi 16:56 (+6.4%). Most sentences fit through the pauses alone.

## Non-negotiables (each one cost a redo before)
- **The English is the source of truth.** Never change the English after the Hindi exists without updating the same Hindi box.
- **Box parity:** box N in Hindi = box N in English, the same 3 sentences in the same order. Sync depends on it.
- **No digits in the voiceover text.** Write numbers the way they're spoken ("twenty-three million", "सोलह सौ चौबीस"). Years may stay as digits in English, but never in Hindi.
- **No abbreviations or symbols:** write T S M C, Mister, percent and dollars as words; no `$`, `%`, `&`, `/` or quote marks.
- **Neutral and advertiser-safe:** facts and each side's claims, no predicted wars, no gore. Avoid lines Vids refuses: it refused "$240K + worst night of your life", so have a plain fallback.
- **Hedge uncertain history:** "reportedly", "according to a famous story", "an estimated", "many linguists believe".
- **No "woman/women" problems in scripts:** that word only matters for Flow image prompts, not for scripts, so don't rewrite scripts for it.

## Files
- `references/formula-documentary.md`: The Long Story / GoDocs formula with section templates, hook lines, ending, and pacing numbers.
- `references/formula-pov-story.md`: the POV money-story formula (cold-open timestamp, generations or levels, recurring object, doubter, mentor rules, honest math, twist, outro).
- `references/hindi-adaptation.md`: how to write the Hindi box by box (register, loanwords, numbers, units, length control, tags).
- `references/vids-rules.md`: the user's fixed Vids tag rules and tag-to-beat mapping.
- `references/research-and-facts.md`: topic and reference research, fact verification, hedging, neutrality, title screening.
- `references/after-recording.md`: transcription, transcript fixing, duplicate/missing box detection, Hindi sync, delivery.
- `scripts/build_vo.py`: validator and page builder (English and Hindi, `।`-aware).
- `scripts/check_pair.py`: English↔Hindi parity and length check.
- `scripts/align_transcript.py`: a whisper JSON plus the script → corrected word timestamps, SRT, and a report of missing or duplicated boxes.
- `scripts/sync_hindi.py`: fits the Hindi VO onto the English timeline sentence by sentence.
- `scripts/transcribe.py`: faster-whisper word timestamps (en / hi).
- `examples/`: `taiwan_EN.txt` + `taiwan_HI.txt` (a matched pair), `panama_EN.txt`, `landlord_pov_EN.txt`.
