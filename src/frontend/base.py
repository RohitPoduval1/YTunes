from textual.widgets import ListView


class VimListView(ListView):
    """A reusable ListView subclass with built-in Vim-style j/k navigation."""
    
    BINDINGS = [
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
    ]

    def on_mount(self) -> None:
        """Automatically select the first item on load if items exist."""
        if len(self.children) > 0 and self.index is None:
            self.index = 0

    def action_cursor_down(self) -> None:
        """Move cursor down on 'j'."""
        if not self.children:
            return
        if self.index is None:
            self.index = 0
        else:
            self.index = min(self.index + 1, len(self.children) - 1)

    def action_cursor_up(self) -> None:
        """Move cursor up on 'k'."""
        if not self.children:
            return
        if self.index is None:
            self.index = 0
        else:
            self.index = max(self.index - 1, 0)
