import csv
import sys
from dataclasses import dataclass, field

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, SelectionList, Input
from textual.binding import Binding


@dataclass
class Song:
    id: str
    title: str
    tags: set = field(default_factory=set)

    @property
    def display_str(self) -> str:
        return f"{self.title.ljust(110)} │ {self.csv_formatted_tags}"


    @property
    def csv_formatted_tags(self) -> str:
        return ', '.join(sorted(self.tags))


class YTag(App):
    """A Textual app to tag songs in a playlist"""

    BINDINGS = [
        Binding("j", "move_down", "Down", show=False),
        Binding("k", "move_up", "Up", show=False),
        Binding("t", "tag_selected_songs", "Tag Selected"),
        Binding("escape", "cancel_action", "Cancel"),
        Binding("backspace", "clear_all_tags", "Clear All Tags"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, csv_path) -> None:
        super().__init__()
        self.csv_path = csv_path

        with open(self.csv_path, "r", encoding="UTF-8") as f:
            csv_reader = csv.reader(f)
            raw_playlist = [tuple(row) for row in csv_reader]
        
        self.playlist = {}
        for (title, id, tags_string) in raw_playlist:
            parsed_tags = [t.strip() for t in tags_string.split(",") if t.strip()]
            self.playlist[id] = Song(title=title, id=id, tags=set(parsed_tags))


    def compose(self) -> ComposeResult:
        yield Header()

        formatted_playlist = [
            # Textual needs tuples formatted as (Prompt, Value)
            (song.display_str, song.id)
            for song in self.playlist.values()
        ]
        yield SelectionList[str](*formatted_playlist)

        tag_input = Input(placeholder="Enter tags (comma separated)...")
        tag_input.styles.dock = "bottom"
        self._hide_input_widget(tag_input)
        yield tag_input

        yield Footer()


    def action_move_down(self) -> None:
        """Move the cursor one down"""
        self.query_one(SelectionList).action_cursor_down()

    def action_move_up(self) -> None:
        """Move the cursor one up"""
        self.query_one(SelectionList).action_cursor_up()

    
    def action_clear_all_tags(self) -> None:
        """Clear all the tags for the selected songs"""
        # The songs to clear the tags of
        selected_song_ids = self.query_one(SelectionList).selected

        # Clear in class attribute
        for song_id in selected_song_ids:
            self.playlist[song_id].tags = set()

        # Clear in CSV
        self._update_csv_for_playlist()

        # Refresh the SelectionList UI to show the new tags
        self._refresh_SelectionListUI()


    def action_tag_selected_songs(self) -> None:
        selected_song_ids = self.query_one(SelectionList).selected

        if not selected_song_ids:
            self.notify("Select at least one song with Spacebar or Enter first!", severity="warning")
            return

        # Shift focus to the Input field so user can enter tags
        tag_input = self.query_one(Input)
        tag_input.styles.display = "block"
        tag_input.focus()


    def action_cancel_action(self) -> None:
        """Triggered when the user presses Escape"""
        tag_input = self.query_one(Input)
        sel_list = self.query_one(SelectionList)
        
        self._hide_input_widget(tag_input)
        sel_list.focus()
        sel_list.deselect_all()


    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Triggered automatically when the user presses Enter in the Input widget."""
        new_tags: str = event.value
        parsed_new_tags = set([t.strip().lower() for t in new_tags.split(",")])
        
        tag_input_widget = self.query_one(Input)
        sel_list_widget = self.query_one(SelectionList)
        
        ### Apply Tags to DB ###
        selected_ids = sel_list_widget.selected
        # Update internal playlist structure
        for id in selected_ids:
            self.playlist[id].tags.update(parsed_new_tags)

        # Update CSV
        self._update_csv_for_playlist()
                
        # Refresh UI to show new tags
        self._refresh_SelectionListUI()
        
        # Cleanup
        self._hide_input_widget(tag_input_widget)
        sel_list_widget.deselect_all()
        sel_list_widget.focus()
        self.notify(f"Added tags: {new_tags}")


    def _update_csv_for_playlist(self) -> None:
        with open(self.csv_path, mode="w", newline="", encoding="UTF-8") as f:
            writer = csv.writer(f)
            for song in self.playlist.values():
                writer.writerow([song.title, song.id, song.csv_formatted_tags])

    def _refresh_SelectionListUI(self) -> None:
        sel_list_widget = self.query_one(SelectionList)
        sel_list_widget.clear_options()
        formatted_playlist = [
            (song.display_str, song.id)
            for song in self.playlist.values()
        ]
        sel_list_widget.add_options(formatted_playlist)


    def _hide_input_widget(self, input_widget: Input) -> None:
        input_widget.value = ""
        input_widget.styles.display = "none"


if __name__ == "__main__":
    app = YTag(sys.argv[1])
    app.run()
