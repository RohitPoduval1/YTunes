from textual.widgets import Static
from textual.reactive import reactive


class NowPlayingHeader(Static):
    """A custom global header that updates reactively."""
    current_song = reactive("None")
    time_info = reactive("00:00 / 00:00")

    def on_mount(self) -> None:
        # Sync instantly upon creation
        self.update_state()
        # Create its own internal timer to pull updates from the App!
        self.set_interval(0.5, self.update_state)

    def update_state(self) -> None:
        """Pulls the latest state directly from the global app."""
        if self.current_song != self.app.now_playing:
            self.current_song = self.app.now_playing
        if self.time_info != self.app.time_info:
            self.time_info = self.app.time_info

    def render(self) -> str:
        return f" Now Playing: {self.current_song} | {self.time_info} "
