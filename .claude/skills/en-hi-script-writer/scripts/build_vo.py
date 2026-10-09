"""Validate a tagged Google Vids voiceover file and build the copy/done chunk page.

Input format (plain text, UTF-8):
    ## Section title
    [natural pace] [serious] Sentence one. [0.4s] Sentence two. [0.3s] Sentence three.
    [thoughtful] Next box...

One non-empty line = one box. Lines starting with "## " start a new section.

Usage:
    python build_vo.py tagged.txt --title "Video title" --out page.html
        [--voice Zeno] [--sentences 3] [--min-words 15] [--max-pause 0.5]
        [--allow-tag TAG ...] [--json chunks.json]

Exit code 1 if any hard rule fails (the page is still written so you can look).
"""
import argparse, json, re, sys, os, unicodedata

PACE = {"natural pace"}  # slow pace / rushed pace are banned by the user's rules
EMOTION = {"admiration", "adoration", "amused", "awe", "confusion", "curiosity",
           "determination", "enthusiasm", "excited", "frustrated", "happy", "hope",
           "interest", "positive", "surprised", "thoughtful"}
STYLE = {"authoritative", "bold", "cautious", "natural", "robotic", "sarcasm",
         "serious", "shouting"}  # whisper is banned by the user's rules
SOUNDS = {"swallow", "inhale", "clear throat", "gasp", "shush", "urgh", "snorts", "giggles"}
BANNED = {"whisper", "slow pace", "rushed pace", "short pause", "medium pause", "long pause"}
ABBREV = ["Mr.", "Mrs.", "Ms.", "Dr.", "St.", "Jr.", "Sr.", "vs.", "etc.", "e.g.", "i.e.",
          "a.m.", "p.m.", "U.S.", "Inc.", "Co.", "No."]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:48] or "vo"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tagged")
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default="Zeno")
    ap.add_argument("--sentences", type=int, default=3)
    ap.add_argument("--min-words", type=int, default=15)
    ap.add_argument("--max-pause", type=float, default=0.5)
    ap.add_argument("--allow-tag", action="append", default=[],
                    help="extra tag the user explicitly allowed for this video")
    ap.add_argument("--json", help="also write the parsed boxes as JSON")
    a = ap.parse_args()

    allowed = PACE | EMOTION | STYLE | SOUNDS | set(a.allow_tag)
    secs, errors, warns = [], [], []
    words = 0
    pause_total = 0.0
    sounds = 0
    n = 0
    for ln, raw in enumerate(open(a.tagged, encoding="utf-8"), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("## "):
            secs.append({"t": line[3:].strip(), "c": []})
            continue
        if not secs:
            secs.append({"t": "Script", "c": []})
        n += 1
        where = f"box {n:03d} (line {ln})"
        for t in re.findall(r"\[([^\]]*)\]", line):
            m = re.fullmatch(r"(\d+(?:\.\d+)?)s", t)
            if m:
                v = float(m.group(1))
                pause_total += v
                if v > a.max_pause:
                    errors.append(f"{where}: pause [{t}] is longer than {a.max_pause}s")
            elif t in BANNED and t not in a.allow_tag:
                errors.append(f"{where}: banned tag [{t}]")
            elif t not in allowed:
                errors.append(f"{where}: unknown tag [{t}] (Vids would read it aloud)")
            elif t in SOUNDS:
                sounds += 1
        spoken = re.sub(r"\[[^\]]*\]\s*", "", line).strip()
        if not spoken:
            errors.append(f"{where}: no spoken text")
            continue
        if not line.startswith("["):
            warns.append(f"{where}: starts without a tone tag")
        countable = spoken
        for ab in ABBREV:
            if ab in countable:
                warns.append(f"{where}: abbreviation '{ab}' (spell it out for the voice)")
                countable = countable.replace(ab, ab.replace(".", ""))
        sc = len(re.findall(r"[.?!।](?=[\s\"')\]]|$)", countable))
        wc = len(spoken.split())
        if sc != a.sentences:
            errors.append(f"{where}: {sc} sentences, needs {a.sentences}: {spoken[:70]}...")
        if wc < a.min_words:
            errors.append(f"{where}: {wc} words, Vids needs at least {a.min_words}")
        if wc > 70:
            warns.append(f"{where}: {wc} words, long boxes can lag in Vids")
        if re.search(r"[\"“”]", spoken):
            warns.append(f"{where}: quote marks in spoken text")
        if re.search(r"\$\d[\d.,]*\s*[KMBkmb]\b|\d+%|&|/", spoken):
            warns.append(f"{where}: symbol or shorthand the voice may misread")
        words += wc
        secs[-1]["c"].append({"text": line, "words": wc})

    if n and sounds > max(1, n // 10):
        warns.append(f"{sounds} sound tags in {n} boxes (keep to about 1 per 10)")

    data = {"secs": [s for s in secs if s["c"]], "words": words}
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "chunk_page_template.html"),
               encoding="utf-8").read()
    short_title = a.title if len(a.title) <= 40 else a.title[:40].rsplit(" ", 1)[0]
    page = (tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
               .replace("__PAGETITLE__", (short_title + " VO").replace("&", "&amp;").replace("<", "&lt;"))
               .replace("__TITLE__", a.title.replace("&", "&amp;").replace("<", "&lt;"))
               .replace("__VOICESLUG__", slug(a.voice).replace("-", "_"))
               .replace("__VOICE__", a.voice.replace("<", "&lt;"))
               .replace("__SENT__", str(a.sentences))
               .replace("__KEY__", "vo-done-" + slug(a.title)))
    open(a.out, "w", encoding="utf-8").write(page)
    if a.json:
        json.dump(data, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"\n{n} boxes · {words} spoken words · {pause_total:.0f}s of pauses · {sounds} sound tags")
    for wpm in (150, 145, 134):
        print(f"  ~{words / wpm:.1f} min at {wpm} wpm")
    print("page:", a.out)
    print("RESULT:", "FAIL" if errors else "OK")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
