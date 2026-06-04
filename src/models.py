from dataclasses import dataclass, field
import re
from typing import Dict

import yt_dlp


@dataclass
class Song:
    id: str
    title: str
    tags: [str] = field(default_factory=list)
    
    @property
    def display_str(self) -> str:
        return f"{self.title.ljust(110)} │ {','.join(self.tags)}"


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
                    song = Song(id=id, title=title)
                    self.songs[id] = song

    def update(self) -> int:
        new_playlist = Playlist(self.url)
        
        new_song_ids = set(new_playlist.songs.keys()) - set(self.songs.keys())
        
        for song_id in new_song_ids:
            self.songs[song_id] = new_playlist.songs[song_id]
            
        self.title = new_playlist.title
        
        return len(new_song_ids)
