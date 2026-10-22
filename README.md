# 🎵 Music Recommender Simulation

## Project Summary

**VibeFinder 1.0** is a small, CLI-first music recommender. It loads a 20-song catalog from `data/songs.csv`, scores every song against a user's "taste profile" (favorite genre, favorite mood, target energy, and whether they like acoustic music), and prints the top 5 songs with a table of *reasons* for each score. Beyond the starter features it uses five extra attributes (popularity, release decade, mood tags, instrumentalness, language), four switchable ranking modes and an optional artist-diversity penalty.

---

## How The System Works

### How real-world recommenders work

Platforms like Spotify and YouTube mix two big ideas:

- **Collaborative filtering** uses *other people's behavior*. If many people who liked songs A and B also liked song C, then C is recommended to you. It needs no knowledge of the music itself, only a big matrix of user–item interactions: **likes, skips, replays, saves, playlist adds, watch/listen time, searches, and follows**. Skips and finishing a track are strong *implicit* signals; a like is an *explicit* one.
- **Content-based filtering** uses *the attributes of the item*. For music these are things like **genre, mood, tempo (BPM), energy, valence (positivity), danceability, acousticness**, plus audio analysis, lyrics and text. It recommends songs that look like what you already liked, so it works even for brand-new songs nobody has played yet (the "cold start" problem that collaborative filtering struggles with).

Real systems combine both, then **rank** candidates (often with a learned model) and apply extra rules such as freshness and variety. The pipeline is: *input data* (song features and user history) → *user preferences* (a taste profile inferred from behavior) → *ranking/selection* (score candidates, sort, show the top few).

**My version is purely content-based.** I have no other users, so there is no collaborative filtering. It prioritizes matching genre first, then mood, then how *close* a song's energy is to what the user wants, with a small bonus for acoustic fit.

### Features used

**`Song`** (from `songs.csv`): `id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness`, plus five extra attributes: `popularity` (0-100), `release_decade`, `mood_tags` (e.g. `retro;late-night;dreamy`), `instrumentalness` (0-1) and `language`. Scoring uses `genre`, `mood`, `energy`, `acousticness` and all five extras (and `artist` for the diversity penalty). Tempo, valence and danceability are loaded but unused so far.

**`UserProfile`** / prefs dict: `favorite_genre` (`genre`), `favorite_mood` (`mood`), `target_energy` (`energy`), `likes_acoustic`. Optional: `favorite_decade` (`decade`), `favorite_tags` (`tags`), `target_popularity` (`popularity`), `likes_instrumental`, `language`. Optional prefs are skipped when absent, so a simple profile is scored exactly as before.

### Algorithm Recipe (the Scoring Rule, for one song)

| Rule | Points (balanced mode) |
|---|---|
| Genre matches | +2.0 |
| Mood matches | +1.0 |
| Energy closeness: `1.0 × (1 − abs(song.energy − target))` | 0 to +1.0 |
| Acoustic fit: `0.5 × acousticness` if user likes acoustic, else `0.5 × (1 − acousticness)` | 0 to +0.5 |
| *Optional:* decade matches | +0.5 |
| *Optional:* each shared mood tag | +0.5 per tag |
| *Optional:* popularity closeness: `0.5 × (1 − abs(diff) / 100)` | 0 to +0.5 |
| *Optional:* instrumental fit (same idea as acoustic fit) | 0 to +0.5 |
| *Optional:* language matches | +0.5 |

Energy uses *distance from the target*, not "higher is better", so a user who wants 0.35 energy is not pushed toward a 0.95 song. Genre is worth more than mood because it is a broader, harder boundary (a metal fan rarely wants a lullaby no matter the mood), while mood is more flexible and overlaps across genres.

**Ranking Rule (for the whole list):** score every song in the catalog, sort by score high→low, and return the top *k*. We need both rules because the scoring rule only says how good *one* song is in isolation; the ranking rule turns those independent numbers into an ordered list and chooses which few to show.

### Data flow

```
Input: user prefs  ──►  Process: loop over all 20 songs, score_song() → (score, reasons)
                        (optional: artist-repeat penalty while picking)
                    ──►  Output: sort by score, return top K with reasons
```

### Ranking modes (Strategy pattern)

Select with `--mode`. Each mode is just a different set of weights passed to the same scoring code.

| Mode | Weights (genre / mood / energy / acoustic) |
|---|---|
| `balanced` (default) | 2.0 / 1.0 / 1.0 / 0.5 |
| `genre_first` | 4.0 / 1.0 / 1.0 / 0.5 |
| `mood_first` | 2.0 / 3.0 / 1.0 / 0.5 |
| `energy_focused` | 1.0 / 1.0 / 2.0 / 0.5 |

### Diversity / fairness component

`--diversity` re-picks the list greedily and subtracts **0.75 points for each song already picked from the same artist**, so one artist cannot fill the whole list. The reason shows up in the table (`repeat-artist penalty (-0.75)`).

### Expected biases

- Genre is the biggest single weight, so great songs in a *neighboring* genre (e.g. "indie pop" for a "pop" fan) get no genre credit at all, because matching is exact string equality.
- Only one favorite genre and one mood are allowed per user.
- With 20 songs, most genres have only one or two songs, so the "top 5" quickly runs out of real matches and is filled by energy proximity.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app (from the project root):

```bash
python3 -m src.main                          # all profiles, balanced mode
python3 -m src.main --mode genre_first       # balanced | genre_first | mood_first | energy_focused
python3 -m src.main --diversity              # artist-repeat penalty
python3 -m src.main --profile "Chill Lofi"   # only one profile
```

### Running Tests

```bash
pytest
```

---

## Sample Recommendation Output

Default `balanced` mode, all six profiles (the first three are "normal" users, then two adversarial edge cases, then one profile that uses the extra attributes):

```
Loaded songs: 20

=== Happy Pop (default) | genre=pop, mood=happy, energy=0.8, acoustic=False | mode=balanced ===
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| #   | Title          | Artist        | Score   | Reasons                                                      |
+=====+================+===============+=========+==============================================================+
| 1   | Sunrise City   | Neon Echo     | 4.39    | genre match (+2.0); mood match (+1.0); energy 0.82 vs target |
|     |                |               |         | 0.80 (+0.98); non-acoustic fit (+0.41)                       |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 2   | Gym Hero       | Max Pulse     | 3.35    | genre match (+2.0); energy 0.93 vs target 0.80 (+0.87); non- |
|     |                |               |         | acoustic fit (+0.47)                                         |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 3   | Rooftop Lights | Indigo Parade | 2.29    | mood match (+1.0); energy 0.76 vs target 0.80 (+0.96); non-  |
|     |                |               |         | acoustic fit (+0.33)                                         |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 4   | Concrete Crown | Verse Theory  | 1.42    | energy 0.78 vs target 0.80 (+0.98); non-acoustic fit (+0.44) |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 5   | Neon Bodega    | Calle Fuego   | 1.36    | energy 0.84 vs target 0.80 (+0.96); non-acoustic fit (+0.40) |
+-----+----------------+---------------+---------+--------------------------------------------------------------+

=== Chill Lofi | genre=lofi, mood=chill, energy=0.35, acoustic=True | mode=balanced ===
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| #   | Title               | Artist         | Score   | Reasons                                                      |
+=====+=====================+================+=========+==============================================================+
| 1   | Library Rain        | Paper Lanterns | 4.43    | genre match (+2.0); mood match (+1.0); energy 0.35 vs target |
|     |                     |                |         | 0.35 (+1.00); acoustic fit (+0.43)                           |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| 2   | Midnight Coding     | LoRoom         | 4.29    | genre match (+2.0); mood match (+1.0); energy 0.42 vs target |
|     |                     |                |         | 0.35 (+0.93); acoustic fit (+0.35)                           |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| 3   | Focus Flow          | LoRoom         | 3.34    | genre match (+2.0); energy 0.40 vs target 0.35 (+0.95);      |
|     |                     |                |         | acoustic fit (+0.39)                                         |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| 4   | Spacewalk Thoughts  | Orbit Bloom    | 2.39    | mood match (+1.0); energy 0.28 vs target 0.35 (+0.93);       |
|     |                     |                |         | acoustic fit (+0.46)                                         |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| 5   | Coffee Shop Stories | Slow Stereo    | 1.43    | energy 0.37 vs target 0.35 (+0.98); acoustic fit (+0.45)     |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+

=== Deep Intense Rock | genre=rock, mood=intense, energy=0.92, acoustic=False | mode=balanced ===
+-----+-----------------+---------------+---------+--------------------------------------------------------------+
| #   | Title           | Artist        | Score   | Reasons                                                      |
+=====+=================+===============+=========+==============================================================+
| 1   | Storm Runner    | Voltline      | 4.44    | genre match (+2.0); mood match (+1.0); energy 0.91 vs target |
|     |                 |               |         | 0.92 (+0.99); non-acoustic fit (+0.45)                       |
+-----+-----------------+---------------+---------+--------------------------------------------------------------+
| 2   | Gym Hero        | Max Pulse     | 2.46    | mood match (+1.0); energy 0.93 vs target 0.92 (+0.99); non-  |
|     |                 |               |         | acoustic fit (+0.47)                                         |
+-----+-----------------+---------------+---------+--------------------------------------------------------------+
| 3   | Pulse Cathedral | Kaleid        | 1.44    | energy 0.96 vs target 0.92 (+0.96); non-acoustic fit (+0.48) |
+-----+-----------------+---------------+---------+--------------------------------------------------------------+
| 4   | Iron Requiem    | Black Lantern | 1.44    | energy 0.97 vs target 0.92 (+0.95); non-acoustic fit (+0.48) |
+-----+-----------------+---------------+---------+--------------------------------------------------------------+
| 5   | Neon Bodega     | Calle Fuego   | 1.32    | energy 0.84 vs target 0.92 (+0.92); non-acoustic fit (+0.40) |
+-----+-----------------+---------------+---------+--------------------------------------------------------------+

=== Sad but High-Energy | genre=folk, mood=melancholy, energy=0.9, acoustic=True | mode=balanced ===
+-----+---------------------+---------------+---------+--------------------------------------------------------------+
| #   | Title               | Artist        | Score   | Reasons                                                      |
+=====+=====================+===============+=========+==============================================================+
| 1   | Porch Light Promise | Willow & Ash  | 3.87    | genre match (+2.0); mood match (+1.0); energy 0.30 vs target |
|     |                     |               |         | 0.90 (+0.40); acoustic fit (+0.47)                           |
+-----+---------------------+---------------+---------+--------------------------------------------------------------+
| 2   | Static Bloom        | Neon Echo     | 1.92    | mood match (+1.0); energy 0.68 vs target 0.90 (+0.78);       |
|     |                     |               |         | acoustic fit (+0.14)                                         |
+-----+---------------------+---------------+---------+--------------------------------------------------------------+
| 3   | Storm Runner        | Voltline      | 1.04    | energy 0.91 vs target 0.90 (+0.99); acoustic fit (+0.05)     |
+-----+---------------------+---------------+---------+--------------------------------------------------------------+
| 4   | Neon Bodega         | Calle Fuego   | 1.04    | energy 0.84 vs target 0.90 (+0.94); acoustic fit (+0.10)     |
+-----+---------------------+---------------+---------+--------------------------------------------------------------+
| 5   | Rooftop Lights      | Indigo Parade | 1.03    | energy 0.76 vs target 0.90 (+0.86); acoustic fit (+0.17)     |
+-----+---------------------+---------------+---------+--------------------------------------------------------------+

=== Unknown Genre (k-pop) | genre=k-pop, mood=happy, energy=0.8, acoustic=False | mode=balanced ===
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| #   | Title          | Artist        | Score   | Reasons                                                      |
+=====+================+===============+=========+==============================================================+
| 1   | Sunrise City   | Neon Echo     | 2.39    | mood match (+1.0); energy 0.82 vs target 0.80 (+0.98); non-  |
|     |                |               |         | acoustic fit (+0.41)                                         |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 2   | Rooftop Lights | Indigo Parade | 2.29    | mood match (+1.0); energy 0.76 vs target 0.80 (+0.96); non-  |
|     |                |               |         | acoustic fit (+0.33)                                         |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 3   | Concrete Crown | Verse Theory  | 1.42    | energy 0.78 vs target 0.80 (+0.98); non-acoustic fit (+0.44) |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 4   | Neon Bodega    | Calle Fuego   | 1.36    | energy 0.84 vs target 0.80 (+0.96); non-acoustic fit (+0.40) |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 5   | Gym Hero       | Max Pulse     | 1.34    | energy 0.93 vs target 0.80 (+0.87); non-acoustic fit (+0.47) |
+-----+----------------+---------------+---------+--------------------------------------------------------------+

=== Retro Late-Night Instrumental | genre=synthwave, mood=moody, energy=0.6, acoustic=False | mode=balanced ===
+-----+--------------------+-------------+---------+--------------------------------------------------------------+
| #   | Title              | Artist      | Score   | Reasons                                                      |
+=====+====================+=============+=========+==============================================================+
| 1   | Night Drive Loop   | Neon Echo   | 6.94    | genre match (+2.0); mood match (+1.0); energy 0.75 vs target |
|     |                    |             |         | 0.60 (+0.85); non-acoustic fit (+0.39); 1980s era match      |
|     |                    |             |         | (+0.5); mood tags retro/late-night (+1.00); popularity 70 vs |
|     |                    |             |         | target 50 (+0.40); instrumental fit (+0.30); language match: |
|     |                    |             |         | none (+0.5)                                                  |
+-----+--------------------+-------------+---------+--------------------------------------------------------------+
| 2   | Static Bloom       | Neon Echo   | 6.00    | genre match (+2.0); energy 0.68 vs target 0.60 (+0.92); non- |
|     |                    |             |         | acoustic fit (+0.36); 1980s era match (+0.5); mood tags      |
|     |                    |             |         | retro/late-night/dreamy (+1.50); popularity 51 vs target 50  |
|     |                    |             |         | (+0.49); instrumental fit (+0.23)                            |
+-----+--------------------+-------------+---------+--------------------------------------------------------------+
| 3   | Spacewalk Thoughts | Orbit Bloom | 3.15    | energy 0.28 vs target 0.60 (+0.68); non-acoustic fit         |
|     |                    |             |         | (+0.04); mood tags dreamy/late-night (+1.00); popularity 40  |
|     |                    |             |         | vs target 50 (+0.45); instrumental fit (+0.47); language     |
|     |                    |             |         | match: none (+0.5)                                           |
+-----+--------------------+-------------+---------+--------------------------------------------------------------+
| 4   | Midnight Coding    | LoRoom      | 2.86    | energy 0.42 vs target 0.60 (+0.82); non-acoustic fit         |
|     |                    |             |         | (+0.15); mood tags late-night (+0.50); popularity 55 vs      |
|     |                    |             |         | target 50 (+0.47); instrumental fit (+0.42); language match: |
|     |                    |             |         | none (+0.5)                                                  |
+-----+--------------------+-------------+---------+--------------------------------------------------------------+
| 5   | Focus Flow         | LoRoom      | 2.35    | energy 0.40 vs target 0.60 (+0.80); non-acoustic fit         |
|     |                    |             |         | (+0.11); popularity 50 vs target 50 (+0.50); instrumental    |
|     |                    |             |         | fit (+0.44); language match: none (+0.5)                     |
+-----+--------------------+-------------+---------+--------------------------------------------------------------+
```

---

## Experiments You Tried

### Experiment 1: weight shift (halve genre, double energy)

Mode `energy_focused` (genre 2.0 → 1.0, energy 1.0 → 2.0). Math check: for a basic profile the maximum possible score goes from 2.0 + 1.0 + 1.0 + 0.5 = 4.5 to 1.0 + 1.0 + 2.0 + 0.5 = 4.5, so scores stay comparable.

```
=== Happy Pop (default) | genre=pop, mood=happy, energy=0.8, acoustic=False | mode=energy_focused ===
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| #   | Title          | Artist        | Score   | Reasons                                                      |
+=====+================+===============+=========+==============================================================+
| 1   | Sunrise City   | Neon Echo     | 4.37    | genre match (+1.0); mood match (+1.0); energy 0.82 vs target |
|     |                |               |         | 0.80 (+1.96); non-acoustic fit (+0.41)                       |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 2   | Rooftop Lights | Indigo Parade | 3.25    | mood match (+1.0); energy 0.76 vs target 0.80 (+1.92); non-  |
|     |                |               |         | acoustic fit (+0.33)                                         |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 3   | Gym Hero       | Max Pulse     | 3.22    | genre match (+1.0); energy 0.93 vs target 0.80 (+1.74); non- |
|     |                |               |         | acoustic fit (+0.47)                                         |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 4   | Concrete Crown | Verse Theory  | 2.40    | energy 0.78 vs target 0.80 (+1.96); non-acoustic fit (+0.44) |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
| 5   | Neon Bodega    | Calle Fuego   | 2.32    | energy 0.84 vs target 0.80 (+1.92); non-acoustic fit (+0.40) |
+-----+----------------+---------------+---------+--------------------------------------------------------------+
```

**What changed:** For Happy Pop, *Gym Hero* (pop, but intense and louder than wanted) dropped from #2 to #3 and *Rooftop Lights* (indie pop, happy, energy 0.76) moved up to #2. That feels **more accurate**, since the user asked for *happy*, and Gym Hero only ever matched on genre and energy.

```
=== Sad but High-Energy | genre=folk, mood=melancholy, energy=0.9, acoustic=True | mode=energy_focused ===
+-----+---------------------+--------------+---------+--------------------------------------------------------------+
| #   | Title               | Artist       | Score   | Reasons                                                      |
+=====+=====================+==============+=========+==============================================================+
| 1   | Porch Light Promise | Willow & Ash | 3.27    | genre match (+1.0); mood match (+1.0); energy 0.30 vs target |
|     |                     |              |         | 0.90 (+0.80); acoustic fit (+0.47)                           |
+-----+---------------------+--------------+---------+--------------------------------------------------------------+
| 2   | Static Bloom        | Neon Echo    | 2.70    | mood match (+1.0); energy 0.68 vs target 0.90 (+1.56);       |
|     |                     |              |         | acoustic fit (+0.14)                                         |
+-----+---------------------+--------------+---------+--------------------------------------------------------------+
| 3   | Storm Runner        | Voltline     | 2.03    | energy 0.91 vs target 0.90 (+1.98); acoustic fit (+0.05)     |
+-----+---------------------+--------------+---------+--------------------------------------------------------------+
| 4   | Neon Bodega         | Calle Fuego  | 1.98    | energy 0.84 vs target 0.90 (+1.88); acoustic fit (+0.10)     |
+-----+---------------------+--------------+---------+--------------------------------------------------------------+
| 5   | Gym Hero            | Max Pulse    | 1.96    | energy 0.93 vs target 0.90 (+1.94); acoustic fit (+0.03)     |
+-----+---------------------+--------------+---------+--------------------------------------------------------------+
```

**What changed:** For the "sad but high-energy" profile, the quiet folk song is still #1 on genre+mood alone even though its energy (0.30) is far from 0.9; doubling energy narrows the gap to the next songs but doesn't flip it. This is the system *failing to resolve conflicting preferences* — see the model card.

### Experiment 2: artist diversity penalty (Chill Lofi)

```
=== Chill Lofi | genre=lofi, mood=chill, energy=0.35, acoustic=True | mode=balanced + diversity ===
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| #   | Title               | Artist         | Score   | Reasons                                                      |
+=====+=====================+================+=========+==============================================================+
| 1   | Library Rain        | Paper Lanterns | 4.43    | genre match (+2.0); mood match (+1.0); energy 0.35 vs target |
|     |                     |                |         | 0.35 (+1.00); acoustic fit (+0.43)                           |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| 2   | Midnight Coding     | LoRoom         | 4.29    | genre match (+2.0); mood match (+1.0); energy 0.42 vs target |
|     |                     |                |         | 0.35 (+0.93); acoustic fit (+0.35)                           |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| 3   | Focus Flow          | LoRoom         | 2.59    | genre match (+2.0); energy 0.40 vs target 0.35 (+0.95);      |
|     |                     |                |         | acoustic fit (+0.39); repeat-artist penalty (-0.75)          |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| 4   | Spacewalk Thoughts  | Orbit Bloom    | 2.39    | mood match (+1.0); energy 0.28 vs target 0.35 (+0.93);       |
|     |                     |                |         | acoustic fit (+0.46)                                         |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
| 5   | Coffee Shop Stories | Slow Stereo    | 1.43    | energy 0.37 vs target 0.35 (+0.98); acoustic fit (+0.45)     |
+-----+---------------------+----------------+---------+--------------------------------------------------------------+
```

**What changed:** *Focus Flow* (second LoRoom song) was docked 0.75 (3.34 → 2.59) but still holds #3 because there are so few lofi songs. The list is the same, but the score is more honest about the repetition. With a bigger catalog this would reorder results.

### Other observations

- **Genre-first bias:** in `genre_first` mode a pop fan with a low energy target still gets a pop song on top (covered by `test_ranking_modes_change_results`).
- **Extra attributes at work:** the *Retro Late-Night Instrumental* profile uses era, mood tags, popularity, instrumentalness and language. Its top two (*Night Drive Loop* and *Static Bloom*, both 1980s synthwave) score 6.94 and 6.00, far above the rest (3.15 and below). *Spacewalk Thoughts* (ambient, no genre or mood match) reaches #3 purely on tags, instrumentalness and language, which a genre-and-mood-only system would never have surfaced.
- The **unknown-genre** profile (k-pop) never earns genre points, so every score drops by 2.0 and the list is driven by mood + energy only.

---

## Limitations and Risks

- Tiny catalog (20 songs); many genres have only one song.
- Exact string match on genre and mood: "indie pop" ≠ "pop", "chill" ≠ "relaxed".
- Ignores lyrics (it only knows the *language* label), tempo, valence and danceability. Popularity is a single number, so it can't tell *why* a song is popular.
- The extra attributes (mood tags, decade) were filled in by hand for 20 songs, so they reflect my guesses, not real data.
- No listening history, so no collaborative filtering and no learning over time.
- Conflicting preferences (sad + high energy) are not resolved sensibly.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

The biggest thing I learned is that a recommender isn't magic. It's a score sheet. You give points for a match, you give points for being close, you add it all up and sort. Even with just a few rules it already felt like real recommendations, mostly because I could print the reasons next to each song. The weights are the part that surprised me, because picking "genre is worth double mood" sounds like math but it's really just my opinion, and it shaped everything the system did.

Bias showed up fast. When I ran the "happy pop" profile, Gym Hero kept sneaking into the top 3 even though it's not really a happy song, just a loud pop one. That made it clear how a system can look right while still missing the vibe. In a real app, the same thing would happen at a huge scale, with whatever genres or artists have the most data getting pushed the most, and people getting stuck in a bubble.
