from .tag_file_manager import TagFileManager


class Song:
    def __init__(self, song_id: str, name: str, playlist) -> None:
        self.id = song_id
        self.name = name
        self.playlist = playlist
        self._tags: set[str] = set()
        self._tag_file_manager = TagFileManager()

    @property
    def display_str(self) -> str:
        return f"{self.name.ljust(110)} │ {','.join(self._tags)}"
    
    def set_tags(self, tags: set[str]) -> None:
        self._tags = tags
        self._tag_file_manager.set_tags_for_song(
            tags=tags,
            playlist_id=self.playlist.id,
            song_id=self.id
        )

    def get_tags(self) -> set[str]:
        return self._tag_file_manager.get_tags_for_song(self.playlist.id, self.id)
