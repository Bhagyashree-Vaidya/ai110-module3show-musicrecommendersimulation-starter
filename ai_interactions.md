# AI Interactions Log

> Stretch-feature notes only. Written after the work, from what was actually done in this session.

---

## Agentic Workflow (SF8)

**What task did you give the agent?**

Build the whole Music Recommender project end to end from the Phase 1–5 instructions: expand the dataset, implement `load_songs`, `score_song`, `recommend_songs`, a CLI table, tests, the README, and the model card.

**Prompts used:**

> "try" (with the full assignment pasted: phases 1–5, rubric, stretch features)

**What did the agent generate or change?**

- `data/songs.csv`: added 10 songs (ids 11–20) in new genres and moods.
- `src/recommender.py`: CSV loading with numeric conversion, `score_song` returning `(score, reasons)`, `recommend_songs` with sorting, mode and diversity options, the `Recommender` class for the starter tests, and docstrings.
- `src/main.py`: five user profiles (3 normal, 2 adversarial), argparse options, a `tabulate` grid table.
- `tests/test_recommender.py`: 6 new tests.
- `README.md`, `model_card.md`: filled in with the real terminal output.
- `requirements.txt`: added `tabulate`.

**What did you verify or fix manually?**

- The starter `main.py` used `from recommender import ...`, which fails under `python -m src.main`; changed to `from src.recommender import ...`.
- Ran `python3 -m src.main` and `pytest` (8 passing) and pasted the real output into the docs.
- Checked claims in the docs against the output (e.g. that Gym Hero moves from #2 to #3 in the energy-focused experiment, and that the folk song still wins for the conflicted profile).
- **Personal reflection:** first drafted by the agent, then rewritten in the user's own casual voice (README and model card) on request.
- **Still for you to do:** check that the numbers in the docs match your own runs, then commit and push, and make sure the repo is public.

---

## Additional Song Attributes via Agentic AI (SF7)

**Task given:** "Skipped stretch: do it", meaning add 5+ meaningful attributes to the dataset and update the scoring consistently.

**Prompt (paraphrased):** Add five new attributes to `data/songs.csv` (popularity 0-100, release decade, detailed mood tags, instrumentalness, language) and wire them into loading, `Song`/`UserProfile`, `score_song`, the CLI and the tests, without changing results for profiles that don't use them.

**What the agent changed:**
- `data/songs.csv`: 5 new columns for all 20 songs, filled by hand-picked values (so they are guesses, not real streaming data).
- `src/recommender.py`: the loader now parses ints, floats and the `;`-separated tag list; `Song` and `UserProfile` got defaulted fields so the starter tests still work; `ScoringStrategy` got 5 new weights; `score_song` got five optional rules (era match, +0.5 per shared tag, popularity closeness, instrumental fit, language match), each with its own reason string.
- `src/main.py`: a sixth profile, "Retro Late-Night Instrumental", that uses all five.
- `tests/test_recommender.py`: 4 new tests (types after loading, new reasons appear, extras change the ranking, plain profiles ignore extras).
- Docs: README, model card.

**Manual verification:**
- Diffed the output of the original five profiles before and after: byte-identical, so existing behaviour was preserved.
- Confirmed the Retro profile's reasons list every new attribute and that the scores add up (e.g. Night Drive Loop: 2.0 + 1.0 + 0.85 + 0.39 + 0.5 + 1.00 + 0.40 + 0.30 + 0.5 = 6.94).
- Noticed tabulate was printing `6.00` as `6`; fixed with `disable_numparse=True`.
- `pytest`: 12 passing.
- **Known weakness:** tags and decades were assigned by the agent as plausible guesses; a human should review them.

---

## Design Pattern (SF10)

**Which design pattern did you use?**

**Strategy pattern.** `ScoringStrategy` is a frozen dataclass holding the weights; `STRATEGIES` maps mode names (`balanced`, `genre_first`, `mood_first`, `energy_focused`) to instances. `score_song` and `recommend_songs` take a strategy/mode, and `--mode` in `main.py` switches between them.

**How did AI help you brainstorm or implement it?**

The assistant chose Strategy over subclasses or `if/else` branches because the modes differ only in numbers, not in behaviour. A weights object keeps `score_song` as one function, makes adding a mode a one-line change, and keeps the "doubled energy, halved genre" experiment easy to run.
