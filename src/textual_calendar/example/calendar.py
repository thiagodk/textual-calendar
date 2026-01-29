
from datetime import date
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Label

from ..calendar import Calendar


class CalendarApp(App[None]):
    """
    Example of use of Calendar widget.
    """

    CSS = """
    Screen {
        align: center middle;
    }

    Vertical {
        width: auto;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Calendar(id="calendar")
            yield Label(self.print_date(), id="calendar-output")

    @staticmethod
    def print_date(date_value: Optional[date] = None) -> str:
        """
        Get a label content from a date object.
        """
        prefix = "[b]Selected Date[/b]:"
        if date_value is None:
            return prefix
        return f"{prefix} {date_value.strftime('%Y-%m-%d')}"

    @on(Calendar.Selected, "#calendar")
    def update_calendar_label(self, message: Calendar.Selected) -> None:
        """
        Update testing label when calendar selection changes.
        """
        self.query_one("#calendar-output", Label).update(self.print_date(message.date))


if __name__ == "__main__":
    app = CalendarApp()
    app.run()
