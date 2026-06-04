import subprocess

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label, Footer, Input, Static
from textual.binding import Binding
from textual.containers import Vertical
from textual.theme import Theme

from models import Playlist
from playlist_screen import PlaylistScreen
from tag_store import delete_tags_for_playlist
from playlist_store import PlaylistFileManager


youtube_theme = Theme(
    name="youtube",
    primary="#FF0000",
    accent="#FF0000",
)


class Home(App):
    CSS_PATH = "home.tcss"

    BINDINGS = [
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("q", "quit", "Quit"),

        Binding("a", "add_playlist", "Add playlist", show=True),
    Binding("u", "update_playlist", "Update playlist", show=True),
        Binding("d", "delete_playlist", "Delete playlist", show=True),
        Binding("escape", "cancel_input", "Cancel", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.playlist_file_manager = PlaylistFileManager()
        self.playlists = [Playlist(url) for url in self.playlist_file_manager.all_playlist_urls]
        self.player_process = None

    def compose(self) -> ComposeResult:
        url_input = Input(placeholder="Paste playlist URL and press Enter...", id="url_input")
        url_input.display = False
        yield url_input

        delete_playlist_input = Input(placeholder='"y" to confirm deletion', id="delete_playlist_input")
        delete_playlist_input.display = False
        yield delete_playlist_input

        logo = r"""
__  _______                      
\ \/ /_   _|   _ _ __   ___  ___ 
 \  /  | || | | | '_ \ / _ \/ __|
 / /   | || |_| | | | |  __/\__ \
/_/    |_| \__,_|_| |_|\___||___/
        """

        playlist_items = [ListItem(Label(playlist.title)) for playlist in self.playlists]

        with Vertical(id="main_wrapper"):
            yield Static(logo, id="logo")
            yield ListView(*playlist_items, id="main_playlist_list")

        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(youtube_theme)
        self.theme = "youtube"
        self.query_one(ListView).focus()

    def play_urls(self, urls: list[str]) -> None:
        """A global method that any Screen can call to play music."""
        self._stop_player()
        command = ["mpv", "--no-video"] + urls
        self.player_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


    def action_quit(self) -> None:
        self._stop_player()
        self.exit()

    def _stop_player(self) -> None:
        """Safely terminates the global background player."""
        if self.player_process is not None:
            if self.player_process.poll() is None:
                self.player_process.terminate()
            self.player_process = None


    def action_move_down(self) -> None:
        self.query_one(ListView).action_cursor_down()

    def action_move_up(self) -> None:
        self.query_one(ListView).action_cursor_up()

    @on(ListView.Selected, "#main_playlist_list")
    def open_playlist_details(self, event: ListView.Selected) -> None:
        list_view = event.list_view
        index = list_view.index
        if index is not None and 0 <= index < len(self.playlists):
            self.push_screen(PlaylistScreen(self.playlists[index]))


    def action_cancel_input(self) -> None:
        url_input = self.query_one("#url_input", Input)
        delete_playlist_input = self.query_one("#delete_playlist_input", Input)

        if url_input.display:
            url_input.display = False
            url_input.value = ""

        if delete_playlist_input.display:
            delete_playlist_input.display = False
            delete_playlist_input.value = ""

        self.query_one(ListView).focus()


    def action_update_playlist(self) -> None:
        """Synchronously updates the currently selected playlist."""
        list_view = self.query_one(ListView)
        index = list_view.index
        
        if index is not None and 0 <= index < len(self.playlists):
            playlist = self.playlists[index]
            
            self.notify(f"Fetching updates for '{playlist.title}'...", title="Updating")
            
            try:
                new_count = playlist.update()
                
                if new_count > 0:
                    self.notify(f"Added {new_count} new song(s) to '{playlist.title}'!", title="Success")
                else:
                    self.notify(f"'{playlist.title}' is already up to date.", title="No New Songs")
                    
            except Exception as e:
                self.notify(f"Failed to update: {e}", title="Error", severity="error")


    ####################################
    # Deleting a Playlist
    ####################################
    def action_delete_playlist(self) -> None:
        list_view = self.query_one(ListView)
        if list_view.index is not None:
            delete_playlist_input = self.query_one("#delete_playlist_input", Input)
            delete_playlist_input.display = True
            delete_playlist_input.focus()

    @on(Input.Submitted, "#delete_playlist_input")
    def delete_playlist(self, event: Input.Submitted) -> None:
        confirmation: str = event.value
        delete_input = event.input
        list_view = self.query_one(ListView)

        delete_input.display = False
        delete_input.value = ""
        list_view.focus()

        if confirmation.strip().lower() == "y":
            index = list_view.index
            if index is not None and 0 <= index < len(self.playlists):
                playlist = self.playlists[index]

                # Wipe tags and remove from playlist file
                delete_tags_for_playlist(playlist.id)
                self.playlist_file_manager.remove(playlist)

                # Remove from in-memory list and UI
                self.playlists.pop(index)
                list_view.pop(index)


    ####################################
    # Adding a Playlist
    ####################################
    def action_add_playlist(self) -> None:
        url_input = self.query_one("#url_input", Input)
        url_input.display = True
        url_input.focus()

    @on(Input.Submitted, "#url_input")
    def handle_new_playlist(self, event: Input.Submitted) -> None:
        url = event.value.strip()
        url_input = event.input

        url_input.display = False
        url_input.value = ""
        self.query_one(ListView).focus()

        if not url:
            return

        playlist = Playlist(url)

        self.playlist_file_manager.add(playlist)
        self.playlists.append(playlist)
        self.query_one(ListView).append(ListItem(Label(playlist.title)))


if __name__ == "__main__":
    app = Home()
    app.run()
