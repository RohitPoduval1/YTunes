from typing import List
from frontend.now_playing import NowPlayingHeader
from frontend.popups import SearchInputPopup, TagInputPopup
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import DataTable, Label, Footer

from backend.models import Playlist, Song
from frontend.popups import *


class PlaylistScreen(Screen):
    """Matches 'Screenshot 2026-07-24 at 2.14.25 PM.jpg'"""

    BINDINGS = [
        ("escape", "app.pop_screen", "Go Back"),
        ("space", "toggle_select", "Select"),
        ("enter", "toggle_select", "Select"),
        ("p", "play_action", "Play"),
        ("t", "tag_action", "Tag"),
        ("d", "delete_tags", "Untag"),
        ("j", "move_down", "Down"),
        ("k", "move_up", "Up"),
        ("s", "search_action", "Search"),
    ]

    def __init__(self, playlist: Playlist, db, **kwargs):
        super().__init__(**kwargs)
        self.playlist = playlist
        self.db = db
        self.selected_songs: set[str] = set()
        self.current_songs: List[Song] = []

    def compose(self) -> ComposeResult:
        yield NowPlayingHeader()
        yield Label(f" {self.playlist.name} ", id="playlist-title")
        yield DataTable(id="songs-table")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_table()

    def refresh_table(self) -> None:
        """Pulls fresh data from DB and repopulates the table."""
        table = self.query_one(DataTable)
        table.clear(columns=True)
        
        table.cursor_type = "row"
        table.zebra_stripes = True
        
        # Adding explicit keys to columns so we can update them directly later
        table.add_column("Status", key="status")
        table.add_column("Song Title", key="title")
        table.add_column("Tags", key="tags")
        
        self.current_songs = self.db.get_songs_for_playlist(self.playlist.id)
        for song in self.current_songs:
            tag_string = ", ".join([tag.name for tag in song.tags])
            status = "[X]" if song.id in self.selected_songs else "   "
            table.add_row(status, song.name, tag_string, key=song.id)

    # --- Actions triggered by Hotkeys ---
    def action_move_down(self) -> None:
        """Fires when 'j' is pressed. Moves the table cursor down."""
        table = self.query_one(DataTable)
        row, col = table.cursor_coordinate
        
        # Ensure we don't try to move past the bottom of the table
        if row < len(table.rows) - 1:
            table.move_cursor(row=row + 1)

    def action_move_up(self) -> None:
        """Fires when 'k' is pressed. Moves the table cursor up."""
        table = self.query_one(DataTable)
        row, col = table.cursor_coordinate
        
        # Ensure we don't try to move past the top of the table
        if row > 0:
            table.move_cursor(row=row - 1)

    def action_toggle_select(self) -> None:
        """Fires when SPACE is pressed."""
        table = self.query_one(DataTable)
        try:
            # Safely get the row key for whatever row the cursor is currently on
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            song_id = row_key.value
            
            if song_id in self.selected_songs:
                self.selected_songs.remove(song_id)
                table.update_cell(row_key, "status", "   ")
            else:
                self.selected_songs.add(song_id)
                table.update_cell(row_key, "status", "[X]")
        except Exception:
            pass # Cursor might not be initialized yet

    def action_play_action(self) -> None:
        """Fires when P is pressed."""
        if self.selected_songs:
            # 1. Songs are selected. Play them.
            urls_to_play = [s.url for s in self.current_songs if s.id in self.selected_songs]
            self.app.play_urls(urls_to_play)
            
            # Clear selection after playing
            self.selected_songs.clear()
            self.refresh_table()
        else:
            # 2. No songs selected. Show Tag Menu.
            # Instantly gather all unique tags from the currently loaded songs
            all_tags = {tag.name for song in self.current_songs for tag in song.tags}
            
            if all_tags:
                self.app.push_screen(TagSelectPopup(all_tags), self._play_by_tag)
            else:
                self.app.bell() # No tags exist in this playlist yet!

    def _play_by_tag(self, tag_name: str) -> None:
        """Callback from the TagSelectPop."""
        if not tag_name:
            return
            
        urls_to_play = [
            song.url for song in self.current_songs 
            if any(t.name == tag_name for t in song.tags)
        ]
        if urls_to_play:
            self.app.play_urls(urls_to_play)

    def action_tag_action(self) -> None:
        """Fires when T is pressed."""
        if not self.selected_songs:
            self.app.bell()
            return
            
        self.app.push_screen(TagInputPopup(), self._apply_tag)

    def _apply_tag(self, tag_name: str) -> None:
        if not tag_name:
            return
            
        for song_id in self.selected_songs:
            self.db.add_tag_to_song(song_id, tag_name)
            
        self.selected_songs.clear()
        self.refresh_table()

    def action_delete_tags(self) -> None:
        """Clears tags for selected songs"""
        table = self.query_one(DataTable)
        
        # Determine which songs to target
        targets = set(self.selected_songs)
        
        # If no songs are explicitly selected with Space, fall back to the hovered row
        if not targets:
            try:
                row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
                targets.add(row_key.value)
            except Exception:
                pass
                
        if not targets:
            self.app.bell()
            return
            
        # 1. Clear them in the SQLite Database
        for song_id in targets:
            self.db.clear_tags_for_song(song_id)
            
        # 2. Reset selection and refresh UI to show tags are gone
        self.selected_songs.clear()
        self.refresh_table()

    def action_search_action(self) -> None:
        """Fires when 's' is pressed. Opens the search modal."""
        self.app.push_screen(SearchInputPopup(), self._apply_search)

    def _apply_search(self, search_term: str) -> None:
        """Callback from SearchInputPopup. Selects all matching songs."""
        if not search_term:
            return
            
        search_lower = search_term.lower()
        matched_any = False
        
        # Loop through all loaded songs and find partial matches
        for song in self.current_songs:
            if search_lower in song.name.lower():
                self.selected_songs.add(song.id)
                matched_any = True
                
        if matched_any:
            # Refresh the table so the newly selected items get their [X]
            self.refresh_table()
        else:
            # Play an alert sound if the search yielded zero results
            self.app.bell()
