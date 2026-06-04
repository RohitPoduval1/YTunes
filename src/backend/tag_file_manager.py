import json
from pathlib import Path


class TagFileManager:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        src_dir = Path(__file__).resolve().parent

        data_dir = src_dir.parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        self.file_path = data_dir / "tags.json"

    def _load_data(self) -> dict:
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="UTF-8") as f:
                json.dump({}, f, indent=2)

        with open(self.file_path, "r", encoding="UTF-8") as f:
            tag_data = json.load(f)

        return tag_data

    def _save_data(self, tag_data: dict) -> None:
        with open(self.file_path, "w", encoding="UTF-8") as f:
            json.dump(tag_data, f, indent=2)

    def set_tags_for_song(self, tags: set[str], playlist_id: str, song_id: str) -> None:
        tag_data = self._load_data()

        if playlist_id not in tag_data:
            tag_data[playlist_id] = {}

        tag_data[playlist_id][song_id] = sorted(tags)

        self._save_data(tag_data)

    def get_tags_for_playlist(self, playlist_id: str) -> set[str]:
        tag_data = self._load_data()
        playlist_data = tag_data.get(playlist_id, {})
        all_tags = set()
        for song_id in playlist_data:
            song_tags = set(playlist_data[song_id])
            all_tags = all_tags.union(song_tags)
        return all_tags

    def get_tags_for_song(self, playlist_id: str, song_id: str) -> set:
        tag_data = self._load_data()
        playlist = tag_data.get(playlist_id, {})
        return set(playlist.get(song_id, []))

    def delete_tags_for_playlist(self, playlist_id: str) -> None:
        tag_data = self._load_data()
        if playlist_id in tag_data:
            del tag_data[playlist_id]
        self._save_data(tag_data)

    def get_songs_by_tag(self, playlist_id: str, tag: str) -> list[str]:
        tag_data = self._load_data()
        playlist_data = tag_data.get(playlist_id, {})
        return [
            song_id
            for song_id, tags in playlist_data.items()
            if tag in tags
        ]
    
    def delete_song(self, playlist_id: str, song_id: str) -> None:
        tag_data = self._load_data()
        if playlist_id in tag_data and song_id in tag_data[playlist_id]:
            del tag_data[playlist_id][song_id]
            self._save_data(tag_data)
