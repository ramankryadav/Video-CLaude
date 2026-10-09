"""Word-timestamp transcription with faster-whisper (English or Hindi).

usage: python transcribe.py <audio_or_video> --lang en|hi [--model medium.en] [--out words.json] [--prompt "names..."]
Writes {"segments":[{start,end,text,words:[{word,start,end,probability}]}]}.
VAD is OFF on purpose: it once dropped a whole spoken box.
Run long jobs detached (PowerShell Start-Process -WindowStyle Hidden).
"""
import argparse, json, os, subprocess, tempfile
from faster_whisper import WhisperModel

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("--lang", default="en")
ap.add_argument("--model"); ap.add_argument("--out"); ap.add_argument("--prompt", default=None)
a = ap.parse_args()
model = a.model or ("medium.en" if a.lang == "en" else "medium")
out = a.out or os.path.splitext(a.src)[0] + f"_{a.lang}_whisper.json"
wav = os.path.join(tempfile.mkdtemp(), "a.wav")
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.src, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
m = WhisperModel(model, device="cpu", compute_type="int8")
kw = dict(beam_size=5, word_timestamps=True, vad_filter=False)
if a.lang != "en" or not model.endswith(".en"): kw["language"] = a.lang
if a.prompt: kw["initial_prompt"] = a.prompt
segs, info = m.transcribe(wav, **kw)
data = {"language": a.lang, "segments": [{"start": s.start, "end": s.end, "text": s.text,
        "words": [{"word": w.word, "start": w.start, "end": w.end, "probability": w.probability} for w in s.words]} for s in segs]}
json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print(out, len(data["segments"]), "segments")
