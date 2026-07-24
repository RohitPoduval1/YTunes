from typing import List

from textual import work
from textual.app import App
from textual.reactive import reactive
from textual.widgets import Input

from frontend.now_playing import NowPlayingHeader
from frontend.landing_screen import LandingScreen
from backend.db_repo import DatabaseRepository
from backend.ytdlp_service import YtDlpService
from backend.mpv_service import MpvService


class YTunesApp(App):
    # Global Keybindings! These work on any screen.
    BINDINGS = [
        ("space", "toggle_play", "Play/Pause"),
        ("n", "skip_next", "Next Track"),
        ("p", "skip_prev", "Previous Track"),
        ("q", "quit_app", "Quit App"),
    ]

    CSS_PATH = "style.tcss"

    # Add the reactive property for time_info
    time_info = reactive("00:00 / 00:00")
    now_playing = reactive("None")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseRepository()
        self.yt = YtDlpService()
        self.player = MpvService()
        self.update_timer = None

    def on_mount(self) -> None:
        self.update_timer = self.set_interval(0.5, self.poll_player_state)
        self.push_screen(LandingScreen())

    def play_urls(self, urls: List[str]) -> None:
        """Called by the Playlist screen to initiate playback."""
        self.player.play_urls(urls)

    def poll_player_state(self) -> None:
        """Fired every 0.5 seconds to sync mpv state with Textual state."""
        new_title = self.player.get_current_title()
        new_time = self.player.get_time_info()
        
        # Update reactive properties (Textual handles the re-rendering automatically)
        if new_title != self.now_playing:
            self.now_playing = new_title
        if new_time != self.time_info:
            self.time_info = new_time

    def import_playlist(self, url: str) -> None:
        try:
            playlist, songs = self.yt.fetch_playlist_metadata(url)
            
            self.db.save_playlist_data(playlist, songs)
            
            if isinstance(self.screen, LandingScreen):
                self.screen.refresh_playlists()
                
            self.notify(f"Successfully imported: {playlist.name}", severity="information")
                
        except Exception as e:
            self.notify(f"Error: {str(e)[:40]}... Try another URL.", severity="error")
            self.bell()

    # --- Header Watchers ---
    def watch_now_playing(self, new_title: str) -> None:
        # Safely loops 0 times on startup, and 1 time once the UI is built
        for header in self.query(NowPlayingHeader):
            header.current_song = new_title

    def watch_time_info(self, new_time: str) -> None:
        for header in self.query(NowPlayingHeader):
            header.time_info = new_time

    # --- Actions (Triggered by Hotkeys) ---
    def action_toggle_play(self) -> None:
        self.player.toggle_play()

    def action_skip_next(self) -> None:
        self.player.skip_next()

    def action_skip_prev(self) -> None:
        self.player.skip_prev()

    def action_quit_app(self) -> None:
        self.exit()

    def on_unmount(self) -> None:
        """Crucial: Clean up the mpv process when exiting Textual."""
        self.player.quit()


if __name__ == "__main__":
    app = YTunesApp()
    app.run()
