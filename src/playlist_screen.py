from textual.app import App, Screen, ComposeResult
from textual.widgets import Footer, Header, SelectionList, Input, ListView, ListItem, Label
from textual.binding import Binding

from models import Playlist
from tag_store import (
    get_tags_for_song,
    set_tags_for_song,
    get_songs_by_tag,
)


class PlaylistScreen(Screen):
    CSS_PATH = "playlist_screen.tcss"

    BINDINGS = [
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("escape", "cancel_action", "Cancel"),
        Binding("q", "quit", "Quit"),
        Binding("b", "go_back", "Back to Playlists"),

        Binding("backspace", "clear_all_tags", "Clear All Tags"),
        Binding("t", "tag_selected_songs", "Tag Selected"),

        Binding("p", "play_selected", "Play Selected"),
    ]

    def __init__(self, playlist: Playlist) -> None:
        super().__init__()
        self.playlist = playlist

    def compose(self) -> ComposeResult:
        yield Header()

        formatted_playlist = [
            (song.display_str, song.id)
            for song in self.playlist.songs.values()
        ]

        yield SelectionList[str](*formatted_playlist, id="playlist_detail_list")

        tag_input = Input(placeholder="Enter tags (comma separated)...")
        tag_input.styles.dock = "bottom"
        self._hide_input_widget(tag_input)
        yield tag_input

        # Tag picker overlay — hidden until p is pressed with nothing selected
        tag_list = ListView(id="tag_picker")
        tag_list.styles.display = "none"
        tag_list.styles.dock = "top"
        tag_list.styles.height = "auto"
        tag_list.styles.max_height = "50%"
        tag_list.styles.border = ("round", "yellow")
        yield tag_list

        yield Footer()

    def on_mount(self) -> None:
        # Load persisted tags into the in-memory playlist on screen open
        for song_id, song in self.playlist.songs.items():
            song.tags = get_tags_for_song(self.playlist.id, song_id)

        sel_list = self.query_one(SelectionList)
        sel_list.focus()
        sel_list.border_title = self.playlist.title
        self._refresh_SelectionListUI()

    def action_go_back(self) -> None:
        """Removes this screen and returns to the Home screen"""
        self.app.pop_screen()

    def action_quit(self) -> None:
        self.app.action_quit()

    def action_move_down(self) -> None:
        self.query_one(SelectionList).action_cursor_down()

    def action_move_up(self) -> None:
        self.query_one(SelectionList).action_cursor_up()

    def action_clear_all_tags(self) -> None:
        """Clear all tags for the selected songs (in memory + file)."""
        selected_song_ids = self.query_one(SelectionList).selected

        for song_id in selected_song_ids:
            self.playlist.songs[song_id].tags = set()
            set_tags_for_song(self.playlist.id, song_id, set())

        self._refresh_SelectionListUI()

    def action_tag_selected_songs(self) -> None:
        selected_song_ids = self.query_one(SelectionList).selected

        if not selected_song_ids:
            self.notify("Select at least one song with Spacebar or Enter first!", severity="warning")
            return

        tag_input = self.query_one(Input)
        tag_input.placeholder = "Enter tags (comma separated)..."
        tag_input.styles.display = "block"
        tag_input.focus()

    def action_play_selected(self) -> None:
        """Play selected songs, or show tag picker overlay if nothing is selected."""
        selected_song_ids = self.query_one(SelectionList).selected

        if selected_song_ids:
            self._play_song_ids(list(selected_song_ids))
        else:
            self._show_tag_picker()

    def _show_tag_picker(self) -> None:
        """Collect all tags across the playlist and show them in the overlay ListView."""
        all_tags = sorted({
            tag
            for song in self.playlist.songs.values()
            for tag in song.tags
        })

        if not all_tags:
            self.notify("No tags exist yet. Tag some songs with 't' first!", severity="warning")
            return

        tag_list = self.query_one("#tag_picker", ListView)
        tag_list.clear()
        for tag in all_tags:
            tag_list.append(ListItem(Label(tag), name=tag))

        tag_list.styles.display = "block"
        tag_list.border_title = "Pick a tag to play  [Esc to cancel]"
        tag_list.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Fires when the user clicks or presses Enter on a tag in the overlay."""
        tag = event.item.name
        tag_list = self.query_one("#tag_picker", ListView)
        tag_list.styles.display = "none"

        matching_ids = get_songs_by_tag(self.playlist.id, tag)
        if not matching_ids:
            self.notify(f'No songs tagged "{tag}".', severity="warning")
        else:
            self._play_song_ids(matching_ids)
            self.notify(f'Playing {len(matching_ids)} song(s) tagged "{tag}".')

        self.query_one(SelectionList).focus()

    def action_cancel_action(self) -> None:
        """Triggered when the user presses Escape"""
        tag_input = self.query_one(Input)
        sel_list = self.query_one(SelectionList)
        tag_list = self.query_one("#tag_picker", ListView)

        self._hide_input_widget(tag_input)
        tag_list.styles.display = "none"
        sel_list.focus()
        sel_list.deselect_all()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handles Enter in the Input widget for tagging."""
        value = event.value.strip()
        tag_input_widget = self.query_one(Input)
        sel_list_widget = self.query_one(SelectionList)

        parsed_new_tags = {t.strip().lower() for t in value.split(",") if t.strip()}
        selected_ids = sel_list_widget.selected

        for song_id in selected_ids:
            self.playlist.songs[song_id].tags.update(parsed_new_tags)
            set_tags_for_song(
                self.playlist.id,
                song_id,
                self.playlist.songs[song_id].tags,
            )

        self._refresh_SelectionListUI()
        self._hide_input_widget(tag_input_widget)
        sel_list_widget.deselect_all()
        sel_list_widget.focus()
        self.notify(f"Added tags: {value}")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _play_song_ids(self, song_ids: list[str]) -> None:
        urls = [f"https://youtu.be/{song_id}" for song_id in song_ids]
        self.app.play_urls(urls)
        self.notify(f"Queued {len(song_ids)} song(s) for playback.")
        self.query_one(SelectionList).deselect_all()

    def _refresh_SelectionListUI(self) -> None:
        sel_list_widget = self.query_one(SelectionList)
        sel_list_widget.clear_options()
        formatted_playlist = [
            (song.display_str, song.id)
            for song in self.playlist.songs.values()
        ]
        sel_list_widget.add_options(formatted_playlist)

    def _hide_input_widget(self, input_widget: Input) -> None:
        input_widget.value = ""
        input_widget.styles.display = "none"


if __name__ == "__main__":
    class TestApp(App):
        def on_mount(self) -> None:
            test_playlist = Playlist("https://youtube.com/playlist?list=PLZGDtj1K-VKZylDfZxxzSwQgCFewu7x8p")
            self.push_screen(PlaylistScreen(test_playlist))

        def play_urls(self, urls):
            self.notify(f"Simulating playing {len(urls)} urls!")

    app = TestApp()
    app.run()
