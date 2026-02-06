
from textual.app import ComposeResult
from textual.containers import Vertical

from .base import ExampleApp
from ..time import Time

class TimeApp(ExampleApp):
    """
    Example use of Time widget.
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Time()


if __name__ == "__main__":
    app = TimeApp()
    app.run()
