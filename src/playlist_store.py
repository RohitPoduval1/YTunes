import json
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent
DATA_DIR = SRC_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
PLAYLISTS_FILE = DATA_DIR / "playlists.json"

def load_playlist_urls() -> list[str]:
    """Return the saved list of playlist URLs. Empty list if file doesn't exist."""
    if not PLAYLISTS_FILE.exists():
        return []
    with open(PLAYLISTS_FILE, "r") as f:
        return json.load(f)


def save_playlist_urls(urls: list[str]) -> None:
    """Overwrite the playlist file with the given list of URLs."""
    with open(PLAYLISTS_FILE, "w") as f:
        json.dump(urls, f, indent=2)


def add_playlist_url(url: str) -> None:
    """Append a single URL to the persisted list."""
    urls = load_playlist_urls()
    if url not in urls:
        urls.append(url)
        save_playlist_urls(urls)


def remove_playlist_url(url: str) -> None:
    """Remove a single URL from the persisted list."""
    urls = load_playlist_urls()
    urls = [u for u in urls if u != url]
    save_playlist_urls(urls)
