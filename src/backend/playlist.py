import re
from typing import Dict
import yt_dlp

from .song import Song
from .tag_file_manager import TagFileManager


class Playlist:
    def __init__(self, url) -> None:
        """Given the URL to a YouTube playlist, populate class attributes
        using metadata extracted with yt-dlp"""
        match = re.match(r"((?:https://)?.+/)(.+)", url)
        if not match:
            raise Exception("Regex failed")
        playlist_id = match.group(2)
        playlist_id = playlist_id.replace("\\", "")
        cleaned_playlist_url = match.group(1) + playlist_id
        self.url = cleaned_playlist_url
        self.id = playlist_id

        self.songs: Dict[str, Song] = {}
        ydl_opts = {
            "extract_flat": True,
            "quiet": True,
            "ignoreerrors": True,
            "no_warnings": True,
            "skip_download": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.url, download=False)

            self.title = info_dict.get("title", "")

            for entry in info_dict.get("entries", {}):
                title = entry.get("title", "")
                if not title or re.match(r"\[\w+ video\]", title):
                    continue
                else:
                    url = entry.get("url")
                    id = url.split("=")[1]
                    song = Song(song_id=id, name=title, playlist=self)
                    self.songs[id] = song

        self._tag_file_manager = TagFileManager()

    def update(self) -> int:
        new_playlist = Playlist(self.url)
        
        new_song_ids = set(new_playlist.songs.keys()) - set(self.songs.keys())
        
        for song_id in new_song_ids:
            self.songs[song_id] = new_playlist.songs[song_id]
            
        self.title = new_playlist.title
        
        return len(new_song_ids)

    def get_tags(self) -> set[str]:
        return self._tag_file_manager.get_tags_for_playlist(self.id)

    def delete_all_tags(self) -> None:
        self._tag_file_manager.delete_tags_for_playlist(self.id)

    def get_songs_for_tag(self, tag: str) -> list[str]:
        return self._tag_file_manager.get_songs_by_tag(self.id, tag)

    def delete_song(self, song_id) -> None:
        self._tag_file_manager.delete_song(
            song_id=song_id,
            playlist_id=self.id
        )
        del self.songs[song_id]
