# After the user records the voiceovers

Vids exports an MP4 per project, usually `Downloads\Untitled video (N).mp4`. **Check the audio stream duration, not the container:** one export had a silent video tail of 115 s.

## 1. Transcribe (word timestamps)
```
python scripts/transcribe.py "<vo_en.mp4>" --lang en --out en_whisper.json --prompt "<names from the script>"
python scripts/transcribe.py "<vo_hi.mp4>" --lang hi --out hi_whisper.json
```
- English: `medium.en` (good with names when you pass `--prompt`). Hindi: the multilingual `medium` (it's cached). Both run on CPU, about 5–10 min for 15 min of audio.
- Run long jobs **detached** (PowerShell `Start-Process -WindowStyle Hidden`). A Claude session restart kills background bash jobs.
- `vad_filter` is off on purpose: VAD once silently dropped a whole spoken box.

## 2. Fix the transcript and find VO mistakes
```
python scripts/align_transcript.py en_whisper.json VO_tagged_chunks.txt --out <project>/transcripts/en
```
- Every word gets the script's spelling ("Bounot-Verilla" → Bunau-Varilla, "Calabra" → Culebra, "$25" → twenty-five dollars) while keeping whisper's timing.
- Outputs `_word_timestamps.json` (sentence segments with words), `.srt`, `_transcript.txt`, `_fix_report.txt`.
- **The report's box check:** it finds any box the VO **skipped** or **repeated**. On Panama, box 41 was generated twice and box 42 was missing. Tell the user the exact cut (start and end seconds of the duplicate) and give them the box text to regenerate. After they fix it, re-run the transcription.
- Whisper quirks to ignore: a doubled last word at segment edges ("sleep. cheap."), or "Kyle," / "Because" hallucinated at box joins. Check against the audio before reporting a real problem.

## 3. Sync the Hindi onto the English timeline
```
python scripts/sync_hindi.py en_whisper.json hi_whisper.json VO_tagged_chunks.txt VO_tagged_chunks_HINDI.txt vo_hi.wav vo_en.wav Hindi_synced.wav
```
- Extract the WAVs first: `ffmpeg -i vo.mp4 -vn -ac 1 -ar 48000 vo.wav`.
- **Per sentence:** the Hindi starts exactly where the English sentence starts (the visual cut). The gap after it shrinks to a minimum of 0.12 s, or grows. Speech is stretched with Rubber Band (pitch- and formant-preserving, from ffmpeg's `rubberband` filter): at most 12% faster, at most 4% slower. If a gap would grow beyond 0.9 s, the speech is slowed slightly instead.
- The output is exactly as long as the English VO. `sync_report.tsv` lists the tempo and spill for each sentence.
- **For a sentence that still spills** (it needed more than 12%): rewrite that Hindi box shorter, have the user regenerate only that box, splice it in, and re-run.
- **Deliver:**
  - `Hindi_synced.wav`
  - a muxed MP4 if a video exists: `ffmpeg -i video.mp4 -i Hindi_synced.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k out_hi.mp4`
  - a mention of YouTube's multi-language audio track: Studio → Languages → add audio track, if the channel has it. It needs the same length, which the sync guarantees.

## 4. Loudness for the final master
`-14 LUFS / -1 dBTP`: `ffmpeg -i in.wav -af loudnorm=I=-14:TP=-1:LRA=11 -ar 48000 out.wav`. Apply the same settings to both languages.
