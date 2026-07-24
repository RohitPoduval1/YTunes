from frontend.now_playing import NowPlayingHeader
from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Label, ListItem, ListView, Static, Footer

from frontend.playlist_screen import PlaylistScreen
from frontend.popups import AddPlaylistURLPopup, ConfirmPopup
from frontend.base import VimListView


class LandingScreen(Screen):
    BINDINGS = [
        ("a", "add_playlist", "Add Playlist"),
        ("d", "delete_playlist", "Delete Playlist"),
    ]

    def compose(self) -> ComposeResult:
        yield NowPlayingHeader()
        ascii_art = """
\\ \\/ /_   _| | | | '_ \\ / _ \\/ __|
 \\  /  | | | |_| | | | |  __/\\__ \\
  \\/   |_|  \\__,_|_| |_|\\___||___/
        """
        with Vertical(id="landing-container"):
            yield Static(ascii_art, id="logo")
            # NO INPUT HERE
            yield VimListView(id="playlist-list")

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_playlists()
        self.query_one(VimListView).focus()

    def refresh_playlists(self) -> None:
        """Pulls playlists from the DB and repopulates the ListView."""
        list_view = self.query_one(ListView)
        list_view.clear()
        
        playlists = self.app.db.get_playlists()
        for playlist in playlists:
            item = ListItem(Label(playlist.name))
            item.playlist_data = playlist
            list_view.append(item)

    def action_add_playlist(self) -> None:
        """Fires when 'a' is pressed. Brings up the playlist URL popup."""
        self.app.push_screen(AddPlaylistURLPopup(), self._handle_new_url)

    def _handle_new_url(self, url: str) -> None:
        """Callback from AddPlaylistURLPopup when Enter is pressed."""
        if url:
            self.app.import_playlist(url)
            self.refresh_playlists()

    def action_delete_playlist(self) -> None:
        """Fires when 'd' is pressed. Prompts for confirmation before deleting."""
        list_view = self.query_one(ListView)
        
        if not list_view.highlighted_child:
            self.app.bell()
            return
            
        item = list_view.highlighted_child
        playlist = getattr(item, "playlist_data", None)
        
        if playlist:
            # Push confirmation modal and pass a callback lambda
            self.app.push_screen(
                ConfirmPopup(f"Delete playlist '{playlist.name}'? (y/n)"),
                lambda confirmed: self._handle_delete_confirmation(confirmed, playlist.id)
            )

    def _handle_delete_confirmation(self, confirmed: bool, playlist_id: str) -> None:
        if confirmed:
            self.app.db.delete_playlist(playlist_id)
            self.refresh_playlists()
            self.notify("Playlist deleted successfully", severity="information")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Navigate to the playlist details."""
        playlist = event.item.playlist_data
        self.app.push_screen(PlaylistScreen(playlist, self.app.db))
