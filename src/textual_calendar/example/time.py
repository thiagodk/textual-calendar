
from textual.app import App, ComposeResult
from textual.containers import Vertical

from ..time import Time

class TimeApp(App[None]):
    """
    Example use of Time widget.
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        align: center middle;
    }

    Screen > Vertical {
        border: double blue;
        width: auto;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Time()


if __name__ == "__main__":
    app = TimeApp()
    app.run()
