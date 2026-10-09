# Research, references and fact-checking

## Studying a reference video the user sends
1. Get its metadata and the channel's upload list from the YouTube Data API. The key is `YT_API_KEY` in `~/.claude/skills/map-shorts-studio/.credentials.env`. Check whether that channel already made our topic. GoDocs had already made a Panama video, so ours took the history angle instead of engineering.
2. **Transcript:** yt-dlp subtitles and timedtext usually fail (HTTP 429 / empty, even in the logged-in Chrome). What works:
   - `yt-dlp -f "bv*[height<=480]+ba/b[height<=480]/worst" -o ref.%(ext)s <url>`
   - then `scripts/transcribe.py ref.webm --lang en --model small.en` (about 3 min for 11 min of audio on CPU)
3. **Measure:** words per minute (words ÷ minutes), hook length, structure beats, sentence length, recurring phrases, and how it ends.
4. **Frames:** `ffmpeg -i ref.webm -vf "fps=1/15,scale=320:-1,tile=6x8" -frames:v 1 frames.jpg` shows the visual style for the image team.
5. Copy the **structure and devices, never the wording or the title.**

## Facts
- Build a fact sheet before writing: each date, number, name and place, marked ✓ (sure) or ? (verify).
- Verify every "?" with web search. Cite the sources to the user at the end, with links.
- **Money math in Python, always:** compound growth, inflation adjustment (e.g. 3%/yr), tax brackets, benefit cuts. Say the honest version in the script ("in 2026 money, roughly…").
- **Hedge wording** for anything not certain: "reportedly", "according to a famous story", "supposedly", "an estimated", "later official estimates put…", "many linguists believe", "some historians argue".
- Prefer widely documented numbers (official estimates, government reports) and give ranges where historians disagree (the 228 Incident: "between eighteen and twenty-eight thousand").

## Neutrality and advertiser safety
- For disputed places (Taiwan, Panama, Israel and so on), state what each side says, plus the facts. No "rightful owner" language, and no predicted wars.
- Wars are told at map level: no gore, no torture detail.
- Present-day politicians: mention their public statements in neutral words ("an American president said publicly that…").
- This keeps the video ad-friendly and stops the comments from turning into a fight.

## Title screening (before writing)
- Documentary: `python ~/.claude/skills/entire-history-studio/scripts/publish/yt_research.py comps "entire history of X"` gives the existing versions, their views and their age.
- POV stories: run a similarity check against the niche titles (difflib ratio ≥ 0.8 to an earlier post = don't publish). See the `pov-wealth-niche` memory.
