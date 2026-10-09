# Adapting the English script into Hindi (box for box)

The Hindi version has to sync onto a video cut for the English VO. The video changes picture **per sentence**, so the only hard requirement is: **Hindi box N = English box N, sentence k = sentence k.** The words inside a sentence can be in any order.

## Parity rules (check_pair.py enforces them)
- The same `## ` sections in the same order (headings translated), the same box count, exactly **3 sentences per box**, ending in `।`, `?` or `!`.
- **Identical tags** at the same positions: `[natural pace]`, tone tags, `[0.3s]` pauses. Keep the English tag words; Vids reads them as instructions. If the Hindi voice reads tags aloud, the user removes them, and that's the only allowed difference.
- No sentence may move from one box to another, even if it would read better.

## Register: spoken Hindi, not textbook Hindi
- Write the way a good Hindi YouTube narrator talks (Dhruv Rathee / Mohak Mangal register). Use simple conversational Hindi plus the English words Indians actually say: चिप्स, एडवांस, लॉन्च पैड, ट्विस्ट, सीक्रेट, बिज़नेस, कंपनी, सेंसरशिप, प्रोपेगेंडा, एक्सपर्ट्स.
- **Everything in Devanagari:** English loanwords too (टी एस एम सी, कोल्ड वॉर, मार्शल लॉ), so the Hindi voice pronounces them in Hindi. No Latin letters and no digits.
- Avoid heavy Sanskritised words when a common word exists: ज़मीन, not भूमि; मदद, not सहायता (unless it fits).
- Keep the hooks punchy: "ये है ताइवान।", "और फिर आया ट्विस्ट।", "ज़रा सोचिए।", "तो चलिए, करीब से देखते हैं…".

## Numbers, dates, units, money
- **Years in spoken Hindi words:** 1624 → सोलह सौ चौबीस, 1949 → उन्नीस सौ उनचास, 2016 → दो हज़ार सोलह.
- **Big numbers in the Indian system:** 23 million → दो करोड़ तीस लाख; 500 million → पचास करोड़; hundreds of thousands → लाखों.
- **Distances in kilometres:** 100 miles → करीब एक सौ साठ किलोमीटर. Feet → metres, unless it's a famous fixed phrase.
- **Money stays in dollars**, spoken: $200,000 → दो लाख डॉलर; $2 million → बीस लाख डॉलर. Don't convert currencies. Don't use a ₹ conversion unless the story is set in India.
- Dates: "सत्ताईस फ़रवरी उन्नीस सौ सैंतालीस".

## Length control (the sync depends on this)
- Measured on Taiwan: the Hindi VO came out **6.4% longer** than the English (16:56 vs 15:55), and sync can absorb that. Aim for the **same or up to 5% longer** spoken length.
- Hindi grows through filler: "जो कि", "इस बात का", "के द्वारा", stacked "और". Cut them.
- A long English sentence can become two short Hindi clauses joined by a comma, but it stays **one sentence**.
- Text-based estimates of Hindi length are unreliable (schwa deletion). `check_pair.py` only flags boxes far above the median ratio; the real check is the recorded audio (`sync_hindi.py` report).

## Names and terms
- Use the standard Hindi spelling of names as Indian media writes them: च्यांग काई-शेक, माओ ज़ेडॉन्ग, कॉक्सिंगा, फ़र्डिनेंड डी लेसेप्स.
- Hedges keep their meaning: "reportedly" → कहा जाता है कि; "an estimated" → अनुमान के मुताबिक़; "many linguists believe" → कई भाषा विशेषज्ञ मानते हैं.
- The ending question and the subscribe line get translated naturally: "तो आपको क्या लगता है…? कमेंट्स में बताइए, और अगली लंबी कहानी के लिए सब्सक्राइब कीजिए।"

## Hindi title
Write the Hindi title in the same format: "[X] का पूरा इतिहास [N] मिनट में". Also offer a Hinglish Latin-script version for YouTube search, for example "Taiwan Ka Poora Itihaas".
