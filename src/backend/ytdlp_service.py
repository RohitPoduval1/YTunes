import yt_dlp
from typing import Tuple, List

from backend.models import Song, Playlist


class YtDlpService:
    """Scrapes YouTube metadata to populate the local database."""
    
    def fetch_playlist_metadata(self, playlist_url: str) -> Tuple[Playlist, List[Song]]:
        """
        Extracts playlist and song metadata without downloading media.
        Returns the Playlist and a list of Songs populated with their playback URLs.
        """
        ydl_opts = {
            'extract_flat': True, 
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            
            if 'entries' not in info:
                raise ValueError("The provided URL does not point to a valid playlist.")
            
            # Defensively fallback if YouTube doesn't provide a playlist ID or Title
            playlist = Playlist(
                id=info.get('id', 'unknown_id'), 
                name=info.get('title', 'Unknown Playlist')
            )
            songs = []
            
            for entry in info['entries']:
                if not entry:
                    continue
                
                song_id = entry.get('id')
                title = entry.get('title')
                
                # STRICT FILTERING: 
                # Skip if there's no ID, no title, or if YouTube flags it as deleted/private
                if not song_id or not title or title in ["[Deleted video]", "[Private video]"]:
                    continue
                
                # Extract URL or build fallback
                video_url = entry.get('url') or f"https://www.youtube.com/watch?v={song_id}"
                
                song = Song(
                    id=song_id, 
                    name=title, 
                    url=video_url,
                    tags=[]
                )
                songs.append(song)
                
            return playlist, songs

if __name__ == "__main__":
    yt_service = YtDlpService()
    playlist, songs = yt_service.fetch_playlist_metadata(
        playlist_url="https://youtube.com/playlist?list=PLZGDtj1K-VKZylDfZxxzSwQgCFewu7x8p&si=nVXSB_B8_iE-SUVh"
    )
    print(playlist.name)
    for song in songs:
        print(song.name)
