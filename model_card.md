# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Goal / Intended Use

VibeFinder suggests the top 5 songs from a small catalog for one user, based on a taste profile: favorite genre, favorite mood, target energy, and whether they like acoustic music. It also says *why* each song was picked.

- **Intended use:** classroom exploration of how recommenders turn data into rankings.
- **Not intended for:** real users, real music apps, or any decision that affects people or artists. The catalog is far too small, and the taste profile is far too simple.

---

## 3. How the Model Works

Think of it as a judge with a score sheet. For each song, the judge gives points:

- **+2.0** if the genre is the user's favorite genre.
- **+1.0** if the mood is the user's favorite mood.
- **Up to +1.0 for energy.** The closer the song's energy is to what the user wants, the more points. A song that is too *high* loses points just like one that is too *low*.
- **Up to +0.5 for acoustic fit.** Acoustic fans get points for acoustic songs; everyone else gets points for non-acoustic songs.
- **Optional bonuses (+0.5 each, only if the user asks for them):** the song's decade matches, each shared mood tag (like "retro" or "late-night"), popularity close to what the user wants, instrumental fit, and language match.

Then the system sorts all songs from highest score to lowest and shows the top 5, with the list of reasons that made up each score.

**Extras I added:**
- **Four ranking modes** (balanced, genre-first, mood-first, energy-focused). They use the same score sheet with different point values.
- **Artist-diversity penalty** (optional): each time a song from the same artist has already been picked, the next one from that artist loses 0.75 points.

**Changes from the starter:** the starter had empty functions; I wrote CSV loading, scoring with reasons, ranking, and the CLI table.

---

## 4. Data

- **20 songs** in `data/songs.csv` (10 from the starter, 10 I added).
- **Features:** genre, mood, energy, tempo_bpm, valence, danceability, acousticness (plus title and artist).
- **Five extra features I added:** popularity (0-100), release decade, mood tags (3 per song), instrumentalness (0-1) and language. I filled these in by hand, so they are my best guesses, not real streaming data.
- **Genres (16):** pop (2 songs), lofi (3 songs), synthwave (2 songs), and one song each for indie pop, rock, ambient, jazz, hip-hop, r&b, country, edm, metal, classical, folk, reggae and latin.
- **Moods:** happy, chill, intense, relaxed, moody, focused, confident, romantic, nostalgic, euphoric, angry, peaceful, melancholy, playful.
- **I added** 10 songs so the catalog covers genres and moods not in the starter file.
- **Missing:** lyrics, language, artist fame, release year, regional or cultural music, and anything about *who* listens to what.

---

## 5. Strengths

- Works well for users whose taste matches a well-covered genre and mood. *Chill Lofi* gets three lofi songs, then calm ambient and jazz tracks, which is what I'd expect.
- *Deep Intense Rock* gets *Storm Runner* first by a wide margin (4.44 vs 2.46).
- The reasons make every score checkable: you can see exactly why a song was picked.
- Energy uses closeness instead of "higher is better", so a calm-music fan is not shown loud songs.

---

## 6. Limitations and Bias

- **Genre dominates.** A genre match is worth 2.0, twice a mood match and twice a perfect energy match. Because matching is exact, "indie pop" gets no credit for a "pop" fan, even though *Rooftop Lights* is a great fit. It only appears at #3 because of its mood.
- **The Gym Hero problem.** For a user who wants *happy pop*, *Gym Hero* (pop, but "intense") ranks #2 above the happy indie-pop song. Its genre points (+2.0) and high energy outweigh the wrong mood. In plain words: the system sees "pop" and "loud", not "does this feel happy?".
- **Conflicting tastes break it.** A user who wants *melancholy folk* with *0.9 energy* gets a quiet folk song at #1 (energy 0.30), because genre + mood add to 3.0 while the energy mismatch only costs 0.6. Nothing in the system notices the contradiction.
- **Unknown genres lose 2.0 points.** The "k-pop" user can never get a genre match, so every song starts behind and the list is mostly energy-driven.
- **Hand-labelled extras.** Mood tags and decades are my guesses on 20 songs. A different person would tag them differently, and the Retro profile's results depend heavily on those tags.
- **Tiny catalog.** Most genres have one song, so once the one matching song is used, the rest of the top 5 is filled by whatever is closest in energy. That can look like a recommendation even when it is just a guess.
- **Diversity penalty is weak at this size.** In the lofi test the repeat artist was penalized but stayed at #3 because there were too few lofi songs to replace it.

---

## 7. Evaluation

**Profiles tested (6):**
1. Happy Pop (pop, happy, 0.8)
2. Chill Lofi (lofi, chill, 0.35, likes acoustic)
3. Deep Intense Rock (rock, intense, 0.92)
4. *Adversarial:* Sad but High-Energy (folk, melancholy, 0.9, likes acoustic)
5. *Adversarial:* Unknown Genre (k-pop, happy, 0.8)
6. Retro Late-Night Instrumental (synthwave, moody, 0.6, 1980s, tags retro/late-night/dreamy, instrumental, language none). This one tests the extra attributes.

I also ran: the weight-shift experiment (halve genre, double energy), the artist-diversity penalty, and automated tests (`pytest`, 12 tests: CSV loading, scoring, energy closeness, sorting, ranking modes, diversity, and the extra attributes).

**Pair comparisons:**
- **Happy Pop vs Chill Lofi:** Pop gets bright, danceable, high-energy songs (Sunrise City, Rooftop Lights, Neon Bodega). Lofi gets slow, acoustic songs (Library Rain, Midnight Coding, Spacewalk Thoughts). The energy target (0.8 vs 0.35) and the acoustic flag pull the lists to opposite ends of the catalog, which makes sense.
- **Happy Pop vs Deep Intense Rock:** Both want loud songs, so *Gym Hero* shows up in both. For Pop it's there because of genre; for Rock it's there because of its "intense" mood. Rock's list is much more lopsided (4.44 then 2.46) because there is only one rock song.
- **Chill Lofi vs Deep Intense Rock:** Complete opposites. They share no songs, which shows energy and acoustic fit are doing real work.
- **Happy Pop vs Unknown Genre (k-pop):** Same mood and energy, but without a genre match the pop songs lose their lead. Sunrise City is still #1 on mood + energy, but its score drops from 4.39 to 2.39, and *Gym Hero* falls from #2 to #5. Good: the system degrades gracefully rather than failing.
- **Retro Late-Night Instrumental vs Chill Lofi:** Both like quiet-ish, instrumental music, but they split. Retro gets 1980s synthwave on top (Night Drive Loop, Static Bloom) because of the era and tags, and Lofi gets lofi. They overlap on slower, instrumental tracks (Midnight Coding, Focus Flow) in the lower spots, which makes sense since both like instrumental music.
- **Sad but High-Energy vs Deep Intense Rock:** Both want high energy, but the sad profile's top pick is a quiet folk song and rock's is a loud rock song. This shows genre + mood can overpower energy.

**What surprised me:**
- *Gym Hero* keeps appearing for people who just want "Happy Pop". It is a pop song, so it gets the biggest bonus, and it is energetic, so it gets energy points too. The system never checks if it *feels* happy. It's like recommending a gym playlist to someone who asked for a birthday party mix because both are "pop" and "loud".
- Even four simple rules produce lists that "feel" right for the normal profiles.

**Experiment results:**
- *Weight shift* (energy ×2, genre ×½): the Happy Pop list got **more accurate** (Rooftop Lights up to #2, Gym Hero down to #3). For the conflicted profile, the list was only **different**, not better: the folk song still won.
- *Diversity penalty:* the artist repeat was penalized, but the order stayed the same because the catalog is tiny.

---

## 8. Future Work

- Add similarity for genres and moods (e.g. "indie pop" is close to "pop", "relaxed" is close to "chill") instead of exact matching.
- Use the features already in the data that I still ignore (valence, tempo, danceability) and let users give a *range* for energy.
- Add a rule that flags conflicting preferences, and use *must-have* vs *nice-to-have* preferences.
- Grow the catalog so there are several songs per genre, then re-test the diversity penalty.

---

## 9. Personal Reflection

**Biggest learning moment.** Seeing Gym Hero show up at #2 for a "happy pop" user. The code did exactly what I told it to, and it still felt wrong. That's when it clicked for me that the system doesn't understand music at all. It just follows the weights I picked, so the weights are basically my opinions written as numbers.

**How AI helped and where I had to double-check it.** The AI got me a working first version really fast: the code, the extra songs, the docs. But I couldn't just trust it. The starter main.py had an import that broke when I ran it the way the instructions said, so I had to fix that. I also checked the numbers in my README against what the terminal actually printed, because it's easy for a written summary to say something nicer than what really happened. The extra tags and decades were also guesses I had to sanity check, since they're not real data.

**What surprised me.** How little it takes to make something feel like a real recommendation. It's just adding points up, but once the reasons are printed next to each song, it feels smart and honest. Also, the extra attributes did more than I expected. Spacewalk Thoughts made it into a synthwave fan's list just from mood tags and being instrumental, which is the kind of thing real apps probably do too.

**What I'd try next.** Make genres and moods "close" to each other instead of exact match only, so indie pop counts a bit for a pop fan. I'd also use valence and tempo, grow the catalog a lot, and try a basic version of collaborative filtering with some fake users.
