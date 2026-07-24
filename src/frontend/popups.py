from textual.screen import ModalScreen
from textual.widgets import Input, ListView, ListItem, Label, Footer, Static
from textual.app import ComposeResult

from frontend.base import VimListView

class BaseInputPopup(ModalScreen[str]):
    DESCRIPTOR_TEXT = "Type here..."  # Default fallback

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        # Pulls the descriptor text dynamically from whatever class is calling it
        yield Input(placeholder=self.DESCRIPTOR_TEXT, classes="modal-input")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def action_cancel(self) -> None:
        self.dismiss("")


class SearchInputPopup(BaseInputPopup):
    """A popup to search for songs to select."""
    DESCRIPTOR_TEXT = "Search songs to select..."

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())


class TagInputPopup(BaseInputPopup):
    """A popup to enter a tag name for selected songs."""
    DESCRIPTOR_TEXT = "Enter tag name..."

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())


class AddPlaylistURLPopup(BaseInputPopup):
    """A popup to enter a YouTube playlist URL."""
    DESCRIPTOR_TEXT = "Paste YouTube Playlist URL here..."

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())


class ConfirmPopup(ModalScreen[bool]):
    """A popup to confirm a destructive action."""
    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
        ("escape", "cancel", "No"),
        ("q", "cancel", "No"),
    ]

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        yield Static(self.message, classes="confirm-label")
        yield Footer()

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class TagSelectPopup(ModalScreen[str]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
    ]
    
    def __init__(self, tags: set[str], **kwargs):
        super().__init__(**kwargs)
        self.tags = sorted(list(tags))

    def compose(self) -> ComposeResult:
        items = []
        for t in self.tags:
            item = ListItem(Label(t))
            item.tag_value = t 
            items.append(item)
            
        # Use VimListView here, passing the unpacked items
        yield VimListView(*items, id="tag-select-list")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.tag_value)

    def action_cancel(self) -> None:
        self.dismiss("")
