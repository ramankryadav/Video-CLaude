"""Fit a Hindi voiceover onto the English voiceover's timing, sentence by sentence.

usage: python sync_hindi.py en_whisper.json hi_whisper.json EN_script.txt HI_script.txt hi.wav en.wav out.wav

Each Hindi sentence k starts where English sentence k starts (the visual cut). The pause after it
absorbs the difference first; speech is time-stretched (Rubber Band via ffmpeg, pitch/formant
preserved) only when needed: at most MAX_FAST faster, MAX_SLOW slower. Output = exact English length.
Writes sync_report.tsv next to out.wav. Sentences that still spill need a shorter Hindi box.
"""
import json, re, sys, difflib, subprocess, os, tempfile
import numpy as np, soundfile as sf

MAX_FAST, MAX_SLOW, MIN_GAP, LONG_GAP = 1.12, 1.04, 0.12, 0.90

def sentences(path):
    out = []
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"): continue
        t = re.sub(r"\[[^\]]*\]", " ", line)
        parts = [p.strip() for p in re.split(r"(?<=[.?!।])\s+", t.strip()) if p.strip()]
        assert len(parts) == 3, f"{path}: box without 3 sentences: {line[:60]}"
        out += parts
    return out

def norm(w, hindi):
    w = w.lower().replace("’", "'")
    if hindi: return re.sub(r"[^ऀ-ॿ0-9a-z]", "", w.replace("़", "")).replace("।", "")
    return re.sub(r"[^a-z0-9]", "", w)

def sentence_times(wjson, sents, hindi):
    raw = json.load(open(wjson, encoding="utf-8"))
    ww = [dict(w, k=norm(w["word"], hindi)) for s in raw["segments"] for w in s["words"]]; ww = [w for w in ww if w["k"]]
    sw, owner = [], []
    for i, s in enumerate(sents):
        for tok in s.split():
            k = norm(tok, hindi)
            if k: sw.append(k); owner.append(i)
    sm = difflib.SequenceMatcher(None, [w["k"] for w in ww], sw, autojunk=False)
    t = [None] * len(sw)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for d in range(i2 - i1): t[j1 + d] = (ww[i1 + d]["start"], ww[i1 + d]["end"])
        elif op == "replace":
            a, b = ww[i1]["start"], ww[i2 - 1]["end"]; n = j2 - j1
            for d in range(n): t[j1 + d] = (a + (b - a) * d / n, a + (b - a) * (d + 1) / n)
    known = [i for i, x in enumerate(t) if x]
    for i in range(len(t)):
        if t[i] is None:
            p = max([k for k in known if k < i], default=None); q = min([k for k in known if k > i], default=None)
            a = t[p][1] if p is not None else 0.0; b = t[q][0] if q is not None else a + 0.3
            t[i] = (a, a + (b - a) * 0.5)
    res = []
    for i in range(len(sents)):
        idx = [j for j, o in enumerate(owner) if o == i]
        res.append((t[idx[0]][0], t[idx[-1]][1]))
    match = sum(i2 - i1 for op, i1, i2, j1, j2 in sm.get_opcodes() if op == "equal") / max(len(sw), 1)
    return res, match

def stretch(x, sr, tempo):
    if abs(tempo - 1) < 0.005: return x
    d = tempfile.mkdtemp(); a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
    sf.write(a, x, sr)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a, "-af",
                    f"rubberband=tempo={tempo:.5f}:pitchq=quality:transients=smooth:formant=preserved", b], check=True)
    y, _ = sf.read(b, dtype="float32"); return y

def main(enj, hij, ens, his, hiwav, enwav, outwav):
    en_s, hi_s = sentences(ens), sentences(his)
    assert len(en_s) == len(hi_s), f"sentence count differs: EN {len(en_s)} HI {len(hi_s)} (run check_pair.py)"
    E, em = sentence_times(enj, en_s, False); H, hm = sentence_times(hij, hi_s, True)
    print(f"sentences {len(E)} | word match EN {em:.0%} HI {hm:.0%} (HI below ~60% = check the Hindi transcript)")
    hi, sr = sf.read(hiwav, dtype="float32")
    if hi.ndim > 1: hi = hi.mean(axis=1)
    en_len = sf.info(enwav).duration
    out = np.zeros(int(round(en_len * sr)), dtype="float32"); rows, cursor = [], 0.0
    for k in range(len(E)):
        s0, s1 = H[k]; speech = hi[int(s0 * sr):int(s1 * sr)]; S = s1 - s0
        slot_end = E[k + 1][0] if k + 1 < len(E) else en_len
        # never demand a wider gap than the English itself has at this joint
        gap_k = min(MIN_GAP, max(slot_end - E[k][1], 0.02)) if k + 1 < len(E) else MIN_GAP
        gap_prev = min(MIN_GAP, max(E[k][0] - E[k - 1][1], 0.02)) if k else 0.0
        start = max(E[k][0], cursor + gap_prev) if k else E[k][0]
        avail = slot_end - start - gap_k; tempo = 1.0
        if S > avail: tempo = min(S / max(avail, 0.05), MAX_FAST)
        elif avail - S > LONG_GAP: tempo = max(S / (avail - LONG_GAP + S), 1 / MAX_SLOW)
        y = stretch(speech, sr, tempo)
        a = int(round(start * sr)); b = min(a + len(y), len(out)); out[a:b] += y[:b - a]
        cursor = start + len(y) / sr
        rows.append((k, E[k][0], start, tempo, cursor - (slot_end - gap_k), hi_s[k]))
    sf.write(outwav, out, sr, subtype="PCM_16")
    rep = os.path.join(os.path.dirname(os.path.abspath(outwav)), "sync_report.tsv")
    with open(rep, "w", encoding="utf-8") as f:
        f.write("box\tsentence\ten_start\thi_start\ttempo\tspill_s\thindi\n")
        for k, es, hs, tp, dr, txt in rows: f.write(f"{k//3+1:03d}\t{k%3+1}\t{es:.2f}\t{hs:.2f}\t{tp:.3f}\t{max(dr,0):.2f}\t{txt}\n")
    late = [r for r in rows if r[4] > 0.05]
    print(f"output {len(out)/sr:.2f}s = english {en_len:.2f}s | max tempo {max(r[3] for r in rows):.3f} | sped up >5%: {sum(r[3]>1.05 for r in rows)} | still spilling: {len(late)}")
    for k, es, hs, tp, dr, txt in late[:40]: print(f"  box {k//3+1:03d}.{k%3+1} at {es:7.2f}s needs {dr:+.2f}s more -> shorten | {txt[:70]}")
    print("report:", rep)

if __name__ == "__main__":
    main(*sys.argv[1:8])
