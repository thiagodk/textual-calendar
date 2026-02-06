
from textual.app import App


class ExampleApp(App[None]):
    """
    Base class for example apps.
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
