import json
from pathlib import Path

from models import Playlist

class PlaylistFileManager:
    """
    A Singleton class to handle file management of metadata for all playlists
    stored in YTunes.
    """
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)

        return cls.instance


    def __init__(self) -> None:
        src_dir = Path(__file__).resolve().parent

        data_dir = src_dir.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        self.file_path = data_dir / "playlists.json"


    def _load_data(self) -> dict:
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="UTF-8") as f:
                json.dump({}, f, indent=2)

        with open(self.file_path, "r", encoding="UTF-8") as f:
            playlist_data = json.load(f)

        return playlist_data


    def _save_data(self, playlist_data: dict) -> None:
        with open(self.file_path, "w", encoding="UTF-8") as f:
            json.dump(playlist_data, f, indent=2)


    def add(self, playlist: Playlist) -> None:
        """Add a playlist to the JSON file"""
        playlist_data = self._load_data()

        playlist_data[playlist.id] = {
            "title": playlist.title,
            "url": playlist.url
        }

        self._save_data(playlist_data)


    def remove(self, playlist: Playlist) -> None:
        """Remove a playlist from the JSON file"""
        playlist_data = self._load_data()
        del playlist_data[playlist.id]
        self._save_data(playlist_data)


    @property
    def all_playlist_urls(self) -> list[str]:
        all_playlist_data = self._load_data()
        urls = []
        for playlist_data in all_playlist_data.values():
            urls.append(playlist_data["url"])

        return urls

