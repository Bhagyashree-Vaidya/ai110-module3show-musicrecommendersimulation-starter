"""
Command line runner for the Music Recommender Simulation.

Usage:
    python -m src.main                      # all profiles, balanced mode
    python -m src.main --mode genre_first   # pick a ranking mode
    python -m src.main --diversity          # penalize repeat artists
"""

import argparse
import textwrap

from tabulate import tabulate

from src.recommender import STRATEGIES, load_songs, recommend_songs

PROFILES = {
    "Happy Pop (default)": {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.92, "likes_acoustic": False},
    # Adversarial profiles
    "Sad but High-Energy": {"genre": "folk", "mood": "melancholy", "energy": 0.9, "likes_acoustic": True},
    "Unknown Genre (k-pop)": {"genre": "k-pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False},
    # Uses the extra attributes (era, mood tags, popularity, instrumentalness, language)
    "Retro Late-Night Instrumental": {
        "genre": "synthwave", "mood": "moody", "energy": 0.6, "likes_acoustic": False,
        "decade": 1980, "tags": ["retro", "late-night", "dreamy"], "popularity": 50,
        "likes_instrumental": True, "language": "none",
    },
}


def show(name: str, prefs: dict, songs: list, mode: str, diversity: bool, k: int = 5) -> None:
    """Print one profile's top-k results as a table with reasons."""
    print(f"\n=== {name} | genre={prefs['genre']}, mood={prefs['mood']}, "
          f"energy={prefs['energy']}, acoustic={prefs['likes_acoustic']} "
          f"| mode={mode}{' + diversity' if diversity else ''} ===")
    rows = []
    for rank, (song, score, why) in enumerate(
        recommend_songs(prefs, songs, k=k, mode=mode, diversity=diversity), start=1
    ):
        rows.append([rank, song["title"], song["artist"], f"{score:.2f}", textwrap.fill(why, 60)])
    print(tabulate(rows, headers=["#", "Title", "Artist", "Score", "Reasons"], tablefmt="grid", disable_numparse=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("--mode", choices=sorted(STRATEGIES), default="balanced")
    parser.add_argument("--diversity", action="store_true", help="penalize repeat artists")
    parser.add_argument("--profile", help="run only the profile whose name contains this text")
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for name, prefs in PROFILES.items():
        if args.profile and args.profile.lower() not in name.lower():
            continue
        show(name, prefs, songs, args.mode, args.diversity)


if __name__ == "__main__":
    main()
