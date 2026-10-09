"""Re-spell a whisper transcript with the script's words (keeping whisper's timing) and
detect boxes the VO skipped or repeated.

usage: python align_transcript.py whisper.json VO_tagged_chunks.txt --out <prefix> [--hindi]
writes <prefix>_word_timestamps.json, <prefix>.srt, <prefix>_transcript.txt, <prefix>_fix_report.txt
"""
import argparse, json, re, difflib

ap = argparse.ArgumentParser()
ap.add_argument("whisper"); ap.add_argument("script"); ap.add_argument("--out", required=True)
ap.add_argument("--hindi", action="store_true")
a = ap.parse_args()
H = a.hindi

def key(t):
    t = t.lower().replace("’", "'")
    if H: return re.sub(r"[^ऀ-ॿ0-9a-z]", "", t.replace("़", "")).replace("।", "")
    return re.sub(r"[^a-z0-9]", "", t)

# script words with box / sentence ownership
boxes = [re.sub(r"\[[^\]]*\]", " ", l).strip() for l in open(a.script, encoding="utf-8") if l.strip() and not l.startswith("#")]
sw = []
for b, line in enumerate(boxes):
    for tok in line.split():
        sw.append({"text": tok, "box": b, "end": bool(re.search(r"[.?!।][\"')]*$", tok)), "key": key(tok)})
sw = [w for w in sw if w["key"]]

raw = json.load(open(a.whisper, encoding="utf-8"))
ww = [dict(w, key=key(w["word"])) for s in raw["segments"] for w in s["words"]]
ww = [w for w in ww if w["key"]]

# --- duplicate / missing box detection: locate every box's word run in the whisper stream
wk = [w["key"] for w in ww]
def find_runs(seq, pat, min_ratio=0.75):
    n = len(pat); hits = []
    if n < 4: return hits
    i = 0
    while i + n <= len(seq):
        r = difflib.SequenceMatcher(None, seq[i:i + n], pat, autojunk=False).ratio()
        if r >= min_ratio:
            # refine: slide around i to the best-matching start
            best = max(range(max(0, i - n // 4), min(len(seq) - n, i + n // 4) + 1),
                       key=lambda j: difflib.SequenceMatcher(None, seq[j:j + n], pat, autojunk=False).ratio())
            hits.append((best, r)); i = best + n
        else: i += max(1, n // 6)
    return hits
report = []
for b in range(len(boxes)):
    pat = [w["key"] for w in sw if w["box"] == b]
    hits = find_runs(wk, pat)
    if len(hits) == 0: report.append(f"MISSING  box {b + 1:03d}: not found in the audio -> regenerate it | {boxes[b][:80]}")
    elif len(hits) > 1:
        spans = [f"{ww[i]['start']:.2f}-{ww[min(i + len(pat), len(ww)) - 1]['end']:.2f}s" for i, _ in hits]
        report.append(f"REPEATED box {b + 1:03d}: heard {len(hits)} times at {', '.join(spans)} -> cut the extra copy | {boxes[b][:60]}")

# --- word alignment for timings
sm = difflib.SequenceMatcher(None, wk, [w["key"] for w in sw], autojunk=False)
out = [None] * len(sw); fixes = []
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == "equal":
        for d in range(i2 - i1): out[j1 + d] = (ww[i1 + d]["start"], ww[i1 + d]["end"], "match")
    elif op == "replace":
        t0, t1 = ww[i1]["start"], ww[i2 - 1]["end"]; L = [max(len(sw[j]["key"]), 1) for j in range(j1, j2)]; tot = sum(L); acc = t0
        for j, l in zip(range(j1, j2), L):
            d = (t1 - t0) * l / tot; out[j] = (acc, acc + d, "fixed"); acc += d
        fixes.append(f"fixed    {t0:8.2f}s heard {' '.join(w['word'].strip() for w in ww[i1:i2])!r} -> {' '.join(sw[j]['text'] for j in range(j1, j2))!r}")
    elif op == "delete":
        fixes.append(f"extra    {ww[i1]['start']:8.2f}s heard {' '.join(w['word'].strip() for w in ww[i1:i2])!r} (not in script)")
i = 0
while i < len(out):
    if out[i] is None:
        j = i
        while j < len(out) and out[j] is None: j += 1
        t0 = out[i - 1][1] if i else 0.0; t1 = out[j][0] if j < len(out) else t0 + 0.3 * (j - i); st_ = (t1 - t0) / (j - i)
        for k in range(i, j): out[k] = (t0 + st_ * (k - i), t0 + st_ * (k - i + 1), "interpolated")
        i = j
    else: i += 1

words = [{"word": sw[k]["text"], "start": round(out[k][0], 3), "end": round(out[k][1], 3), "source": out[k][2]} for k in range(len(sw))]
segs, cur = [], []
for k, w in enumerate(words):
    cur.append(w)
    if sw[k]["end"]: segs.append({"start": cur[0]["start"], "end": cur[-1]["end"], "box": sw[k]["box"] + 1, "text": " ".join(x["word"] for x in cur), "words": cur}); cur = []
if cur: segs.append({"start": cur[0]["start"], "end": cur[-1]["end"], "box": sw[-1]["box"] + 1, "text": " ".join(x["word"] for x in cur), "words": cur})
json.dump({"segments": segs}, open(a.out + "_word_timestamps.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def ts(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"
with open(a.out + ".srt", "w", encoding="utf-8") as f:
    for n, s in enumerate(segs, 1): f.write(f"{n}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text']}\n\n")
open(a.out + "_transcript.txt", "w", encoding="utf-8").write("\n".join(f"[{ts(s['start'])[:8]}] (box {s['box']:03d}) {s['text']}" for s in segs))
summary = f"script words {len(sw)} | heard {len(ww)} | matched {sum(w['source']=='match' for w in words)} | fixed {sum(w['source']=='fixed' for w in words)} | interpolated {sum(w['source']=='interpolated' for w in words)}"
with open(a.out + "_fix_report.txt", "w", encoding="utf-8") as f:
    f.write(summary + "\n\nBOX CHECK\n" + ("\n".join(report) if report else "every box heard exactly once") + "\n\nWORD FIXES\n" + "\n".join(fixes) + "\n")
print(summary); print("\n".join(report) if report else "box check: every box heard exactly once")
