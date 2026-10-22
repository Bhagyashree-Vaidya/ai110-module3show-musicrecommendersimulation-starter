from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# --- functional API tests ---
from src.recommender import load_songs, score_song, recommend_songs

PREFS = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}


def test_load_songs_converts_numbers():
    songs = load_songs("data/songs.csv")
    assert len(songs) >= 15
    assert isinstance(songs[0]["energy"], float)
    assert isinstance(songs[0]["id"], int)


def test_score_song_returns_score_and_reasons():
    song = load_songs("data/songs.csv")[0]
    score, reasons = score_song(PREFS, song)
    assert score > 0
    assert any("genre match" in r for r in reasons)


def test_energy_rewards_closeness_not_height():
    near = {"genre": "x", "mood": "x", "energy": 0.5, "acousticness": 0.5}
    far_high = {"genre": "x", "mood": "x", "energy": 0.95, "acousticness": 0.5}
    prefs = {"genre": "y", "mood": "y", "energy": 0.5}
    assert score_song(prefs, near)[0] > score_song(prefs, far_high)[0]


def test_recommend_songs_sorted_and_top_k():
    songs = load_songs("data/songs.csv")
    recs = recommend_songs(PREFS, songs, k=3)
    scores = [s for _, s, _ in recs]
    assert len(recs) == 3
    assert scores == sorted(scores, reverse=True)
    assert recs[0][0]["title"] == "Sunrise City"


def test_ranking_modes_change_results():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.3}
    genre_first = recommend_songs(prefs, songs, k=1, mode="genre_first")[0][0]["genre"]
    assert genre_first == "pop"


def test_diversity_penalizes_repeat_artist():
    songs = load_songs("data/songs.csv")
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True}
    plain = {s["title"]: sc for s, sc, _ in recommend_songs(prefs, songs, k=5)}
    diverse = {s["title"]: sc for s, sc, _ in recommend_songs(prefs, songs, k=5, diversity=True)}
    assert diverse["Focus Flow"] < plain["Focus Flow"]


# --- extra attribute tests ---
RETRO = {
    "genre": "synthwave", "mood": "moody", "energy": 0.6, "likes_acoustic": False,
    "decade": 1980, "tags": ["retro", "late-night", "dreamy"], "popularity": 50,
    "likes_instrumental": True, "language": "none",
}


def test_extra_attributes_load_with_right_types():
    song = load_songs("data/songs.csv")[0]
    assert isinstance(song["popularity"], int)
    assert isinstance(song["release_decade"], int)
    assert isinstance(song["mood_tags"], list) and song["mood_tags"]
    assert isinstance(song["instrumentalness"], float)
    assert isinstance(song["language"], str)


def test_extra_attributes_show_up_in_reasons():
    songs = {s["title"]: s for s in load_songs("data/songs.csv")}
    _, reasons = score_song(RETRO, songs["Night Drive Loop"])
    text = " ".join(reasons)
    for expected in ("1980s era", "mood tags", "popularity", "instrumental fit", "language match"):
        assert expected in text


def test_extra_attributes_change_the_ranking():
    songs = load_songs("data/songs.csv")
    plain = {k: v for k, v in RETRO.items() if k in ("genre", "mood", "energy", "likes_acoustic")}
    with_extras = recommend_songs(RETRO, songs, k=3)
    assert with_extras[0][0]["title"] == "Night Drive Loop"
    assert with_extras[2][0]["title"] != recommend_songs(plain, songs, k=3)[2][0]["title"]


def test_profiles_without_extras_ignore_them():
    songs = load_songs("data/songs.csv")
    _, reasons = score_song(PREFS, songs[0])
    assert not any("era" in r or "tags" in r or "language" in r for r in reasons)
