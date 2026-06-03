import subprocess

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label, Footer, Input, Static
from textual.binding import Binding
from textual.containers import Vertical
from textual.theme import Theme

from models import Playlist
from playlist_screen import PlaylistScreen
from playlist_store import load_playlist_urls, add_playlist_url, remove_playlist_url
from tag_store import delete_tags_for_playlist


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
        Binding("d", "delete_playlist", "Delete playlist", show=True),
        Binding("escape", "cancel_input", "Cancel", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        # Load playlists from file — this is the single source of truth
        urls = load_playlist_urls()
        self.playlists: list[Playlist] = [Playlist(url) for url in urls]
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

    def _stop_player(self) -> None:
        """Safely terminates the global background player."""
        if self.player_process is not None:
            if self.player_process.poll() is None:
                self.player_process.terminate()
            self.player_process = None

    def action_quit(self) -> None:
        self._stop_player()
        self.exit()

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

    def action_add_playlist(self) -> None:
        url_input = self.query_one("#url_input", Input)
        url_input.display = True
        url_input.focus()

    def action_delete_playlist(self) -> None:
        list_view = self.query_one(ListView)
        if list_view.index is not None:
            delete_playlist_input = self.query_one("#delete_playlist_input", Input)
            delete_playlist_input.display = True
            delete_playlist_input.focus()

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
                remove_playlist_url(playlist.url)

                # Remove from in-memory list and UI
                self.playlists.pop(index)
                list_view.pop(index)

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

        # Persist to file, then update in-memory list and UI
        add_playlist_url(playlist.url)
        self.playlists.append(playlist)
        self.query_one(ListView).append(ListItem(Label(playlist.title)))


if __name__ == "__main__":
    app = Home()
    app.run()
