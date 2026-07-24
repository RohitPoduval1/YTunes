from typing import List, Optional
import sqlite3

from backend.models import *


class DatabaseRepository:
    def __init__(self, db_path: str = "ytunes.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        # row_factory allows us to access columns by name (e.g., row['id'])
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        """Initializes the schema with junction tables and composite keys."""
        with self.conn:
            # SQLite disables foreign key constraints by default! We must turn them on.
            self.conn.execute("PRAGMA foreign_keys = ON;")
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS PLAYLIST (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS SONG (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS TAG (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS SONG_TAGS (
                    song_id TEXT,
                    tag_id INTEGER,
                    PRIMARY KEY (song_id, tag_id),
                    FOREIGN KEY (song_id) REFERENCES SONG(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES TAG(id) ON DELETE CASCADE
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS PLAYLIST_SONGS (
                    playlist_id TEXT,
                    song_id TEXT,
                    PRIMARY KEY (playlist_id, song_id),
                    FOREIGN KEY (playlist_id) REFERENCES PLAYLIST(id) ON DELETE CASCADE,
                    FOREIGN KEY (song_id) REFERENCES SONG(id) ON DELETE CASCADE
                )
            """)


    def save_playlist_data(self, playlist: Playlist, songs: List[Song]) -> None:
        """Saves a playlist and its songs, linking them in the junction table."""
        with self.conn:
            self.conn.execute(
                "INSERT OR IGNORE INTO PLAYLIST (id, name) VALUES (?, ?)", 
                (playlist.id, playlist.name)
            )
            
            for song in songs:
                self.conn.execute(
                    "INSERT OR IGNORE INTO SONG (id, name, url) VALUES (?, ?, ?)", 
                    (song.id, song.name, song.url)
                )
                self.conn.execute(
                    "INSERT OR IGNORE INTO PLAYLIST_SONGS (playlist_id, song_id) VALUES (?, ?)", 
                    (playlist.id, song.id)
                )

    def add_tag_to_song(self, song_id: str, tag_name: str) -> None:
        """Creates a tag if it doesn't exist, and links it to a song."""
        tag_name = tag_name.lower().strip()
        with self.conn:
            # 1. Insert tag if it doesn't exist
            self.conn.execute("INSERT OR IGNORE INTO TAG (name) VALUES (?)", (tag_name,))
            
            # 2. Get the tag ID
            cursor = self.conn.execute("SELECT id FROM TAG WHERE name = ?", (tag_name,))
            tag_id = cursor.fetchone()['id']
            
            # 3. Link song and tag
            self.conn.execute(
                "INSERT OR IGNORE INTO SONG_TAGS (song_id, tag_id) VALUES (?, ?)", 
                (song_id, tag_id)
            )


    def get_playlists(self) -> List[Playlist]:
        cursor = self.conn.execute("SELECT id, name FROM PLAYLIST")
        return [Playlist(id=row['id'], name=row['name']) for row in cursor.fetchall()]

    def get_songs_for_playlist(self, playlist_id: str, tag_filter: Optional[str] = None) -> List[Song]:
        """
        The heavy lifter. Grabs songs for a playlist, optionally filtering by a specific tag.
        Also hydrates the tags for each song.
        """
        # Base query joining playlist_songs to get the core song data
        query = """
            SELECT s.id, s.name, s.url 
            FROM SONG s
            JOIN PLAYLIST_SONGS ps ON s.id = ps.song_id
            WHERE ps.playlist_id = ?
        """
        params = [playlist_id]

        # If we are filtering, we add another JOIN to ensure the song has the specific tag
        if tag_filter:
            query += """
                AND s.id IN (
                    SELECT st.song_id 
                    FROM SONG_TAGS st 
                    JOIN TAG t ON st.tag_id = t.id 
                    WHERE t.name = ?
                )
            """
            params.append(tag_filter.lower().strip())

        cursor = self.conn.execute(query, params)
        songs = []
        
        for row in cursor.fetchall():
            song = Song(id=row['id'], name=row['name'], url=row['url'], tags=[])
            
            # Hydrate the tags for this specific song
            tag_cursor = self.conn.execute("""
                SELECT t.id, t.name 
                FROM TAG t
                JOIN SONG_TAGS st ON t.id = st.tag_id
                WHERE st.song_id = ?
            """, (song.id,))
            
            song.tags = [Tag(id=t['id'], name=t['name']) for t in tag_cursor.fetchall()]
            songs.append(song)
            
        return songs

    def clear_tags_for_song(self, song_id: str) -> None:
        """Removes all tags from a specific song by clearing the junction table."""
        with self.conn:
                self.conn.execute("DELETE FROM SONG_TAGS WHERE song_id = ?", (song_id,))

    def delete_playlist(self, playlist_id: str) -> None:
        """Deletes a playlist from the database."""
        with self.conn:
            self.conn.execute("DELETE FROM PLAYLIST WHERE id = ?", (playlist_id,))
