import subprocess
import socket
import json
import os
import tempfile

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label, Footer, Input, Static, ContentSwitcher
from textual.binding import Binding
from textual.containers import Vertical
from textual.theme import Theme
from textual.reactive import reactive

from backend.playlist_file_manager import PlaylistFileManager
from backend.playlist import Playlist

from .playlist_screen import PlaylistScreen


youtube_theme = Theme(
    name="youtube",
    primary="#FF0000",
    accent="#FF0000",
)


class YTunes(App):
    CSS_PATH = "ytunes.tcss"

    BINDINGS = [
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("q", "quit", "Quit"),
        Binding("a", "add_playlist", "Add playlist", show=True),
        Binding("u", "update_playlist", "Update playlist", show=True),
        Binding("d", "delete_playlist", "Delete playlist", show=True),
        Binding("escape", "go_back", "Back/Cancel", show=True),
        Binding("space", "toggle_play", "Play/Pause", show=True),
        Binding("]", "skip_next", "Next", show=True),
        Binding("[", "skip_prev", "Prev", show=True),
    ]

    current_track = reactive("None")
    current_time = reactive(0.0)
    total_time = reactive(0.0)

    def __init__(self) -> None:
        super().__init__()
        self.playlist_file_manager = PlaylistFileManager()
        self.playlists = [Playlist(url) for url in self.playlist_file_manager.all_playlist_urls]
        
        self.player_process = None
        self.ipc_socket_path = os.path.join(tempfile.gettempdir(), "ytunes_mpv.sock")
        self.update_timer = None

    def compose(self) -> ComposeResult:
        url_input = Input(placeholder="Paste playlist URL and press Enter...", id="url_input")
        url_input.display = False
        yield url_input

        delete_playlist_input = Input(placeholder='"y" to confirm deletion', id="delete_playlist_input")
        delete_playlist_input.display = False
        yield delete_playlist_input

        yield Static("Now Playing: None", id="now_playing_header")

        with ContentSwitcher(initial="home_view", id="main_switcher"):
            with Vertical(id="home_view"):
                logo = r"""
__  _______                    
\ \/ /   _|   _ _ __   ___  ___ 
 \  /    | || | | | '_ \ / _ \/ __|
 / /     | || |_| | | | |  __/\__ \
/_/      |_| \__,_|_| |_|\___||___/
                """
                yield Static(logo, id="logo")
                playlist_items = [ListItem(Label(playlist.title)) for playlist in self.playlists]
                yield ListView(*playlist_items, id="main_playlist_list")
            
            with Vertical(id="details_view"):
                pass

        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(youtube_theme)
        self.theme = "youtube"
        self.query_one(ListView).focus()
        
        # Setup polling timer (paused until playback starts)
        self.update_timer = self.set_interval(1.0, self.poll_mpv, pause=True)

    def watch_current_time(self, time: float) -> None:
        self._update_now_playing_ui()

    def watch_current_track(self, track: str) -> None:
        self._update_now_playing_ui()

    def _update_now_playing_ui(self) -> None:
        try:
            header = self.query_one("#now_playing_header", Static)
            c_mins, c_secs = divmod(int(self.current_time), 60)
            t_mins, t_secs = divmod(int(self.total_time), 60)
            time_str = f"{c_mins:02d}:{c_secs:02d} / {t_mins:02d}:{t_secs:02d}"
            
            header.update(f"Now Playing: {self.current_track} | {time_str}")
        except Exception:
            pass

    # --- IPC Backend Integration ---

    def _send_ipc_command(self, command: list):
        """Sends a command to the mpv socket and returns the result."""
        if not os.path.exists(self.ipc_socket_path):
            return None
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.ipc_socket_path)
            message = json.dumps({"command": command}) + "\n"
            client.sendall(message.encode('utf-8'))
            
            response = client.recv(4096).decode('utf-8')
            client.close()
            
            if response:
                data = json.loads(response.split('\n')[0])
                return data.get("data")
        except Exception:
            pass
        return None

    def poll_mpv(self) -> None:
        """Called every second to fetch time, duration, and title from mpv."""
        if self.player_process is None or self.player_process.poll() is not None:
            self.update_timer.pause()
            return

        time_pos = self._send_ipc_command(["get_property", "time-pos"])
        duration = self._send_ipc_command(["get_property", "duration"])
        media_title = self._send_ipc_command(["get_property", "media-title"])

        if time_pos is not None:
            self.current_time = float(time_pos)
        if duration is not None:
            self.total_time = float(duration)
        if media_title is not None and media_title != self.current_track:
            self.current_track = media_title

    def play_urls(self, urls: list[str], title: str = "Loading...") -> None:
        if not urls:
            return
        self._stop_player()
        self.current_track = title

        # Clean up old socket if it exists
        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except OSError:
                pass

        # Native subprocess enables macOS media keys, IPC server enables polling
        command = [
            "mpv", 
            "--no-video", 
            f"--input-ipc-server={self.ipc_socket_path}"
        ] + urls

        self.player_process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Give mpv a moment to spin up the socket, then start polling
        self.set_timer(0.5, self.update_timer.resume)

    # --- Textual Media Controls (Fallback mapped to IPC) ---

    def action_toggle_play(self) -> None:
        self._send_ipc_command(["cycle", "pause"])

    def action_skip_next(self) -> None:
        self._send_ipc_command(["playlist-next"])

    def action_skip_prev(self) -> None:
        self._send_ipc_command(["playlist-prev"])

    # -----------------------------

    def action_quit(self) -> None:
        self._stop_player()
        self.exit()

    def _stop_player(self) -> None:
        self.current_track = "None"
        self.current_time = 0.0
        self.total_time = 0.0
        
        if self.update_timer:
            self.update_timer.pause()
            
        if self.player_process is not None:
            if self.player_process.poll() is None:
                self.player_process.terminate()
            self.player_process = None
            
        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except OSError:
                pass

    def action_move_down(self) -> None:
        self.query_one(ListView).action_cursor_down()

    def action_move_up(self) -> None:
        self.query_one(ListView).action_cursor_up()

    @on(ListView.Selected, "#main_playlist_list")
    async def open_playlist_details(self, event: ListView.Selected) -> None:
        list_view = event.list_view
        index = list_view.index
        if index is not None and 0 <= index < len(self.playlists):
            details_view = self.query_one("#details_view")
            
            await details_view.query("*").remove()
            
            playlist_widget = PlaylistScreen(self.playlists[index])
            await details_view.mount(playlist_widget)
            
            self.query_one("#main_switcher", ContentSwitcher).current = "details_view"

    def action_go_back(self) -> None:
        url_input = self.query_one("#url_input", Input)
        delete_playlist_input = self.query_one("#delete_playlist_input", Input)

        if url_input.display:
            url_input.display = False
            url_input.value = ""
            self.query_one(ListView).focus()
            return

        if delete_playlist_input.display:
            delete_playlist_input.display = False
            delete_playlist_input.value = ""
            self.query_one(ListView).focus()
            return
            
        switcher = self.query_one("#main_switcher", ContentSwitcher)
        if switcher.current == "details_view":
            switcher.current = "home_view"
            self.query_one("#main_playlist_list").focus()

    def action_update_playlist(self) -> None:
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
                playlist.delete_all_tags()
                self.playlists.pop(index)
                list_view.pop(index)

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
        if url in self.playlist_file_manager.all_playlist_urls:
            self.notify(f'Playlist "{playlist.title}" is already registered!')
        else:
            self.playlists.append(playlist)
            self.playlist_file_manager.add(playlist)
            self.query_one(ListView).append(ListItem(Label(playlist.title)))


if __name__ == "__main__":
    app = YTunes()
    app.run()
