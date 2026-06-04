import json
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
DATA_DIR = SRC_DIR.parent / "data"
TAGS_FILE = DATA_DIR / "tags.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_tags() -> dict:
    """Read all tags from the JSON file. Returns empty dict if file doesn't exist."""
    if not TAGS_FILE.exists():
        # TAGS_FILE.touch(exist_ok=True)
        return {}
    with open(TAGS_FILE, "r") as f:
        return json.load(f)


def save_tags(data: dict) -> None:
    """Write the entire tags dict to the JSON file."""
    with open(TAGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_tags_for_song(playlist_id: str, song_id: str) -> set:
    """Return the tag set for a specific song in a specific playlist."""
    data = load_tags()
    return set(data.get(playlist_id, {}).get(song_id, []))


def set_tags_for_song(playlist_id: str, song_id: str, tags: set) -> None:
    """Overwrite the tags for a specific song in a specific playlist."""
    data = load_tags()
    if playlist_id not in data:
        data[playlist_id] = {}
    data[playlist_id][song_id] = sorted(tags)  # sorted for stable file output
    save_tags(data)


def delete_tags_for_playlist(playlist_id: str) -> None:
    """Remove all tag data for an entire playlist."""
    data = load_tags()
    if playlist_id in data:
        del data[playlist_id]
        save_tags(data)

def delete_song(playlist_id: str, song_id: str) -> None:
    data = load_tags()
    if playlist_id in data and song_id in data[playlist_id]:
        del data[playlist_id][song_id]
        save_tags(data)
    

def get_songs_by_tag(playlist_id: str, tag: str) -> list[str]:
    """Return all song IDs in a playlist that have the given tag."""
    data = load_tags()
    playlist_data = data.get(playlist_id, {})
    return [
        song_id
        for song_id, tags in playlist_data.items()
        if tag.strip().lower() in [t.lower() for t in tags]
    ]
