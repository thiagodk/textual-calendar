
from datetime import time

from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label

from .base import ExampleApp
from ..time import Time

class TimeApp(ExampleApp):
    """
    Example use of Time widget.
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Time(show_tz=True, id="time")
            yield Label(id="time-output")

    def on_mount(self) -> None:
        """
        Event handler called when app is mounted.
        """
        time_obj = self.query_one("#time", Time)
        time_value = time_obj.time_value
        assert time_value is not None
        self.query_one("#time-output", Label).update(self.print_time(time_value))

    @staticmethod
    def print_time(time_value: time) -> str:
        """
        Get a label content from a time object.
        """
        output = f"[b]Selected Time[/b]: {time_value.strftime('%H:%M:%S')}"
        if time_value.tzinfo is not None:
            output += f" {time_value.tzinfo}"
        return output

    @on(Time.Changed, "#time")
    def update_time_label(self, message: Time.Changed) -> None:
        """
        Update testing label when time value changes.
        """
        self.query_one("#time-output", Label).update(self.print_time(message.time_value))


if __name__ == "__main__":
    app = TimeApp()
    app.run()
