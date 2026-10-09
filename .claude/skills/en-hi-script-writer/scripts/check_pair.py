"""Check that a Hindi VO script matches its English source box for box.

usage: python check_pair.py VO_tagged_chunks.txt VO_tagged_chunks_HINDI.txt

Checks: same sections, same box count, identical tags per box, 3 sentences per box in both,
no digits / Latin letters left in the Hindi spoken text, and a per-box length ratio
(flagging boxes far longer than the script's typical ratio). Exit 1 on hard errors.
"""
import re, sys, statistics as st

TAG = re.compile(r"\[[^\]]*\]")

def load(path):
    secs, boxes = [], []
    for ln in open(path, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln.strip(): continue
        if ln.startswith("#"): secs.append(len(boxes)); continue
        boxes.append(ln.strip())
    return secs, boxes

def sentences(text):
    t = TAG.sub(" ", text)
    return [p for p in re.split(r"(?<=[.?!।])\s+", t.strip()) if p.strip()]

def syl_en(t):
    n = 0
    for w in re.findall(r"[a-zA-Z']+", t):
        g = len(re.findall(r"[aeiouy]+", w.lower()))
        if w.lower().endswith("e") and g > 1: g -= 1
        n += max(g, 1)
    return n

def syl_hi(t):
    # akshara count minus word-final inherent vowels (rough schwa deletion)
    n = 0
    for w in re.findall(r"[ऀ-ॿ]+", t):
        c = len(re.findall(r"[क-हक़-य़]", w)) - len(re.findall("्", w)) + len(re.findall(r"[अ-औ]", w))
        if re.search(r"[क-हक़-य़]$", w): c -= 0.5   # final consonant usually loses its vowel
        n += max(c, 1)
    return n

def main(en_path, hi_path):
    es, eb = load(en_path); hs, hb = load(hi_path)
    err, warn = [], []
    if es != hs: err.append(f"section starts differ: EN {es} vs HI {hs}")
    if len(eb) != len(hb): err.append(f"box count differs: EN {len(eb)} vs HI {len(hb)}")
    ratios = []
    for i, (e, h) in enumerate(zip(eb, hb), 1):
        if TAG.findall(e) != TAG.findall(h): err.append(f"box {i:03d}: tags differ\n   EN {TAG.findall(e)}\n   HI {TAG.findall(h)}")
        ne, nh = len(sentences(e)), len(sentences(h))
        if ne != 3: err.append(f"box {i:03d}: English has {ne} sentences")
        if nh != 3: err.append(f"box {i:03d}: Hindi has {nh} sentences")
        spoken = TAG.sub(" ", h)
        if re.search(r"\d", spoken): err.append(f"box {i:03d}: digits in Hindi (write numbers as words): {re.findall(r'[0-9][0-9,.]*', spoken)}")
        if re.search(r"[A-Za-z]", spoken): warn.append(f"box {i:03d}: Latin letters in Hindi: {re.findall(r'[A-Za-z]+', spoken)[:5]}")
        if re.search(r"[$%&/\"“”]", spoken): err.append(f"box {i:03d}: symbol or quote mark in Hindi")
        r = syl_hi(spoken) / max(syl_en(TAG.sub(' ', e)), 1); ratios.append(r)
    if ratios:
        med = st.median(ratios)
        for i, r in enumerate(ratios, 1):
            if r > med * 1.25: warn.append(f"box {i:03d}: Hindi looks long ({r / med:.2f}x the script's typical ratio), consider tightening")
        print(f"boxes EN {len(eb)} / HI {len(hb)} | median length ratio {med:.2f} (text estimate only; trust the recorded audio)")
    for w in warn: print("WARN ", w)
    for e in err: print("ERROR", e)
    print("RESULT:", "OK" if not err else f"{len(err)} error(s)")
    sys.exit(1 if err else 0)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
