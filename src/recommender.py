import csv
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Song:
    """A song and its attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: int = 50
    release_decade: int = 2020
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: float = 0.0
    language: str = "english"


@dataclass
class UserProfile:
    """A user's taste preferences."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Optional preferences for the extra attributes; None means "don't care".
    favorite_decade: Optional[int] = None
    favorite_tags: Optional[List[str]] = None
    target_popularity: Optional[int] = None
    likes_instrumental: Optional[bool] = None
    language: Optional[str] = None


@dataclass(frozen=True)
class ScoringStrategy:
    """A named set of weights; swapping strategies changes the ranking mode."""
    name: str
    genre_weight: float = 2.0
    mood_weight: float = 1.0
    energy_weight: float = 1.0
    acoustic_weight: float = 0.5
    decade_weight: float = 0.5
    tag_weight: float = 0.5  # per shared mood tag
    popularity_weight: float = 0.5
    instrumental_weight: float = 0.5
    language_weight: float = 0.5


# Ranking modes (Strategy pattern): same scoring code, different weights.
STRATEGIES: Dict[str, ScoringStrategy] = {
    "balanced": ScoringStrategy("balanced"),
    "genre_first": ScoringStrategy("genre_first", genre_weight=4.0),
    "mood_first": ScoringStrategy("mood_first", mood_weight=3.0),
    "energy_focused": ScoringStrategy("energy_focused", genre_weight=1.0, energy_weight=2.0),
}

ARTIST_PENALTY = 0.75  # points removed for each earlier pick by the same artist


def _song_to_dict(song: Song) -> Dict:
    """Convert a Song into the dict shape used by the functional API."""
    return {
        "id": song.id, "title": song.title, "artist": song.artist,
        "genre": song.genre, "mood": song.mood, "energy": song.energy,
        "tempo_bpm": song.tempo_bpm, "valence": song.valence,
        "danceability": song.danceability, "acousticness": song.acousticness,
        "popularity": song.popularity, "release_decade": song.release_decade,
        "mood_tags": song.mood_tags, "instrumentalness": song.instrumentalness,
        "language": song.language,
    }


def _profile_to_prefs(user: UserProfile) -> Dict:
    """Convert a UserProfile into the prefs dict used by score_song."""
    prefs = {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "energy": user.target_energy,
        "likes_acoustic": user.likes_acoustic,
    }
    optional = {
        "decade": user.favorite_decade,
        "tags": user.favorite_tags,
        "popularity": user.target_popularity,
        "likes_instrumental": user.likes_instrumental,
        "language": user.language,
    }
    prefs.update({k: v for k, v in optional.items() if v is not None})
    return prefs


class Recommender:
    """OOP wrapper around the scoring and ranking logic."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects for a user, best first."""
        by_id = {s.id: s for s in self.songs}
        ranked = recommend_songs(
            _profile_to_prefs(user), [_song_to_dict(s) for s in self.songs], k=k
        )
        return [by_id[song["id"]] for song, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-language reason string for one song."""
        _, reasons = score_song(_profile_to_prefs(user), _song_to_dict(song))
        return "; ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Read songs.csv into a list of dicts with numeric fields converted."""
    int_fields = ("id", "popularity", "release_decade")
    float_fields = ("energy", "tempo_bpm", "valence", "danceability", "acousticness", "instrumentalness")
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for key in int_fields:
                row[key] = int(row[key])
            for key in float_fields:
                row[key] = float(row[key])
            row["mood_tags"] = [t for t in row["mood_tags"].split(";") if t]
            songs.append(row)
    return songs


def score_song(
    user_prefs: Dict, song: Dict, strategy: Optional[ScoringStrategy] = None
) -> Tuple[float, List[str]]:
    """Score one song against user prefs; return (score, list of reasons)."""
    s = strategy or STRATEGIES["balanced"]
    score = 0.0
    reasons: List[str] = []

    if song["genre"] == user_prefs.get("genre"):
        score += s.genre_weight
        reasons.append(f"genre match (+{s.genre_weight:.1f})")

    if song["mood"] == user_prefs.get("mood"):
        score += s.mood_weight
        reasons.append(f"mood match (+{s.mood_weight:.1f})")

    if "energy" in user_prefs:
        # Closeness, not "higher is better": 1.0 at the target, 0.0 at the far end.
        gap = abs(song["energy"] - user_prefs["energy"])
        points = s.energy_weight * (1.0 - gap)
        score += points
        reasons.append(f"energy {song['energy']:.2f} vs target {user_prefs['energy']:.2f} (+{points:.2f})")

    if "likes_acoustic" in user_prefs:
        # Reward acoustic songs for fans, electronic ones for everyone else.
        fit = song["acousticness"] if user_prefs["likes_acoustic"] else 1.0 - song["acousticness"]
        points = s.acoustic_weight * fit
        score += points
        label = "acoustic" if user_prefs["likes_acoustic"] else "non-acoustic"
        reasons.append(f"{label} fit (+{points:.2f})")

    if "decade" in user_prefs and song["release_decade"] == user_prefs["decade"]:
        score += s.decade_weight
        reasons.append(f"{song['release_decade']}s era match (+{s.decade_weight:.1f})")

    if user_prefs.get("tags"):
        shared = [t for t in song["mood_tags"] if t in user_prefs["tags"]]
        if shared:
            points = s.tag_weight * len(shared)
            score += points
            reasons.append(f"mood tags {'/'.join(shared)} (+{points:.2f})")

    if "popularity" in user_prefs:
        # Same closeness idea as energy, on a 0-100 scale.
        points = s.popularity_weight * (1.0 - abs(song["popularity"] - user_prefs["popularity"]) / 100.0)
        score += points
        reasons.append(f"popularity {song['popularity']} vs target {user_prefs['popularity']} (+{points:.2f})")

    if "likes_instrumental" in user_prefs:
        fit = song["instrumentalness"] if user_prefs["likes_instrumental"] else 1.0 - song["instrumentalness"]
        points = s.instrumental_weight * fit
        score += points
        label = "instrumental" if user_prefs["likes_instrumental"] else "vocal"
        reasons.append(f"{label} fit (+{points:.2f})")

    if "language" in user_prefs and song["language"] == user_prefs["language"]:
        score += s.language_weight
        reasons.append(f"language match: {song['language']} (+{s.language_weight:.1f})")

    return score, reasons


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = "balanced",
    diversity: bool = False,
) -> List[Tuple[Dict, float, str]]:
    """Rank all songs by score and return the top k as (song, score, explanation)."""
    strategy = STRATEGIES[mode]
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, strategy)
        scored.append((song, score, reasons))

    if not diversity:
        scored.sort(key=lambda item: item[1], reverse=True)
        return [(song, score, "; ".join(reasons)) for song, score, reasons in scored[:k]]

    # Diversity: greedily pick the best remaining song, docking repeats by artist.
    picked: List[Tuple[Dict, float, str]] = []
    seen: Dict[str, int] = {}
    pool = list(scored)
    while pool and len(picked) < k:
        def adjusted(item):
            return item[1] - ARTIST_PENALTY * seen.get(item[0]["artist"], 0)
        best = max(pool, key=adjusted)
        pool.remove(best)
        song, score, reasons = best
        penalty = ARTIST_PENALTY * seen.get(song["artist"], 0)
        if penalty:
            reasons = reasons + [f"repeat-artist penalty (-{penalty:.2f})"]
        picked.append((song, score - penalty, "; ".join(reasons)))
        seen[song["artist"]] = seen.get(song["artist"], 0) + 1
    return picked
